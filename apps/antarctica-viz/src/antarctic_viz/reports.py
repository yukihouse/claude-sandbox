"""JMA monthly weather reports for Syowa Station: HTML parsing and text analysis.

The Japan Meteorological Agency publishes one page a month ("南極の気象") with a
prose summary (概況), a table of monthly statistics and, on the older pages, a
summary for each ten-day period (旬別の天候経過). This module turns those pages into
``MonthlyReport`` records and extracts what the prose says: blizzard counts, named
weather events, keyword hits and how the summary describes the month against normal.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from html.parser import HTMLParser

import pandas as pd

from antarctic_viz.parsers import ParseError

_MONTH_LINK = re.compile(r"ant(\d{4})(\d{2})\.html")
_SPACES = re.compile(r"[ \t\r\n　]+")


@dataclass(frozen=True)
class MonthlyReport:
    year: int
    month: int
    summary: tuple[str, ...]
    periods: tuple[tuple[str, str], ...] = ()
    stats: dict[str, str] = field(default_factory=dict)

    @property
    def date(self) -> pd.Timestamp:
        return pd.Timestamp(self.year, self.month, 1)

    @property
    def summary_text(self) -> str:
        return "".join(self.summary)

    @property
    def full_text(self) -> str:
        """Summary plus the ten-day period notes, for searching and event extraction."""
        return self.summary_text + "".join(text for _, text in self.periods)


def normalize(text: str) -> str:
    """NFKC (full-width digits/letters to ASCII) with runs of whitespace collapsed."""
    return _SPACES.sub(" ", unicodedata.normalize("NFKC", text)).strip()


def parse_index(html: str) -> list[tuple[int, int]]:
    """Year/month pairs linked from the list page, oldest first."""
    found = {(int(y), int(m)) for y, m in _MONTH_LINK.findall(html) if 1 <= int(m) <= 12}
    return sorted(found)


class _ReportParser(HTMLParser):
    """Collects text per ``<h2>`` section: paragraphs, ``<dt>/<dd>`` pairs and table cells."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.sections: list[dict] = []
        self._tag: str | None = None  # the text-collecting element we are inside
        self._skip = 0  # depth inside <p class="stx"> footnotes and <script>/<style>
        self._buffer: list[str] = []

    @property
    def _current(self) -> dict | None:
        return self.sections[-1] if self.sections else None

    def handle_starttag(self, tag, attrs):
        classes = (dict(attrs).get("class") or "").split()
        if tag in ("script", "style") or (tag == "p" and "stx" in classes):
            self._skip += 1
        elif tag == "h2":
            self._start(tag)
        elif tag == "br" and self._tag == "p":
            self._buffer.append("\n")
        elif tag in ("p", "dt", "dd", "th", "td") and self._current is not None:
            self._start(tag)

    def handle_endtag(self, tag):
        if tag in ("script", "style") or (tag == "p" and self._skip):
            self._skip = max(0, self._skip - 1)
        elif tag == self._tag:
            self._finish()

    def handle_data(self, data):
        if self._tag is not None and not self._skip:
            self._buffer.append(data)

    def _start(self, tag: str) -> None:
        if self._tag is not None:
            self._finish()
        self._tag = tag
        self._buffer = []

    def _finish(self) -> None:
        tag, raw = self._tag, "".join(self._buffer)
        self._tag, self._buffer = None, []
        if tag == "h2":
            self.sections.append({"title": normalize(raw).replace(" ", ""), "items": []})
        else:  # other tags are only collected once a section has started
            self.sections[-1]["items"].append((tag, raw))


def _lines(raw: str) -> list[str]:
    return [line for line in (normalize(part) for part in raw.split("\n")) if line]


def parse_report(html: str, year: int, month: int) -> MonthlyReport:
    """One monthly page. Raises ``ParseError`` when it has no 概況 section."""
    parser = _ReportParser()
    parser.feed(html)
    parser.close()
    summary: list[str] = []
    periods: list[tuple[str, str]] = []
    stats: dict[str, str] = {}
    found = False
    for section in parser.sections:
        title, items = section["title"], section["items"]
        if "概況" in title:
            found = True
            summary += [line for tag, raw in items if tag == "p" for line in _lines(raw)]
        elif "旬別" in title:
            label = ""
            for tag, raw in items:
                if tag == "dt":
                    label = normalize(raw).rstrip(":：")
                elif tag == "dd":
                    periods.append((label, "".join(_lines(raw))))
        elif "統計値" in title:
            cells = [normalize(raw) for tag, raw in items if tag in ("th", "td")]
            stats.update(zip(cells[0::2], cells[1::2], strict=False))
    if not found:
        raise ParseError(f"{year}年{month}月の月報: 概況が見つかりませんでした")
    return MonthlyReport(year, month, tuple(summary), tuple(periods), stats)


def headline(report: MonthlyReport, limit: int = 60) -> str:
    """The summary's first sentence, shortened to ``limit`` characters for tooltips."""
    first = sentences(report.summary_text)[0] if report.summary else ""
    return first if len(first) <= limit else first[: limit - 1] + "…"


def sentences(text: str) -> list[str]:
    """Split normalized text into sentences ending with 。 (a trailing fragment is kept)."""
    return [s for s in re.split(r"(?<=。)", normalize(text)) if s.strip()]


# --- Events (出来事) ------------------------------------------------------------

_NEGATED = re.compile(r"ブリザード(?:と|に)は?なら(?:な|ず)|ブリザードは(?:発生しなかった|0回)")
# Sentences about one ten-day period ("中旬は…計3回") give no total for the month.
_PARTIAL = re.compile(r"^(?:\d\))?(?:特に)?[上中下]旬|期間の|[上中下]旬(?:は|にも)")
_WHOLE_MONTH = re.compile(r"\d+月(?:の|は)ブリザード")
_BLIZZARD_COUNTS = (  # tried in this order within a sentence
    re.compile(r"(?:計|合計|合わせて)(\d+(?:\.\d+)?)回"),
    re.compile(r"(\d+(?:\.\d+)?)回の(?:[ABC]級)?ブリザード"),
    re.compile(r"ブリザード[^。]*?(\d+(?:\.\d+)?)回"),
)
EVENTS: dict[str, re.Pattern[str]] = {
    "ブリザード": re.compile(r"ブリザード"),
    "ふぶき": re.compile(r"ふぶき"),
    "カタバ風": re.compile(r"カタバ風"),
    "低気圧の接近": re.compile(r"低気圧[^。]*?(?:接近|通過)"),
    "高気圧・尾根": re.compile(r"高気圧|気圧の尾根"),
    "暖気の流入": re.compile(r"暖気|暖かい空気|暖かく湿った空気"),
    "寒気・放射冷却": re.compile(r"寒気|放射冷却"),
    "記録・順位": re.compile(r"\d+位|\d+番目|極値|過去最"),
}


def mentions(sentence: str, event: str) -> bool:
    """Whether ``sentence`` reports ``event``; "ブリザードとはならなかった" does not count."""
    if not EVENTS[event].search(sentence):
        return False
    return event != "ブリザード" or not _NEGATED.search(sentence)


def blizzard_count(text: str) -> float | None:
    """Number of blizzards in the month when the text states it, else ``None``.

    The first sentence giving a count for the whole month wins. Reports sometimes count
    a blizzard spanning two months as 0.5, hence a float.
    """
    for sentence in sentences(text):
        if "ブリザード" not in sentence:
            continue
        if _PARTIAL.search(sentence) and not _WHOLE_MONTH.search(sentence):
            continue
        if "発生しなかった" in sentence:
            return 0.0
        for pattern in _BLIZZARD_COUNTS:
            match = pattern.search(sentence)
            if match:
                return float(match.group(1))
    return None


def event_table(reports: list[MonthlyReport]) -> pd.DataFrame:
    """One row per month: ``date, year, month, blizzard_count`` and a bool per event."""
    rows = []
    for report in reports:
        text = sentences(report.full_text)
        row = {
            "date": report.date,
            "year": report.year,
            "month": report.month,
            "blizzard_count": blizzard_count(report.full_text),
        }
        row.update({event: any(mentions(s, event) for s in text) for event in EVENTS})
        rows.append(row)
    columns = ["date", "year", "month", "blizzard_count", *EVENTS]
    return pd.DataFrame(rows, columns=columns).astype({"blizzard_count": float})


def yearly_event_months(events: pd.DataFrame) -> pd.DataFrame:
    """Long table ``year, event, value``: months per year whose report mentions the event."""
    counts = events.groupby("year")[list(EVENTS)].sum().reset_index()
    long = counts.melt(id_vars="year", var_name="event", value_name="value")
    return long.astype({"value": int})


# --- Keyword search -------------------------------------------------------------


def search(reports: list[MonthlyReport], query: str) -> pd.DataFrame:
    """Sentences containing any of the space-separated keywords in ``query``."""
    keywords = [k for k in normalize(query).split(" ") if k]
    rows = [
        {"date": report.date, "year": report.year, "month": report.month, "sentence": sentence}
        for report in reports
        for sentence in sentences(report.full_text)
        if keywords and any(k in sentence for k in keywords)
    ]
    return pd.DataFrame(rows, columns=["date", "year", "month", "sentence"])


# --- How the summary describes the month against normal -------------------------

LEVELS = (-2, -1, 0, 1, 2)
_RANK = re.compile(
    r"(高い|低い|多い|少ない|強い|弱い|大きい|小さい)(?:方|ほう)から[^、。]*?(?:(\d+)位|極値)"
)
_RANK_NOUN = re.compile(r"(\d+)位(?:タイ)?の(高さ|低さ|多さ|少なさ|強さ|弱さ|大きさ|小ささ)")
_RECORD = re.compile(r"(?:過去最|最も)(大|高|多|強|小|低|少|弱)")
_STRONG = re.compile(r"かなり|大きく(?:上|下)回|非常に|著しく")
# Rank 6 or better is roughly the outer 10% of Syowa's record since 1957.
_TOP_RANK = 6
_UP_WORDS = "高大多強"


@dataclass(frozen=True)
class Element:
    """A monthly quantity the summaries compare with normal."""

    label: str
    unit: str
    subject: re.Pattern[str]  # how the text names the monthly mean
    up: re.Pattern[str]
    down: re.Pattern[str]
    stat: str  # its row in the statistics table
    reader: str  # its READER element, for the normal-period distribution
    words: tuple[str, str]  # names for below / above normal

    def level_label(self, level: int) -> str:
        if level == 0:
            return "平年並"
        word = self.words[level > 0]
        return f"かなり{word}" if abs(level) == 2 else word


ELEMENTS: dict[str, Element] = {
    "temperature": Element(
        "気温",
        "°C",
        re.compile(r"月平均気温"),
        re.compile(r"高|上回"),
        re.compile(r"低|下回"),
        "平均気温",
        "temperature",
        ("低い", "高い"),
    ),
    "wind_speed": Element(
        "風速",
        "m/s",
        re.compile(r"月平均風速"),
        re.compile(r"強|大き|高|上回"),
        re.compile(r"弱|小さ|低|下回"),
        "平均風速",
        "wind_speed",
        ("弱い", "強い"),
    ),
    "pressure": Element(
        "気圧",
        "hPa",
        re.compile(r"月平均(?:海面)?気圧"),
        re.compile(r"高|上回"),
        re.compile(r"低|下回"),
        "平均気圧(海面)",
        "pressure",
        ("低い", "高い"),
    ),
}
_ANY_SUBJECT = re.compile("|".join(e.subject.pattern for e in ELEMENTS.values()))


def _chunk_level(chunk: str, element: Element) -> int | None:
    if "平年並" in chunk:
        return 0
    rank = _RANK.search(chunk)
    if rank:
        sign = 1 if rank.group(1)[0] in _UP_WORDS else -1
        return sign * (2 if int(rank.group(2) or 1) <= _TOP_RANK else 1)
    rank = _RANK_NOUN.search(chunk)
    if rank:
        sign = 1 if rank.group(2)[0] in _UP_WORDS else -1
        return sign * (2 if int(rank.group(1)) <= _TOP_RANK else 1)
    record = _RECORD.search(chunk)
    if record:
        return 2 if record.group(1) in _UP_WORDS else -2
    strength = 2 if _STRONG.search(chunk) else 1
    if element.down.search(chunk):
        return -strength
    if element.up.search(chunk):
        return strength
    return None


def text_level(text: str, element: Element) -> tuple[int, str] | None:
    """How the text describes the monthly mean: (-2..2, sentence), or ``None``.

    The words after the first mention of the monthly mean ("月平均気温は平年よりかなり
    高く…") decide: 平年並 → 0, かなり/大きく → ±2, and a rank such as "低い方から4位"
    → ±2 down to 6th place, ±1 below that.
    """
    for sentence in sentences(text):
        for match in element.subject.finditer(sentence):
            rest = sentence[match.end() :]
            following = _ANY_SUBJECT.search(rest)
            if following:
                rest = rest[: following.start()]
            for chunk in rest.split("、"):
                level = _chunk_level(chunk, element)
                if level is not None:
                    return level, sentence
    return None


def stat_value(report: MonthlyReport, element: Element) -> float | None:
    """The month's value from the statistics table, e.g. ``-2.8℃`` → -2.8."""
    raw = normalize(report.stats.get(element.stat, ""))
    match = re.match(r"-?\d+(?:\.\d+)?", raw)
    return float(match.group()) if match else None


def jma_normal_period(year: int, month: int) -> tuple[int, int]:
    """The 30-year normal JMA compared against when writing that month's report.

    JMA switched normals in May 2011 (to 1981–2010) and May 2021 (to 1991–2020).
    """
    if (year, month) < (2011, 5):
        return (1971, 2000)
    if (year, month) < (2021, 5):
        return (1981, 2010)
    return (1991, 2020)


def normal_values(series: pd.DataFrame, year: int, month: int) -> pd.Series:
    """Values of ``series`` for the same calendar month within that report's normal period."""
    start, end = jma_normal_period(year, month)
    dates = series["date"]
    mask = (dates.dt.month == month) & (dates.dt.year >= start) & (dates.dt.year <= end)
    return series.loc[mask, "value"].dropna()


def classify(value: float, normals: pd.Series) -> int | None:
    """JMA-style class of ``value`` within the normal-period values of the same month.

    Thirds of the distribution are 低い / 平年並 / 高い, and the outer 10% on each
    side are かなり低い / かなり高い. ``None`` when fewer than 10 years are available.
    """
    clean = normals.dropna()
    if len(clean) < 10:
        return None
    q10, q33, q67, q90 = clean.quantile([0.1, 1 / 3, 2 / 3, 0.9])
    if value < q10:
        return -2
    if value < q33:
        return -1
    if value <= q67:
        return 0
    if value <= q90:
        return 1
    return 2


def expression_table(
    reports: list[MonthlyReport], monthly: dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """Compare what each summary says with where the month's value falls among normals.

    ``monthly`` maps an ``ELEMENTS`` key to its monthly ``date``/``value`` series at
    Syowa (READER), from which the normal period of each report is taken.
    """
    rows = []
    for report in reports:
        start, end = jma_normal_period(report.year, report.month)
        for key, series in monthly.items():
            element = ELEMENTS[key]
            described = text_level(report.full_text, element)
            value = stat_value(report, element)
            if described is None or value is None:
                continue
            same_month = normal_values(series, report.year, report.month)
            computed = classify(value, same_month)
            if computed is None:
                continue
            level, sentence = described
            rows.append(
                {
                    "date": report.date,
                    "element": element.label,
                    "text_level": level,
                    "text_label": element.level_label(level),
                    "value": value,
                    "normal": float(same_month.mean()),
                    "anomaly": value - float(same_month.mean()),
                    "computed_level": computed,
                    "computed_label": element.level_label(computed),
                    "normal_period": f"{start}–{end}",
                    "sentence": sentence,
                }
            )
    columns = [
        "date",
        "element",
        "text_level",
        "text_label",
        "value",
        "normal",
        "anomaly",
        "computed_level",
        "computed_label",
        "normal_period",
        "sentence",
    ]
    out = pd.DataFrame(rows, columns=columns)
    out["direction_match"] = (
        out["text_level"].apply(_sign) == out["computed_level"].apply(_sign)
    ).astype(bool)
    out["exact_match"] = (out["text_level"] == out["computed_level"]).astype(bool)
    return out


def _sign(level: int) -> int:
    return (level > 0) - (level < 0)

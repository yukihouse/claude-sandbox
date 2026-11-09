"""Parsers turning the raw text files of each data source into tidy DataFrames.

Every parser returns a DataFrame with a ``date`` (Timestamp) column and a float
``value`` column, sorted by date, so the analysis and chart code can treat all
sources the same way. Ice-core records reach 800,000 years back, beyond what a
Timestamp can hold, so their parsers use an ``age_bp`` column (years before 1950)
instead of ``date``. The ozone-hole files carry more than one quantity per row, so
their parsers add columns next to (or instead of) ``value``.
"""

from __future__ import annotations

import csv
import io
import re
from datetime import date

import pandas as pd

MISSING_THRESHOLD = -999.0
KNOT_IN_MS = 0.514444
_NUMBER = re.compile(r"^-?\d+(?:\.\d+)?")
_YEAR = re.compile(r"^\d{4}$")


class ParseError(ValueError):
    """Raised when a file contains no recognisable data rows."""


def _frame(rows: list[tuple[date, float]], source: str) -> pd.DataFrame:
    if not rows:
        raise ParseError(f"{source}: データ行が見つかりませんでした")
    df = pd.DataFrame(rows, columns=["date", "value"])
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = df["value"].astype(float)
    return df.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)


def _age_frame(rows: list[tuple[float, float]], source: str) -> pd.DataFrame:
    if not rows:
        raise ParseError(f"{source}: データ行が見つかりませんでした")
    df = pd.DataFrame(rows, columns=["age_bp", "value"]).astype(float)
    return df.sort_values("age_bp").drop_duplicates("age_bp", keep="last").reset_index(drop=True)


def parse_sea_ice_daily(text: str) -> pd.DataFrame:
    """NSIDC Sea Ice Index daily extent CSV (``Year, Month, Day, Extent, ...``).

    The two header lines and any malformed rows are skipped.
    """
    rows = []
    for line in text.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:
            continue
        try:
            day = date(int(parts[0]), int(parts[1]), int(parts[2]))
            extent = float(parts[3])
        except ValueError:
            continue
        if extent <= MISSING_THRESHOLD:
            continue
        rows.append((day, extent))
    return _frame(rows, "sea ice extent")


def parse_gml_monthly(text: str) -> pd.DataFrame:
    """NOAA GML in-situ monthly text file.

    Column names come from a ``# data_fields:`` comment or from the first
    non-comment line containing ``year`` and ``value``. Missing values
    (``-999.99``) and rows whose QC flag doesn't start with ``.`` are dropped.
    """
    header: list[str] | None = None
    rows = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# data_fields:"):
            header = stripped.split(":", 1)[1].split()
            continue
        if not stripped or stripped.startswith("#"):
            continue
        tokens = stripped.split()
        if header is None or tokens == header:
            if "year" in tokens and "value" in tokens:
                header = tokens
            continue
        record = dict(zip(header, tokens, strict=False))
        try:
            month_start = date(int(record["year"]), int(record["month"]), 1)
            value = float(record["value"])
        except (KeyError, ValueError):
            continue
        if value <= MISSING_THRESHOLD or not record.get("qcflag", ".").startswith("."):
            continue
        rows.append((month_start, value))
    return _frame(rows, "NOAA GML")


def parse_reader_monthly(text: str) -> pd.DataFrame:
    """SCAR READER monthly table: ``Year Jan Feb ... Dec`` rows.

    Missing months are written as ``-`` and incomplete means may carry a
    trailing marker such as ``*``; the numeric prefix is used when present.
    """
    rows = []
    for line in text.splitlines():
        tokens = line.split()
        if len(tokens) < 2 or not _YEAR.match(tokens[0]):
            continue
        year = int(tokens[0])
        for month, token in enumerate(tokens[1:13], start=1):
            match = _NUMBER.match(token)
            if match:
                rows.append((date(year, month, 1), float(match.group())))
    return _frame(rows, "READER")


def parse_reader_wind(text: str) -> pd.DataFrame:
    """READER wind-speed table, converted from knots to m/s."""
    df = parse_reader_monthly(text)
    df["value"] = df["value"] * KNOT_IN_MS
    return df


def parse_ozone_annual(text: str) -> pd.DataFrame:
    """NASA Ozone Watch annual table: ``Year  O3 hole area (mil km2)  Minimum ozone (DU)``.

    Returns ``date`` (1 July of each year), ``area`` and ``min_ozone``; missing
    values become NaN.
    """
    rows = []
    for line in text.splitlines():
        tokens = line.split()
        if len(tokens) < 3 or not _YEAR.match(tokens[0]):
            continue
        try:
            area, low = (float(t) for t in tokens[1:3])
        except ValueError:
            continue
        rows.append((date(int(tokens[0]), 7, 1), area, low))
    if not rows:
        raise ParseError("ozone hole annual: データ行が見つかりませんでした")
    df = pd.DataFrame(rows, columns=["date", "area", "min_ozone"])
    df["date"] = pd.to_datetime(df["date"])
    for column in ("area", "min_ozone"):
        df[column] = df[column].mask(df[column] <= MISSING_THRESHOLD)
    return df.sort_values("date").reset_index(drop=True)


OZONE_DAILY_COLUMNS = ["value", "minimum", "p10", "p30", "mean", "p70", "p90", "maximum"]


def parse_ozone_daily(text: str) -> pd.DataFrame:
    """NASA Ozone Watch daily area file: ``Date Data Minimum 10% 30% Mean 70% 90% Maximum``.

    Every day of the year is kept so the climatology columns span the whole year;
    days not yet observed (``-9999``) have a NaN ``value``.
    """
    rows = []
    for line in text.splitlines():
        tokens = line.split()
        if len(tokens) < 9:
            continue
        try:
            day = date.fromisoformat(tokens[0])
            numbers = [float(t) for t in tokens[1:9]]
        except ValueError:
            continue
        rows.append((day, *numbers))
    if not rows:
        raise ParseError("ozone hole daily: データ行が見つかりませんでした")
    df = pd.DataFrame(rows, columns=["date", *OZONE_DAILY_COLUMNS])
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = df["value"].mask(df["value"] <= MISSING_THRESHOLD)
    return df.sort_values("date").reset_index(drop=True)


def parse_ice_core_co2(text: str) -> pd.DataFrame:
    """NOAA NCEI Antarctic composite CO2 (``age_gas_calBP  co2_ppm  co2_1s_ppm``).

    ``#`` comment lines and the column header are skipped.
    """
    rows = []
    for line in text.splitlines():
        if line.lstrip("\ufeff").startswith("#"):
            continue
        tokens = line.split()
        if len(tokens) < 2:
            continue
        try:
            rows.append((float(tokens[0]), float(tokens[1])))
        except ValueError:
            continue
    return _age_frame(rows, "ice core CO2")


def parse_edc_temperature(text: str) -> pd.DataFrame:
    """EPICA Dome C table: ``Bag  ztop  Age  Deuterium  Temperature``.

    Rows missing the deuterium value still end with the temperature, while rows
    with only three columns carry no temperature and are skipped.
    """
    rows = []
    for line in text.splitlines():
        tokens = line.split()
        if len(tokens) < 4 or not tokens[0].isdigit():
            continue
        try:
            rows.append((float(tokens[2]), float(tokens[-1])))
        except ValueError:
            continue
    return _age_frame(rows, "EPICA Dome C")


JMA_DOWNLOAD_MARKER = "ダウンロードした時刻"
# Sub-header labels of the JMA columns that qualify a value rather than hold one.
JMA_FLAG_LABELS = frozenset({"品質情報", "均質番号", "現象なし情報"})


def decode_upload(data: bytes) -> str:
    """UTF-8 (with or without BOM) first, then Shift_JIS (CP932) as JMA writes it."""
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    try:
        return data.decode("cp932")
    except UnicodeDecodeError as exc:
        raise ParseError(
            "文字コードを判別できませんでした (UTF-8 または Shift_JIS のみ対応)"
        ) from exc


def _looks_like_date(cell: str) -> bool:
    return bool(re.match(r"^\d{4}[-/]\d{1,2}", cell.strip()))


def _read_jma(text: str) -> pd.DataFrame:
    """JMA download CSV: a timestamp line, then several header rows, then data.

    The header rows are station, element and a sub-header naming the quality /
    homogeneity columns; those flag columns are dropped and the rest are named
    after their element (prefixed with the station when there are several).
    """
    rows = list(csv.reader(io.StringIO(text)))[1:]
    rows = [row for row in rows if any(cell.strip() for cell in row)]
    start = next((i for i, row in enumerate(rows) if row and _looks_like_date(row[0])), None)
    if start is None or start == 0:
        raise ParseError("気象庁形式のCSVからデータ行が見つかりませんでした")
    header, body = rows[:start], rows[start:]
    width = max(len(row) for row in rows)
    columns = [[row[j].strip() if j < len(row) else "" for row in header] for j in range(width)]
    stations = {col[0] for col in columns[1:] if len(header) >= 3 and col[0]}
    keep, names = [0], [columns[0][-2] or columns[0][-1] or "年月日"]
    for j, col in enumerate(columns[1:], start=1):
        if JMA_FLAG_LABELS & set(col):
            continue
        labels = [cell for cell in col if cell]
        if len(stations) <= 1 and len(labels) > 1:
            labels = labels[1:]
        name = " ".join(labels) or f"列{j}"
        while name in names:
            name += "'"
        keep.append(j)
        names.append(name)
    data = [[row[j] if j < len(row) else "" for j in keep] for row in body]
    return pd.DataFrame(data, columns=names)


def _strip_pangaea_header(text: str) -> str:
    """PANGAEA text export: drop the ``/* DATA DESCRIPTION ... */`` block."""
    end = text.find("\n*/")
    if end < 0:
        raise ParseError("PANGAEA形式の説明ブロック (/* ... */) の終わりが見つかりませんでした")
    return text[end + len("\n*/") :].lstrip("\r\n")


def read_upload(data: bytes) -> pd.DataFrame:
    """Read an uploaded table, recognising JMA and PANGAEA downloads.

    Anything else is read as delimited text with the delimiter sniffed and ``#``
    comment lines skipped.
    """
    text = decode_upload(data)
    if text.lstrip().startswith(JMA_DOWNLOAD_MARKER):
        return _read_jma(text)
    if text.lstrip().startswith("/*"):
        text = _strip_pangaea_header(text)
        sep = "\t"
    else:
        sep = None
    try:
        return pd.read_csv(io.StringIO(text), sep=sep, engine="python", comment="#")
    except (ValueError, csv.Error) as exc:  # ParserError/EmptyDataError are ValueErrors
        raise ParseError(str(exc)) from exc


_UNIT_SUFFIX = re.compile(r"[(\[（［]([^()\[\]（）［］]+)[)\]）］]\s*$")


def unit_from_label(label: str) -> str:
    """Unit written at the end of a column name, e.g. ``平均気温(℃)`` or ``t [°C]``."""
    match = _UNIT_SUFFIX.search(label)
    return match.group(1).strip() if match else ""


def parse_user_table(df: pd.DataFrame, date_col: str, value_col: str) -> pd.DataFrame:
    """Normalise an uploaded table to the ``date``/``value`` shape."""
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(df[date_col], errors="coerce"),
            "value": pd.to_numeric(df[value_col], errors="coerce"),
        }
    ).dropna()
    if out.empty:
        raise ParseError(f"'{date_col}' / '{value_col}' から有効な行を読み取れませんでした")
    out = out.groupby("date", as_index=False)["value"].mean()
    return out.reset_index(drop=True)

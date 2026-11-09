"""Streamlit web UI for exploring public Antarctic observation data.

Run with ``uv run antarctic-viz`` (or ``uv run streamlit run src/antarctic_viz/app.py``).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from antarctic_viz import analysis, charts, parsers, reports, sources

PARSERS: dict[str, Callable[[str], pd.DataFrame]] = {
    "sea_ice": parsers.parse_sea_ice_daily,
    "gml": parsers.parse_gml_monthly,
    "reader": parsers.parse_reader_monthly,
    "reader_wind": parsers.parse_reader_wind,
    "ozone_annual": parsers.parse_ozone_annual,
    "ozone_daily": parsers.parse_ozone_daily,
    "ice_co2": parsers.parse_ice_core_co2,
    "edc_temp": parsers.parse_edc_temperature,
}
PAGES = [
    "概要",
    "海氷面積",
    "温室効果ガス",
    "オゾンホール",
    "アイスコア",
    "基地の気象",
    "昭和基地の月報",
    "CSVを分析",
    "データソース",
]
GAS_UNITS = {"CO₂": "ppm", "CH₄": "ppb"}
# Station -> gas -> (dataset, download file stem)
GHG_STATIONS: dict[str, dict[str, tuple[sources.Dataset, str]]] = {
    "南極点": {
        "CO₂": (sources.SOUTH_POLE_CO2, "co2_south_pole_monthly"),
        "CH₄": (sources.SOUTH_POLE_CH4, "ch4_south_pole_monthly"),
    },
    "昭和基地": {
        "CO₂": (sources.SYOWA_CO2, "co2_syowa_monthly"),
        "CH₄": (sources.SYOWA_CH4, "ch4_syowa_monthly"),
    },
}
READER_PARSERS = {"wind_speed": "reader_wind"}
FIRST_OZONE_YEAR = 1979
SOURCES_DOC = Path(__file__).with_name("data_sources.md")
REPORT_KEYWORDS = ["カタバ風", "極成層圏雲", "蜃気楼", "暖気", "放射冷却", "極値", "A級"]


@st.cache_data(ttl=3600, show_spinner="データを取得しています…")
def load(url: str, parser: str, max_age: float = sources.DEFAULT_MAX_AGE) -> pd.DataFrame:
    return PARSERS[parser](sources.fetch_text(url, max_age=max_age))


def load_or_report(dataset: sources.Dataset, parser: str) -> pd.DataFrame | None:
    try:
        max_age = st.session_state.get("max_age", sources.DEFAULT_MAX_AGE)
        return load(dataset.url, parser, max_age)
    except (sources.FetchError, parsers.ParseError) as exc:
        st.error(f"**{dataset.title}** を読み込めませんでした。\n\n{exc}")
        st.caption(
            "提供元のサーバーの障害か、ネットワーク接続の問題が考えられます。"
            "一度取得できたデータは "
            f"`{sources.DEFAULT_CACHE_DIR}` にキャッシュされ、オフラインでも表示できます。"
        )
        return None


@st.cache_data(ttl=3600, show_spinner="気象庁の月報の一覧を取得しています…")
def load_report_index(max_age: float) -> list[tuple[int, int]]:
    months = reports.parse_index(sources.fetch_text(sources.JMA_REPORT_INDEX_URL, max_age=max_age))
    if not months:
        raise parsers.ParseError("月報の一覧に月別ページへのリンクが見つかりませんでした")
    return months


@st.cache_data(ttl=3600, show_spinner="気象庁の月報を取得しています…")
def load_report(year: int, month: int) -> reports.MonthlyReport:
    url = sources.jma_report_url(year, month)
    return reports.parse_report(
        sources.fetch_text(url, max_age=sources.JMA_REPORT_MAX_AGE), year, month
    )


@st.cache_data(ttl=3600, show_spinner=False)
def load_reports(
    months: tuple[tuple[int, int], ...],
) -> tuple[list[reports.MonthlyReport], list[str]]:
    """Every listed month, downloaded at a polite pace; months that fail are named."""
    urls = {sources.jma_report_url(y, m): (y, m) for y, m in months}
    texts = sources.fetch_many(list(urls), max_age=sources.JMA_REPORT_MAX_AGE)
    corpus, failed = [], []
    for url, text in texts.items():
        year, month = urls[url]
        try:
            if isinstance(text, sources.FetchError):
                raise text
            corpus.append(reports.parse_report(text, year, month))
        except (sources.FetchError, parsers.ParseError):
            failed.append(f"{year}年{month}月")
    return corpus, failed


def report_months(*, quiet: bool = False) -> list[tuple[int, int]] | None:
    """Months with a JMA report; on failure an error, or only a caption when ``quiet``."""
    try:
        return load_report_index(st.session_state.get("max_age", sources.DEFAULT_MAX_AGE))
    except (sources.FetchError, parsers.ParseError) as exc:
        if quiet:
            st.caption(f"気象庁の月報を取得できませんでした: {exc}")
        else:
            st.error(f"**{sources.JMA_SYOWA_REPORTS.title}** を読み込めませんでした。\n\n{exc}")
        return None


def syowa_monthly() -> dict[str, pd.DataFrame]:
    """READER monthly series at Syowa for each element the reports compare with normal."""
    out = {}
    max_age = st.session_state.get("max_age", sources.DEFAULT_MAX_AGE)
    for key in reports.ELEMENTS:
        dataset = sources.reader_series("Syowa", key)
        try:
            out[key] = load(dataset.url, READER_PARSERS.get(key, "reader"), max_age)
        except (sources.FetchError, parsers.ParseError):
            continue
    return out


def report_view(months: list[tuple[int, int]], key: str) -> None:
    """Pick a month and show its summary next to the numbers it describes."""
    years = sorted({y for y, _ in months}, reverse=True)
    left, right = st.columns(2)
    year = left.selectbox("年", years, key=f"{key}_year")
    options = [m for y, m in months if y == year]
    month = right.selectbox(
        "月", options, index=len(options) - 1, format_func="{}月".format, key=f"{key}_month"
    )
    try:
        report = load_report(year, month)
    except (sources.FetchError, parsers.ParseError) as exc:
        st.error(f"{year}年{month}月の月報を読み込めませんでした。\n\n{exc}")
        return
    monthly = syowa_monthly()
    cols = st.columns(len(reports.ELEMENTS))
    for col, (name, element) in zip(cols, reports.ELEMENTS.items(), strict=True):
        value = reports.stat_value(report, element)
        if value is None:
            continue
        delta, help_text = None, None
        normals = reports.normal_values(monthly[name], year, month) if name in monthly else None
        if normals is not None and len(normals):
            delta = f"{value - normals.mean():+.1f} {element.unit} (平年差)"
            computed = reports.classify(value, normals)
            if computed is not None:
                help_text = f"平年値の期間での区分: {element.level_label(computed)}"
        described = reports.text_level(report.full_text, element)
        if described is not None:
            help_text = f"概況の表現: {element.level_label(described[0])}" + (
                f" / {help_text}" if help_text else ""
            )
        col.metric(
            f"月平均{element.label}",
            f"{value:g} {element.unit}",
            delta,
            delta_color="off",
            help=help_text,
        )
    st.markdown(f"#### {year}年{month}月の概況")
    st.markdown("\n".join(f"> {line}  " for line in report.summary))
    if report.periods:
        with st.expander("旬別の天候経過"):
            for label, text in report.periods:
                st.markdown(f"**{label}**: {text}")
    if report.stats:
        with st.expander("気候統計値"):
            st.dataframe(
                pd.DataFrame(list(report.stats.items()), columns=["項目", "値"]), hide_index=True
            )
    start, end = reports.jma_normal_period(year, month)
    st.caption(
        f"平年差: READER の昭和基地の値から求めた {start}–{end}年の同月平均 "
        "(気象庁がこの月の月報で使っていた平年値の期間) との差。"
        f"原文: [{sources.jma_report_url(year, month)}]({sources.jma_report_url(year, month)})"
    )


def report_corpus(months: list[tuple[int, int]]) -> list[reports.MonthlyReport] | None:
    """All months' reports, after the user agrees to download what is not cached yet."""
    urls = [sources.jma_report_url(y, m) for y, m in months]
    missing = sum(not sources.is_fresh(u, max_age=sources.JMA_REPORT_MAX_AGE) for u in urls)
    if missing and not st.session_state.get("reports_requested"):
        minutes = max(1, round(missing * sources.REQUEST_INTERVAL / 60))
        st.info(
            f"「出来事の推移」「キーワード検索」「表現と偏差」は全{len(months)}か月分の月報を"
            f"使います。未取得の{missing}か月分は、気象庁のサーバーに負担をかけないよう"
            f"{sources.REQUEST_INTERVAL:g}秒間隔で取得するため約{minutes}分かかります。"
            "取得したページは30日間キャッシュされ、次からはすぐに表示されます。"
        )
        if not st.button("全期間の月報を取得"):
            return None
        st.session_state["reports_requested"] = True
    with st.spinner(f"気象庁の月報を取得しています (未取得 {missing} ページ)…"):
        corpus, failed = load_reports(tuple(months))
    if failed:
        st.caption("取得・解析できなかった月: " + "、".join(failed))
    return corpus


def report_notes(months: list[tuple[int, int]]) -> pd.DataFrame | None:
    """First sentence of each month's summary, once every report is available locally.

    Nothing is downloaded here: the full set is fetched only from the 月報 page.
    """
    urls = [sources.jma_report_url(y, m) for y, m in months]
    cached = all(sources.is_fresh(u, max_age=sources.JMA_REPORT_MAX_AGE) for u in urls)
    if not (cached or st.session_state.get("reports_requested")):
        return None
    corpus, _ = load_reports(tuple(months))
    return pd.DataFrame(
        [{"year": r.year, "month": r.month, "note": reports.headline(r)} for r in corpus],
        columns=["year", "month", "note"],
    )


def report_events(corpus: list[reports.MonthlyReport]) -> None:
    events = reports.event_table(corpus)
    c1, c2, c3 = st.columns(3)
    c1.metric("収録した月", f"{len(events)} か月")
    c2.metric("ブリザードの記述がある月", f"{int(events['ブリザード'].sum())} か月")
    c3.metric("回数が書かれている月", f"{int(events['blizzard_count'].notna().sum())} か月")
    st.subheader("ブリザード")
    st.altair_chart(charts.blizzard_grid(events), width="stretch")
    st.caption(
        "数字は概況に書かれたその月のブリザードの回数 (「4回のブリザード」「ブリザードは0回」"
        "など)。旬ごとの回数しか書かれていない月や、回数を書かずに「ブリザードとなった」と"
        "だけある月は「記述のみ」です。「ブリザードとはならなかった」は記述に数えません。"
    )
    st.subheader("出来事が書かれた月の数 (年ごと)")
    long = reports.yearly_event_months(events)
    st.altair_chart(
        charts.count_heatmap(long, "event", "year", "月数", list(reports.EVENTS)), width="stretch"
    )
    st.caption(
        "その年の月報のうち、概況 (と旬別の天候経過) に各出来事が書かれていた月の数です。"
        "語句の一致で数えているため、書き方の変化 (年によって旬ごとの記述が増えるなど) "
        "の影響を受けます。"
    )
    csv_download(events, "syowa_report_events")


def report_search(corpus: list[reports.MonthlyReport]) -> None:
    query = st.text_input(
        "キーワード (スペースで区切ると、いずれかを含む文を探します)", REPORT_KEYWORDS[0]
    )
    st.caption("例: " + " / ".join(REPORT_KEYWORDS))
    hits = reports.search(corpus, query)
    if hits.empty:
        st.info("該当する文はありませんでした。")
        return
    months = hits[["year", "month"]].drop_duplicates()
    st.metric("該当する月", f"{len(months)} / {len(corpus)} か月")
    years = sorted({r.year for r in corpus})
    per_year = (
        months.groupby("year").size().reindex(years, fill_value=0).rename("value").reset_index()
    )
    st.altair_chart(charts.simple_bars(per_year, "year", "value", "該当する月数"), width="stretch")
    table = hits.assign(
        年月=hits["date"].dt.strftime("%Y年%m月"),
        原文=[
            sources.jma_report_url(y, m) for y, m in zip(hits["year"], hits["month"], strict=True)
        ],
    )
    st.dataframe(
        table[["年月", "sentence", "原文"]].rename(columns={"sentence": "文"}),
        hide_index=True,
        column_config={"原文": st.column_config.LinkColumn(display_text="開く")},
    )


def report_expressions(corpus: list[reports.MonthlyReport]) -> None:
    monthly = syowa_monthly()
    table = reports.expression_table(corpus, monthly)
    if table.empty:
        st.info("比べられる月がありませんでした (平年値の計算に使う READER のデータが必要です)。")
        return
    by_label = {e.label: e for e in reports.ELEMENTS.values()}
    present = [label for label in by_label if label in set(table["element"])]
    label = st.radio("要素", present, horizontal=True, key="expression_element")
    element = by_label[label]
    sub = table[table["element"] == label]
    c1, c2, c3 = st.columns(3)
    c1.metric("比べた月", f"{len(sub)} か月")
    c2.metric("向き (低い・平年並・高い) の一致", f"{sub['direction_match'].mean():.0%}")
    c3.metric("「かなり」まで一致", f"{sub['exact_match'].mean():.0%}")
    labels = [element.level_label(level) for level in reports.LEVELS]
    st.altair_chart(charts.expression_matrix(sub, labels), width="content")
    st.caption(
        f"縦: 概況の「月平均{label}は平年より…」の表現。横: 月報の統計表の値が、気象庁がその月に"
        "使っていた平年値の期間 (READER の昭和基地の値) の同じ月の分布のどこにあるか。"
        "下位・上位10%を「かなり」、3等分した中央を「平年並」としています。"
        "表現は語句のルールで読み取っているため、読み違いもあります (下の表で文を確認できます)。"
    )
    shown = sub.assign(
        年月=sub["date"].dt.strftime("%Y年%m月"),
        一致=sub["exact_match"].map({True: "○", False: "×"}),
    )
    shown.loc[~shown["direction_match"], "一致"] = "××"
    st.dataframe(
        shown[["年月", "text_label", "computed_label", "value", "anomaly", "一致", "sentence"]],
        hide_index=True,
        column_config={
            "text_label": "概況の表現",
            "computed_label": "計算した区分",
            "value": st.column_config.NumberColumn(f"値 ({element.unit})", format="%.1f"),
            "anomaly": st.column_config.NumberColumn("平年差", format="%+.1f"),
            "sentence": "文",
        },
    )
    st.caption("一致: ○ 程度まで一致 / × 向きは一致 / ×× 向きが逆または平年並との食い違い")
    csv_download(table, "syowa_report_expressions")


def source_note(dataset: sources.Dataset) -> None:
    st.caption(
        f"出典: {dataset.provider} — [{dataset.homepage}]({dataset.homepage})  \n"
        f"{dataset.description}  \n引用: {dataset.citation}"
    )


def csv_download(df: pd.DataFrame, name: str) -> None:
    st.download_button(
        "CSVをダウンロード",
        df.to_csv(index=False).encode("utf-8"),
        file_name=f"{name}.csv",
        mime="text/csv",
    )


def climatology_or_warn(df: pd.DataFrame, base: tuple[int, int]) -> pd.Series | None:
    try:
        return analysis.monthly_climatology(df, base)
    except ValueError as exc:
        st.warning(str(exc))
        return None


def anomaly_section(
    monthly: pd.DataFrame,
    base: tuple[int, int],
    unit: str,
    *,
    reverse: bool,
    notes: pd.DataFrame | None = None,
):
    """Heatmap and bars of monthly anomalies; ``notes`` (year, month, note) join the tooltip."""
    clim = climatology_or_warn(monthly, base)
    if clim is None:
        return
    anomalies = analysis.monthly_anomalies(monthly, clim)
    if notes is not None:
        anomalies = anomalies.merge(notes, on=["year", "month"], how="left")
        anomalies["note"] = anomalies["note"].fillna("")
    label = f"偏差 ({unit})"
    st.caption(f"{base[0]}–{base[1]}年の月別平均からの偏差")
    st.altair_chart(charts.anomaly_heatmap(anomalies, label, reverse=reverse), width="stretch")
    st.altair_chart(charts.anomaly_bars(anomalies, label, reverse=reverse), width="stretch")


def page_overview(base: tuple[int, int]) -> None:
    st.title("南極観測データ ビューア")
    st.write(
        "南極で取得されている公開観測データを取得・可視化・分析するためのWeb UIです。"
        "左のメニューからデータセットを選んでください。"
    )
    cols = st.columns(3)
    sea_ice = load_or_report(sources.SEA_ICE_EXTENT, "sea_ice")
    if sea_ice is not None:
        rank = analysis.same_day_rank(sea_ice)
        cols[0].metric(
            f"海氷面積 ({rank.date:%Y-%m-%d})",
            f"{rank.value:.2f} 百万km²",
            help=f"同じ日付の中で {rank.total_years} 年中 {rank.rank_lowest} 番目に小さい値",
        )
    co2 = load_or_report(sources.SOUTH_POLE_CO2, "gml")
    if co2 is not None:
        latest = co2.iloc[-1]
        cols[1].metric(f"南極点 CO₂ ({latest['date']:%Y-%m})", f"{latest['value']:.1f} ppm")
    syowa = load_or_report(sources.reader_temperature("Syowa"), "reader")
    if syowa is not None:
        latest = syowa.iloc[-1]
        cols[2].metric(f"昭和基地 月平均気温 ({latest['date']:%Y-%m})", f"{latest['value']:.1f} °C")
    cols = st.columns(3)
    ch4 = load_or_report(sources.SOUTH_POLE_CH4, "gml")
    if ch4 is not None:
        latest = ch4.iloc[-1]
        cols[0].metric(f"南極点 CH₄ ({latest['date']:%Y-%m})", f"{latest['value']:.0f} ppb")
    ozone = load_or_report(sources.OZONE_HOLE_ANNUAL, "ozone_annual")
    if ozone is not None:
        latest = ozone.dropna(subset=["area"]).iloc[-1]
        cols[1].metric(
            f"オゾンホール面積 ({latest['date']:%Y}年)",
            f"{latest['area']:.1f} 百万km²",
            help="9月7日〜10月13日の平均",
        )
    syowa_co2 = load_or_report(sources.SYOWA_CO2, "gml")
    if syowa_co2 is not None:
        latest = syowa_co2.iloc[-1]
        cols[2].metric(f"昭和基地 CO₂ ({latest['date']:%Y-%m})", f"{latest['value']:.1f} ppm")

    st.subheader("収録データセット")
    st.dataframe(
        pd.DataFrame(
            [{"データ": d.title, "提供元": d.provider, "URL": d.homepage} for d in sources.CATALOG]
        ),
        hide_index=True,
        column_config={"URL": st.column_config.LinkColumn()},
    )
    st.caption(f"気候値・偏差の基準期間: {base[0]}–{base[1]}年 (サイドバーで変更できます)")


def page_sea_ice(base: tuple[int, int]) -> None:
    dataset = sources.SEA_ICE_EXTENT
    st.title(dataset.title)
    df = load_or_report(dataset, "sea_ice")
    if df is None:
        return
    rank = analysis.same_day_rank(df)
    days = analysis.with_day_of_year(df)
    try:
        band = analysis.daily_climatology_band(df, base)
    except ValueError as exc:
        st.warning(str(exc))
        band = None

    c1, c2, c3 = st.columns(3)
    c1.metric(f"最新値 ({rank.date:%Y-%m-%d})", f"{rank.value:.2f} 百万km²")
    if band is not None:
        same_day = (band["plot_date"].dt.month == rank.date.month) & (
            band["plot_date"].dt.day == rank.date.day
        )
        normal = band.loc[same_day, "median"]
        if not normal.empty:
            diff = rank.value - float(normal.iloc[0])
            c2.metric("平年 (同日中央値) との差", f"{diff:+.2f} 百万km²")
    c3.metric("同日の順位 (小さい順)", f"{rank.rank_lowest} / {rank.total_years} 年")

    years = sorted(days["year"].unique().tolist())
    latest_year = years[-1]
    defaults = [y for y in (latest_year, latest_year - 1, 2023, 2014) if y in years][:4]
    tab_year, tab_long, tab_anom, tab_ext = st.tabs(
        ["年ごとの比較", "長期変化", "月別偏差", "年最大・最小"]
    )
    with tab_year:
        chosen = st.multiselect("強調表示する年 (最大8)", years, default=defaults, max_selections=8)
        st.altair_chart(
            charts.year_overlay(days, band, chosen, "海氷面積 (百万km²)"), width="stretch"
        )
        st.caption(
            "灰色の細線: その他の年 / 水色の帯: 基準期間の10–90パーセンタイル / "
            "破線: 基準期間の中央値"
        )
    # Before 1987 the record is every other day, hence the 10-sample threshold.
    monthly = analysis.monthly_mean(analysis.drop_incomplete_last_month(df), min_count=10)
    with tab_long:
        trend = analysis.linear_trend(monthly)
        st.altair_chart(
            charts.time_series(
                monthly,
                "海氷面積 (百万km²)",
                smooth=analysis.rolling_mean(monthly, 12),
                trend=analysis.trend_line(monthly, trend),
            ),
            width="stretch",
        )
        st.caption(
            "月平均 (細線)・12か月移動平均 (太線)・" + charts.trend_caption(trend, "百万km²")
        )
    with tab_anom:
        st.caption("海氷が少ないほど赤、多いほど青で表示します。")
        anomaly_section(monthly, base, "百万km²", reverse=True)
    with tab_ext:
        summary = analysis.annual_summary(df)
        summary = summary[summary["year"].isin(analysis.complete_years(df))]
        st.altair_chart(charts.annual_extremes(summary, "海氷面積 (百万km²)"), width="stretch")
        for kind, label in (("min", "年最小"), ("max", "年最大")):
            frame = summary.rename(columns={kind: "value"}).assign(
                date=pd.to_datetime(summary["year"].astype(str) + "-07-01")
            )
            st.caption(f"{label}: " + charts.trend_caption(analysis.linear_trend(frame), "百万km²"))
        st.dataframe(
            summary,
            hide_index=True,
            column_config={
                "year": st.column_config.NumberColumn("年", format="%d"),
                "mean": st.column_config.NumberColumn("年平均", format="%.2f"),
                "min": st.column_config.NumberColumn("年最小", format="%.2f"),
                "min_date": st.column_config.DateColumn("年最小の日", format="YYYY-MM-DD"),
                "max": st.column_config.NumberColumn("年最大", format="%.2f"),
                "max_date": st.column_config.DateColumn("年最大の日", format="YYYY-MM-DD"),
                "count": st.column_config.NumberColumn("日数", format="%d"),
            },
        )
    csv_download(df, "sea_ice_extent_south_daily")
    source_note(dataset)


def page_greenhouse(base: tuple[int, int]) -> None:
    st.title("南極の温室効果ガス")
    station = st.radio("観測所", list(GHG_STATIONS), horizontal=True)
    gas = st.radio("成分", list(GAS_UNITS), horizontal=True)
    dataset, stem = GHG_STATIONS[station][gas]
    unit = GAS_UNITS[gas]
    st.subheader(dataset.title)
    df = load_or_report(dataset, "gml")
    if df is None:
        return
    trend = analysis.linear_trend(df)
    growth = analysis.annual_growth(df)
    c1, c2 = st.columns(2)
    latest = df.iloc[-1]
    c1.metric(f"最新値 ({latest['date']:%Y-%m})", f"{latest['value']:.2f} {unit}")
    if not growth.empty:
        last = growth.iloc[-1]
        c2.metric(f"{int(last['year'])}年の年増加量", f"{last['growth']:+.2f} {unit}/年")
    st.altair_chart(
        charts.time_series(
            df,
            f"{gas} ({unit})",
            smooth=analysis.rolling_mean(df, 12),
            trend=analysis.trend_line(df, trend),
        ),
        width="stretch",
    )
    st.caption(charts.trend_caption(trend, unit))
    left, right = st.columns(2)
    with left:
        st.subheader("平均的な季節変化 (トレンド除去)")
        st.altair_chart(
            charts.seasonal_bars(analysis.seasonal_cycle(df), f"偏差 ({unit})"),
            width="stretch",
        )
    with right:
        st.subheader("年平均の前年差")
        st.altair_chart(
            charts.simple_bars(growth, "year", "growth", f"増加量 ({unit}/年)"),
            width="stretch",
        )
    station_comparison(gas, unit)
    csv_download(df, stem)
    source_note(dataset)


def station_comparison(gas: str, unit: str) -> None:
    """Annual means of ``gas`` at every station, on one axis (12-month years only)."""
    st.subheader(f"観測所の比較 ({gas} 年平均)")
    frames = []
    for name, by_gas in GHG_STATIONS.items():
        dataset, _ = by_gas[gas]
        try:
            max_age = st.session_state.get("max_age", sources.DEFAULT_MAX_AGE)
            df = load(dataset.url, "gml", max_age)
        except (sources.FetchError, parsers.ParseError):
            continue
        full = df[df["date"].dt.year.isin(analysis.complete_years(df))]
        yearly = analysis.annual_summary(full)[["year", "mean"]]
        frames.append(yearly.rename(columns={"mean": "value"}).assign(station=name))
    if len(frames) < 2:
        st.info("比較に必要なデータを取得できませんでした。")
        return
    combined = pd.concat(frames, ignore_index=True)
    order = [f["station"].iloc[0] for f in frames]
    st.altair_chart(
        charts.multi_line(combined, "station", f"{gas} 年平均 ({unit})", order, value_format=".2f"),
        width="stretch",
    )
    first, second = (f.set_index("year")["value"] for f in frames[:2])
    diff = (second - first).dropna()
    note = "12か月そろった年の平均。欠測のある年は線が途切れます。"
    if not diff.empty:
        note += (
            f" 両方そろった{len(diff)}年の差 ({order[1]} − {order[0]}) は平均 "
            f"{diff.mean():+.2f} {unit}、最大でも {diff.abs().max():.2f} {unit} で、"
            "線はほぼ重なります。"
        )
    st.caption(note)


def page_ozone(base: tuple[int, int]) -> None:
    dataset = sources.OZONE_HOLE_ANNUAL
    st.title("南極のオゾンホール")
    st.write(
        "南半球の春 (9〜10月) には、フロン類に由来する塩素によって南極上空のオゾンが"
        "大きく壊されます。オゾン全量が220 DU未満の領域をオゾンホールと呼びます。"
    )
    annual = load_or_report(dataset, "ozone_annual")
    if annual is None:
        return
    area = annual.dropna(subset=["area"])
    latest = area.iloc[-1]
    rank = int((area["area"] > latest["area"]).sum()) + 1
    peak = area.loc[area["area"].idxmax()]
    c1, c2, c3 = st.columns(3)
    c1.metric(
        f"{latest['date']:%Y}年の面積",
        f"{latest['area']:.1f} 百万km²",
        help=f"9月7日〜10月13日の平均。{len(area)} 年中 {rank} 番目の大きさ",
    )
    low = annual.dropna(subset=["min_ozone"])
    if not low.empty:
        last_low = low.iloc[-1]
        c2.metric(f"{last_low['date']:%Y}年の最低オゾン全量", f"{last_low['min_ozone']:.0f} DU")
    c3.metric(f"観測史上最大 ({peak['date']:%Y}年)", f"{peak['area']:.1f} 百万km²")

    tab_annual, tab_daily = st.tabs(["年ごとの推移", "日別の季節変化"])
    with tab_annual:
        for column, title in (("area", "面積 (百万km²)"), ("min_ozone", "最低オゾン全量 (DU)")):
            series = annual[["date", column]].dropna().rename(columns={column: "value"})
            st.altair_chart(charts.time_series(series, title, value_format=".1f"), width="stretch")
        st.caption(
            "面積は9月7日〜10月13日の平均、最低オゾン全量は9月21日〜10月16日の最小値です。"
            "1995年など衛星観測のない年は再解析データで補われています。"
        )
        st.dataframe(annual, hide_index=True)
    with tab_daily:
        years = list(range(date.today().year, FIRST_OZONE_YEAR - 1, -1))
        year = st.selectbox("年", years)
        daily_dataset = sources.ozone_hole_daily(year)
        daily = load_or_report(daily_dataset, "ozone_daily")
        if daily is not None:
            observed = daily.dropna(subset=["value"])
            if observed.empty:
                st.info(f"{year}年の日別データはありません (衛星観測の空白期間など)。")
            else:
                last = observed.iloc[-1]
                top = observed.loc[observed["value"].idxmax()]
                d1, d2 = st.columns(2)
                d1.metric(
                    f"最新値 ({last['date']:%Y-%m-%d})",
                    f"{last['value']:.2f} 百万km²",
                    f"{last['value'] - last['mean']:+.2f} 百万km² (同日平均との差)",
                    delta_color="inverse",
                )
                d2.metric(f"{year}年の最大 ({top['date']:%m-%d})", f"{top['value']:.2f} 百万km²")
                st.altair_chart(charts.ozone_season(daily), width="stretch")
                st.caption(
                    "オレンジの線: 選んだ年 / 水色の帯: 1979年以降の同日の10–90パーセンタイル / "
                    "破線: 平均 / 灰色の線: 最大"
                )
            source_note(daily_dataset)
    csv_download(annual, "ozone_hole_annual")
    source_note(dataset)


def page_ice_core(base: tuple[int, int]) -> None:
    st.title("アイスコア: 過去80万年のCO₂と気温")
    st.write(
        "南極の氷床を掘削した氷の気泡には、当時の大気がそのまま閉じ込められています。"
        "現在の南極点での直接観測と並べると、今のCO₂濃度を自然の変動幅と比べられます。"
    )
    co2 = load_or_report(sources.ICE_CORE_CO2, "ice_co2")
    if co2 is None:
        return
    temperature = load_or_report(sources.EDC_TEMPERATURE, "edc_temp")
    try:
        max_age = st.session_state.get("max_age", sources.DEFAULT_MAX_AGE)
        spo = load(sources.SOUTH_POLE_CO2.url, "gml", max_age)
    except (sources.FetchError, parsers.ParseError):
        spo = None
        st.caption("南極点の直接観測を取得できなかったため、現在値との比較は省略しています。")

    summary = analysis.ice_core_summary(co2)
    c1, c2, c3 = st.columns(3)
    c1.metric(
        "自然の変動幅 (1750年以前)",
        f"{summary.min_value:.0f}〜{summary.max_value:.0f} ppm",
        help=(
            f"最小: 約{summary.min_age_bp / 1000:,.0f}千年前 / "
            f"最大: 約{summary.max_age_bp / 1000:,.0f}千年前"
        ),
    )
    if summary.preindustrial is not None:
        c2.metric("産業革命前 (1000〜1750年の平均)", f"{summary.preindustrial:.0f} ppm")
    modern = None
    if spo is not None:
        latest = spo.iloc[-1]
        modern = float(latest["value"])
        c3.metric(
            f"南極点 直接観測 ({latest['date']:%Y-%m})",
            f"{modern:.0f} ppm",
            f"{modern - summary.max_value:+.0f} ppm (自然の最大値比)",
            delta_color="inverse",
        )

    tab_long, tab_recent, tab_relation = st.tabs(["80万年", "過去2000年", "CO₂と気温の関係"])
    with tab_long:
        st.altair_chart(charts.paleo_co2(co2, modern=modern), width="stretch")
        if temperature is not None:
            st.altair_chart(charts.paleo_temperature(temperature), width="stretch")
        st.caption(
            "上: アイスコアのCO₂ (破線は南極点の最新値) / 下: EPICA Dome C の気温偏差 "
            "(過去1000年平均との差)。約10万年周期で氷期と間氷期が繰り返されています。"
        )
    with tab_recent:
        instrumental = analysis.instrumental_as_age(spo) if spo is not None else None
        st.altair_chart(charts.recent_co2(co2, instrumental, since_year=0), width="stretch")
        st.caption(
            "アイスコア (直近はロードーム) の記録は2001年まで。1975年以降は南極点での"
            "直接観測と重なり、両者がよく一致することを確認できます。"
        )
    with tab_relation:
        if temperature is None:
            st.info("気温データを取得できなかったため表示できません。")
        else:
            pairs = analysis.paired_on_ages(co2, temperature)
            if len(pairs) >= 2:
                r = pairs["co2"].corr(pairs["temperature"])
                st.metric("相関係数 r", f"{r:.2f}", help=f"{len(pairs)} 組のサンプルで計算")
            st.altair_chart(charts.co2_temperature_scatter(pairs), width="stretch")
            st.caption(
                "CO₂の各サンプルの年代に気温を線形補間して対応させています。"
                "相関は氷期サイクルでの両者の連動を示しますが、因果の向きや時間差は示しません。"
            )
    csv_download(co2, "ice_core_co2")
    source_note(sources.ICE_CORE_CO2)
    source_note(sources.EDC_TEMPERATURE)


def page_station(base: tuple[int, int]) -> None:
    st.title("南極観測基地の気象")
    names = list(sources.READER_STATIONS)
    station = st.selectbox("観測基地", names, format_func=sources.READER_STATIONS.__getitem__)
    element = st.radio(
        "要素",
        list(sources.READER_ELEMENTS),
        horizontal=True,
        format_func=lambda key: sources.READER_ELEMENTS[key].label,
    )
    spec = sources.READER_ELEMENTS[element]
    label, unit = spec.label, spec.unit
    parser = READER_PARSERS.get(element, "reader")
    dataset = sources.reader_series(station, element)
    df = load_or_report(dataset, parser)
    if df is None:
        return
    full_years = analysis.complete_years(df)
    annual = analysis.annual_summary(df[df["date"].dt.year.isin(full_years)])
    annual_df = pd.DataFrame(
        {"date": pd.to_datetime(annual["year"].astype(str) + "-07-01"), "value": annual["mean"]}
    )
    c1, c2 = st.columns(2)
    c1.metric("観測期間", f"{df['date'].iloc[0]:%Y-%m} 〜 {df['date'].iloc[-1]:%Y-%m}")
    trend = None
    if len(annual_df) >= 2:
        trend = analysis.linear_trend(annual_df)
        c2.metric(f"年平均{label}のトレンド", f"{trend.slope_per_decade:+.2f} {unit}/10年")

    tab_series, tab_anom, tab_compare = st.tabs(["時系列", "月別偏差", "基地の比較"])
    with tab_series:
        st.altair_chart(
            charts.time_series(df, f"{label} ({unit})", smooth=analysis.rolling_mean(df, 12)),
            width="stretch",
        )
        if trend is not None:
            st.subheader(f"年平均{label}")
            st.altair_chart(
                charts.time_series(
                    annual_df,
                    f"年平均{label} ({unit})",
                    trend=analysis.trend_line(annual_df, trend),
                ),
                width="stretch",
            )
            st.caption(charts.trend_caption(trend, unit) + " (12か月揃った年のみ)")
        clim = climatology_or_warn(df, base)
        if clim is not None:
            st.subheader(f"月別平年値 ({base[0]}–{base[1]}年)")
            cycle = pd.DataFrame({"month": clim.index.astype(int), "value": clim.to_numpy()})
            st.altair_chart(charts.seasonal_bars(cycle, f"{label} ({unit})"), width="stretch")
    with tab_anom:
        months = report_months(quiet=True) if station == "Syowa" else None
        notes = report_notes(months) if months is not None else None
        anomaly_section(df, base, unit, reverse=False, notes=notes)
        if months is not None:
            st.subheader("気象庁の月報で確認する")
            hover = (
                "ヒートマップのセルにマウスを乗せると、その月の概況の冒頭も表示されます。"
                if notes is not None
                else "「昭和基地の月報」ページで全期間の月報を取得すると、ヒートマップの"
                "セルにマウスを乗せたときにその月の概況の冒頭も表示されます。"
            )
            st.caption(
                "偏差の大きな月に何が起きていたかを、気象庁「南極の気象」の概況 (文章) で"
                f"確認できます (2010年1月以降)。{hover}"
            )
            report_view(months, key="station_report")
    with tab_compare:
        chosen = st.multiselect(
            "比較する基地 (最大5)",
            names,
            default=[station],
            max_selections=5,
            format_func=sources.READER_STATIONS.__getitem__,
        )
        frames = []
        for name in chosen:
            other = load_or_report(sources.reader_series(name, element), parser)
            if other is None:
                continue
            clim = climatology_or_warn(other, base)
            if clim is None:
                continue
            anomalies = analysis.monthly_anomalies(other, clim)
            full = anomalies[anomalies["year"].isin(analysis.complete_years(other))]
            yearly = full.groupby("year", as_index=False)["anomaly"].mean()
            station_label = sources.READER_STATIONS[name]
            frames.append(yearly.rename(columns={"anomaly": "value"}).assign(station=station_label))
        if frames:
            order = [f["station"].iloc[0] for f in frames]
            combined = pd.concat(frames, ignore_index=True)
            st.altair_chart(
                charts.multi_line(combined, "station", f"年平均{label}偏差 ({unit})", order),
                width="stretch",
            )
            st.caption(f"各基地の {base[0]}–{base[1]}年平均からの偏差 (12か月揃った年のみ)")
    csv_download(df, f"{element}_{station}")
    source_note(dataset)


def page_reports(base: tuple[int, int]) -> None:
    dataset = sources.JMA_SYOWA_REPORTS
    st.title("昭和基地の月報")
    st.write(
        "気象庁「南極の気象」は、昭和基地のその月の天候を文章 (概況) でまとめています。"
        "数値だけでは分からない背景 (低気圧の通過、ブリザード、記録の更新など) を読み、"
        "文章から出来事を数えたり、言葉と数値を突き合わせたりできます。"
    )
    months = report_months()
    if months is None:
        return
    gate = st.container()
    tab_month, tab_events, tab_search, tab_expr = st.tabs(
        ["月の概況", "出来事の推移", "キーワード検索", "表現と偏差"]
    )
    with tab_month:
        report_view(months, key="report")
    with gate:
        corpus = report_corpus(months)
    for tab, render in (
        (tab_events, report_events),
        (tab_search, report_search),
        (tab_expr, report_expressions),
    ):
        with tab:
            if corpus:
                render(corpus)
            else:
                st.info("全期間の月報を取得すると表示されます。")
    source_note(dataset)


def page_upload(base: tuple[int, int]) -> None:
    st.title("CSVを分析")
    st.write(
        "気象庁「過去の気象データ・ダウンロード」(昭和基地) や PANGAEA などからダウンロードした"
        "時系列データを読み込み、同じ手法 (トレンド・季節変化・偏差) で分析できます。"
        "気象庁のCSV (Shift_JIS・複数行の見出し) と PANGAEA のテキスト形式はそのまま読み込めます。"
    )
    uploaded = st.file_uploader("CSVファイル", type=["csv", "txt", "tab", "tsv"])
    if uploaded is None:
        return
    try:
        raw = parsers.read_upload(uploaded.getvalue())
    except parsers.ParseError as exc:
        st.error(f"CSVを読み込めませんでした: {exc}")
        return
    st.dataframe(raw.head(20))
    columns = list(raw.columns)
    date_col = st.selectbox("日付の列", columns)
    value_col = st.selectbox("値の列", columns, index=min(1, len(columns) - 1))
    unit = st.text_input("単位", parsers.unit_from_label(str(value_col)))
    try:
        df = parsers.parse_user_table(raw, date_col, value_col)
    except parsers.ParseError as exc:
        st.error(str(exc))
        return
    y_title = f"{value_col} ({unit})" if unit else str(value_col)
    trend = analysis.linear_trend(df) if len(df) >= 2 else None
    st.altair_chart(
        charts.time_series(df, y_title, trend=analysis.trend_line(df, trend) if trend else None),
        width="stretch",
    )
    if trend is not None:
        st.caption(charts.trend_caption(trend, unit or "単位"))
    monthly = analysis.monthly_mean(df)
    if len(analysis.complete_years(monthly)) >= 2:
        anomaly_section(monthly, base, unit or "単位", reverse=False)


def page_sources(base: tuple[int, int]) -> None:
    st.markdown(SOURCES_DOC.read_text(encoding="utf-8"))


RENDERERS = {
    "概要": page_overview,
    "海氷面積": page_sea_ice,
    "温室効果ガス": page_greenhouse,
    "オゾンホール": page_ozone,
    "アイスコア": page_ice_core,
    "基地の気象": page_station,
    "昭和基地の月報": page_reports,
    "CSVを分析": page_upload,
    "データソース": page_sources,
}


def main() -> None:
    st.set_page_config(page_title="南極観測データ ビューア", page_icon="🧊", layout="wide")
    with st.sidebar:
        st.header("🧊 南極観測データ")
        page = st.radio("ページ", PAGES, label_visibility="collapsed")
        base = st.slider("気候値の基準期間", 1957, 2025, analysis.DEFAULT_BASE_PERIOD)
        refresh = st.button(
            "データを再取得", help="キャッシュを使わずに最新データをダウンロードします"
        )
        if refresh:
            load.clear()
        st.session_state["max_age"] = 0 if refresh else sources.DEFAULT_MAX_AGE
    RENDERERS[page](base)


main()

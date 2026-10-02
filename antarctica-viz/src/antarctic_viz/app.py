"""Streamlit web UI for exploring public Antarctic observation data.

Run with ``uv run antarctic-viz`` (or ``uv run streamlit run src/antarctic_viz/app.py``).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from antarctic_viz import analysis, charts, parsers, sources

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
    "南極点 温室効果ガス",
    "オゾンホール",
    "アイスコア",
    "基地の気象",
    "CSVを分析",
    "データソース",
]
# Gas label -> (dataset, unit, download file stem)
GASES: dict[str, tuple[sources.Dataset, str, str]] = {
    "CO₂": (sources.SOUTH_POLE_CO2, "ppm", "co2_south_pole_monthly"),
    "CH₄": (sources.SOUTH_POLE_CH4, "ppb", "ch4_south_pole_monthly"),
}
READER_PARSERS = {"wind_speed": "reader_wind"}
FIRST_OZONE_YEAR = 1979
SOURCES_DOC = Path(__file__).with_name("data_sources.md")


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
            "ネットワーク接続を確認してください。一度取得できたデータは "
            f"`{sources.DEFAULT_CACHE_DIR}` にキャッシュされ、オフラインでも表示できます。"
        )
        return None


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


def anomaly_section(monthly: pd.DataFrame, base: tuple[int, int], unit: str, *, reverse: bool):
    clim = climatology_or_warn(monthly, base)
    if clim is None:
        return
    anomalies = analysis.monthly_anomalies(monthly, clim)
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
    st.title("南極点の温室効果ガス")
    gas = st.radio("成分", list(GASES), horizontal=True)
    dataset, unit, stem = GASES[gas]
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
    csv_download(df, stem)
    source_note(dataset)


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
        anomaly_section(df, base, unit, reverse=False)
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
    "南極点 温室効果ガス": page_greenhouse,
    "オゾンホール": page_ozone,
    "アイスコア": page_ice_core,
    "基地の気象": page_station,
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

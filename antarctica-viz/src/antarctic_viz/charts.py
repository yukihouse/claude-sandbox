"""Altair chart builders. Colors follow a colorblind-validated categorical order."""

from __future__ import annotations

import altair as alt
import pandas as pd

from antarctic_viz.analysis import Trend

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
CONTEXT_GRAY = "#a8a7a2"
BAND_BLUE = "#9ec5f4"
COLD, NEUTRAL, WARM = "#2a78d6", "#f0efec", "#e34948"

# A full daily record is ~17k rows; embed it rather than hitting Altair's 5k-row guard.
alt.data_transformers.disable_max_rows()


def _date_x(title: str = "") -> alt.X:
    return alt.X("date:T", title=title)


def break_gaps(df: pd.DataFrame, factor: float = 3.0) -> pd.DataFrame:
    """Insert a null row inside every gap wider than ``factor`` x the typical spacing.

    Lines then stop at an observing outage instead of drawing a straight bridge across it.
    """
    steps = df["date"].diff()
    if len(df) < 3:
        return df
    gap_ends = df.loc[steps > steps.median() * factor, "date"]
    if gap_ends.empty:
        return df
    fillers = pd.DataFrame({"date": gap_ends - steps[gap_ends.index] / 2, "value": float("nan")})
    return pd.concat([df, fillers]).sort_values("date", kind="stable").reset_index(drop=True)


def time_series(
    df: pd.DataFrame,
    y_title: str,
    *,
    smooth: pd.DataFrame | None = None,
    trend: pd.DataFrame | None = None,
    value_format: str = ".2f",
) -> alt.LayerChart:
    """Raw series (thin), optional smoothed overlay and dashed trend line."""
    tooltip = [
        alt.Tooltip("date:T", title="日付"),
        alt.Tooltip("value:Q", title=y_title, format=value_format),
    ]
    base = (
        alt.Chart(break_gaps(df))
        .mark_line(strokeWidth=1, color=SERIES[0], opacity=0.55 if smooth is not None else 1)
        .encode(
            _date_x(), alt.Y("value:Q", title=y_title, scale=alt.Scale(zero=False)), tooltip=tooltip
        )
    )
    layers: list[alt.Chart] = [base]
    if smooth is not None:
        layers.append(
            alt.Chart(break_gaps(smooth))
            .mark_line(strokeWidth=2, color=SERIES[0])
            .encode(_date_x(), alt.Y("value:Q"), tooltip=tooltip)
        )
    if trend is not None:
        layers.append(
            alt.Chart(trend)
            .mark_line(strokeWidth=2, strokeDash=[6, 4], color=SERIES[1])
            .encode(_date_x(), alt.Y("value:Q"))
        )
    return alt.layer(*layers).properties(height=320).interactive(bind_y=False)


def year_overlay(
    days: pd.DataFrame,
    band: pd.DataFrame | None,
    highlight_years: list[int],
    y_title: str,
) -> alt.LayerChart:
    """Every year on a shared Jan–Dec axis; highlighted years in fixed series colors."""
    x = alt.X("plot_date:T", title="", axis=alt.Axis(format="%-m月"))
    context = days[~days["year"].isin(highlight_years)]
    focus = days[days["year"].isin(highlight_years)].assign(
        year_label=lambda d: d["year"].astype(str)
    )
    layers: list[alt.Chart] = []
    if band is not None:
        band_base = alt.Chart(band).encode(x)
        layers.append(
            band_base.mark_area(color=BAND_BLUE, opacity=0.45).encode(y="p10:Q", y2="p90:Q")
        )
        layers.append(
            band_base.mark_line(color=CONTEXT_GRAY, strokeDash=[4, 3], strokeWidth=1.5).encode(
                y="median:Q"
            )
        )
    layers.append(
        alt.Chart(context)
        .mark_line(strokeWidth=0.6, color=CONTEXT_GRAY, opacity=0.35)
        .encode(x, alt.Y("value:Q", title=y_title), detail="year:N")
    )
    palette = SERIES[: max(len(highlight_years), 1)]
    layers.append(
        alt.Chart(focus)
        .mark_line(strokeWidth=2)
        .encode(
            x,
            alt.Y("value:Q", title=y_title),
            color=alt.Color(
                "year_label:N",
                title="年",
                scale=alt.Scale(domain=[str(y) for y in highlight_years], range=palette),
            ),
            tooltip=[
                alt.Tooltip("date:T", title="日付"),
                alt.Tooltip("value:Q", title=y_title, format=".2f"),
            ],
        )
    )
    return alt.layer(*layers).properties(height=360)


def anomaly_bars(anomalies: pd.DataFrame, y_title: str, *, reverse: bool = False) -> alt.Chart:
    """Diverging bars: below-normal in blue, above-normal in red (swapped by ``reverse``)."""
    low, high = (WARM, COLD) if reverse else (COLD, WARM)
    return (
        alt.Chart(anomalies)
        .mark_bar(width={"band": 1})
        .encode(
            _date_x(),
            alt.Y("anomaly:Q", title=y_title),
            color=alt.condition(alt.datum.anomaly < 0, alt.value(low), alt.value(high)),
            tooltip=[
                alt.Tooltip("yearmonth(date):T", title="年月"),
                alt.Tooltip("anomaly:Q", title=y_title, format="+.2f"),
            ],
        )
        .properties(height=260)
    )


def anomaly_heatmap(anomalies: pd.DataFrame, title: str, *, reverse: bool = False) -> alt.Chart:
    """Year x month grid on a diverging blue-gray-red scale centered on zero.

    ``reverse`` flips the poles, e.g. so that *less* sea ice reads as red.
    """
    low, high = (WARM, COLD) if reverse else (COLD, WARM)
    limit = float(anomalies["anomaly"].abs().quantile(0.98)) or 1.0
    return (
        alt.Chart(anomalies)
        .mark_rect(stroke="white", strokeWidth=0.5)
        .encode(
            alt.X("month:O", title="", axis=alt.Axis(labelExpr="datum.value + '月'", labelAngle=0)),
            alt.Y("year:O", title="", sort="descending"),
            color=alt.Color(
                "anomaly:Q",
                title=title,
                scale=alt.Scale(
                    domain=[-limit, 0, limit],
                    range=[low, NEUTRAL, high],
                    interpolate="lab",
                    clamp=True,
                ),
            ),
            tooltip=[
                alt.Tooltip("year:O", title="年"),
                alt.Tooltip("month:O", title="月"),
                alt.Tooltip("value:Q", title="値", format=".2f"),
                alt.Tooltip("anomaly:Q", title=title, format="+.2f"),
            ],
        )
        .properties(height=alt.Step(9))
    )


def seasonal_bars(cycle: pd.DataFrame, y_title: str) -> alt.Chart:
    return (
        alt.Chart(cycle)
        .mark_bar(color=SERIES[0], cornerRadiusEnd=4)
        .encode(
            alt.X("month:O", title="", axis=alt.Axis(labelExpr="datum.value + '月'", labelAngle=0)),
            alt.Y("value:Q", title=y_title),
            tooltip=[alt.Tooltip("month:O", title="月"), alt.Tooltip("value:Q", format="+.2f")],
        )
        .properties(height=260)
    )


def annual_extremes(summary: pd.DataFrame, y_title: str) -> alt.Chart:
    """Annual minimum and maximum as two labelled lines on one axis."""
    long = summary.melt(
        id_vars="year", value_vars=["min", "max"], var_name="kind", value_name="value"
    )
    long["kind"] = long["kind"].map({"min": "年最小", "max": "年最大"})
    return (
        alt.Chart(long)
        .mark_line(point=alt.OverlayMarkDef(size=40), strokeWidth=2)
        .encode(
            alt.X("year:Q", title="", axis=alt.Axis(format="d")),
            alt.Y("value:Q", title=y_title, scale=alt.Scale(zero=False)),
            color=alt.Color(
                "kind:N", title="", scale=alt.Scale(domain=["年最大", "年最小"], range=SERIES[:2])
            ),
            tooltip=[
                alt.Tooltip("year:Q", title="年", format="d"),
                alt.Tooltip("kind:N", title="種別"),
                alt.Tooltip("value:Q", title=y_title, format=".2f"),
            ],
        )
        .properties(height=280)
    )


def trend_caption(trend: Trend, unit: str) -> str:
    return (
        f"線形トレンド: {trend.slope_per_decade:+.3f} {unit}/10年 "
        f"(R² = {trend.r_squared:.2f}, n = {trend.n})"
    )


def fill_missing_years(df: pd.DataFrame, group: str) -> pd.DataFrame:
    """Add a null row for every year missing inside each series, so its line breaks there."""
    parts = []
    for key, part in df.groupby(group, sort=False):
        years = pd.RangeIndex(int(part["year"].min()), int(part["year"].max()) + 1, name="year")
        parts.append(part.set_index("year").reindex(years).assign(**{group: key}).reset_index())
    return pd.concat(parts, ignore_index=True)


def multi_line(df: pd.DataFrame, color_field: str, y_title: str, order: list[str]) -> alt.Chart:
    """Several yearly series on one axis, colored in fixed categorical order by ``order``."""
    return (
        alt.Chart(fill_missing_years(df, color_field))
        .mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=20))
        .encode(
            alt.X("year:Q", title="", axis=alt.Axis(format="d")),
            alt.Y("value:Q", title=y_title),
            color=alt.Color(
                f"{color_field}:N",
                title="",
                scale=alt.Scale(domain=order, range=SERIES[: len(order)]),
            ),
            tooltip=[
                alt.Tooltip(f"{color_field}:N", title="系列"),
                alt.Tooltip("year:Q", title="年", format="d"),
                alt.Tooltip("value:Q", title=y_title, format="+.2f"),
            ],
        )
        .properties(height=320)
    )


def simple_bars(df: pd.DataFrame, x: str, y: str, y_title: str) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_bar(color=SERIES[0], cornerRadiusEnd=4)
        .encode(
            alt.X(f"{x}:O", title=""),
            alt.Y(f"{y}:Q", title=y_title),
            tooltip=[alt.Tooltip(f"{x}:O"), alt.Tooltip(f"{y}:Q", title=y_title, format=".2f")],
        )
        .properties(height=260)
    )


# Fixed axis span and y-axis width keep the stacked paleo charts aligned.
_PALEO_Y_EXTENT = 40
_PALEO_DOMAIN_KA = [-0.1, 810]


def _ka_x() -> alt.X:
    # Reversed so time runs left (past) to right (present).
    return alt.X(
        "ka:Q",
        title="千年前",
        scale=alt.Scale(domain=_PALEO_DOMAIN_KA, reverse=True, nice=False, clamp=True),
        axis=alt.Axis(format="d"),
    )


def _with_ka(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(ka=df["age_bp"] / 1000)


def paleo_co2(co2: pd.DataFrame, *, modern: float | None = None) -> alt.LayerChart:
    """800 kyr ice-core CO2, with the latest direct measurement as a dashed reference."""
    line = (
        alt.Chart(_with_ka(co2))
        .mark_line(strokeWidth=1.5, color=SERIES[0])
        .encode(
            _ka_x(),
            alt.Y(
                "value:Q",
                title="CO₂ (ppm)",
                scale=alt.Scale(zero=False),
                axis=alt.Axis(minExtent=_PALEO_Y_EXTENT),
            ),
            tooltip=[
                alt.Tooltip("ka:Q", title="千年前", format=",.1f"),
                alt.Tooltip("value:Q", title="CO₂ (ppm)", format=".1f"),
            ],
        )
    )
    layers: list[alt.Chart] = [line]
    if modern is not None:
        rule = pd.DataFrame({"value": [modern], "label": [f"現在 {modern:.0f} ppm"]})
        layers.append(
            alt.Chart(rule).mark_rule(color=SERIES[1], strokeDash=[6, 4]).encode(y="value:Q")
        )
        layers.append(
            alt.Chart(rule)
            .mark_text(align="left", dx=4, dy=-6, color=SERIES[1], x=0)
            .encode(y="value:Q", text="label:N")
        )
    return alt.layer(*layers).properties(height=260)


def paleo_temperature(temperature: pd.DataFrame) -> alt.Chart:
    """Antarctic temperature anomaly on the same reversed age axis as ``paleo_co2``."""
    return (
        alt.Chart(_with_ka(temperature))
        .mark_line(strokeWidth=1, color=SERIES[3])
        .encode(
            _ka_x(),
            alt.Y("value:Q", title="気温偏差 (°C)", axis=alt.Axis(minExtent=_PALEO_Y_EXTENT)),
            tooltip=[
                alt.Tooltip("ka:Q", title="千年前", format=",.1f"),
                alt.Tooltip("value:Q", title="気温偏差 (°C)", format="+.2f"),
            ],
        )
        .properties(height=200)
    )


def recent_co2(ice: pd.DataFrame, instrumental: pd.DataFrame | None, since_year: int) -> alt.Chart:
    """Ice-core CO2 joined to direct South Pole measurements on a calendar-year axis."""
    parts = [ice.assign(source="アイスコア")]
    if instrumental is not None:
        parts.append(instrumental.assign(source="南極点 直接観測"))
    df = pd.concat(parts, ignore_index=True)
    df["year"] = 1950 - df["age_bp"]
    df = df[df["year"] >= since_year]
    order = ["アイスコア", "南極点 直接観測"]
    return (
        alt.Chart(df)
        .mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=12))
        .encode(
            alt.X("year:Q", title="西暦年", scale=alt.Scale(nice=False), axis=alt.Axis(format="d")),
            alt.Y("value:Q", title="CO₂ (ppm)", scale=alt.Scale(zero=False)),
            color=alt.Color("source:N", title="", scale=alt.Scale(domain=order, range=SERIES[:2])),
            tooltip=[
                alt.Tooltip("source:N", title="データ"),
                alt.Tooltip("year:Q", title="年", format=".0f"),
                alt.Tooltip("value:Q", title="CO₂ (ppm)", format=".1f"),
            ],
        )
        .properties(height=320)
        .interactive(bind_y=False)
    )


def co2_temperature_scatter(pairs: pd.DataFrame) -> alt.Chart:
    """CO2 against interpolated temperature, shaded by age."""
    return (
        alt.Chart(_with_ka(pairs))
        .mark_circle(size=18, opacity=0.7)
        .encode(
            alt.X("co2:Q", title="CO₂ (ppm)", scale=alt.Scale(zero=False)),
            alt.Y("temperature:Q", title="気温偏差 (°C)"),
            color=alt.Color("ka:Q", title="千年前", scale=alt.Scale(scheme="blues", reverse=True)),
            tooltip=[
                alt.Tooltip("ka:Q", title="千年前", format=",.1f"),
                alt.Tooltip("co2:Q", title="CO₂ (ppm)", format=".1f"),
                alt.Tooltip("temperature:Q", title="気温偏差 (°C)", format="+.2f"),
            ],
        )
        .properties(height=340)
    )


def ozone_season(daily: pd.DataFrame) -> alt.LayerChart:
    """One year's daily ozone-hole area against the 1979-onward climatology band."""
    y_title = "オゾンホール面積 (百万km²)"
    x = alt.X("date:T", title="", axis=alt.Axis(format="%-m月"))
    band = alt.Chart(daily).encode(x)
    line = daily.dropna(subset=["value"])[["date", "value"]]
    layers: list[alt.Chart] = [
        band.mark_area(color=BAND_BLUE, opacity=0.45).encode(
            alt.Y("p10:Q", title=y_title), y2="p90:Q"
        ),
        band.mark_line(color=CONTEXT_GRAY, strokeDash=[4, 3], strokeWidth=1.5).encode(y="mean:Q"),
        band.mark_line(color=CONTEXT_GRAY, strokeWidth=1).encode(y="maximum:Q"),
        alt.Chart(break_gaps(line))
        .mark_line(strokeWidth=2.5, color=SERIES[1])
        .encode(
            x,
            alt.Y("value:Q"),
            tooltip=[
                alt.Tooltip("date:T", title="日付"),
                alt.Tooltip("value:Q", title=y_title, format=".2f"),
            ],
        ),
    ]
    return alt.layer(*layers).properties(height=360)

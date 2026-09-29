"""Analysis helpers over ``date``/``value`` DataFrames produced by ``parsers``."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

DEFAULT_BASE_PERIOD = (1981, 2010)
_REFERENCE_YEAR = 2001  # non-leap year used to map month/day onto a day-of-year axis


@dataclass(frozen=True)
class Trend:
    slope_per_year: float
    intercept: float
    r_squared: float
    n: int

    @property
    def slope_per_decade(self) -> float:
        return self.slope_per_year * 10


def decimal_year(dates: pd.Series) -> pd.Series:
    dates = pd.to_datetime(dates)
    start = pd.to_datetime(dates.dt.year.astype(str) + "-01-01")
    days_in_year = np.where(dates.dt.is_leap_year, 366.0, 365.0)
    return dates.dt.year + (dates - start).dt.days / days_in_year


def linear_trend(df: pd.DataFrame) -> Trend:
    """Least-squares linear trend of ``value`` against decimal year."""
    clean = df.dropna(subset=["value"])
    if len(clean) < 2:
        raise ValueError("トレンド計算には2点以上のデータが必要です")
    x = decimal_year(clean["date"]).to_numpy(dtype=float)
    y = clean["value"].to_numpy(dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    residual = y - (slope * x + intercept)
    total = ((y - y.mean()) ** 2).sum()
    r_squared = 1 - (residual**2).sum() / total if total else 1.0
    return Trend(float(slope), float(intercept), float(r_squared), len(clean))


def trend_line(df: pd.DataFrame, trend: Trend) -> pd.DataFrame:
    """Fitted values at the first and last date, for drawing the trend line."""
    ends = df["date"].iloc[[0, -1]].reset_index(drop=True)
    fitted = trend.slope_per_year * decimal_year(ends) + trend.intercept
    return pd.DataFrame({"date": ends, "value": fitted.to_numpy()})


def monthly_mean(df: pd.DataFrame, min_count: int = 1) -> pd.DataFrame:
    """Resample to calendar months, dropping months with fewer than ``min_count`` samples."""
    grouped = df.set_index("date")["value"].resample("MS").agg(["mean", "count"])
    grouped = grouped[grouped["count"] >= max(min_count, 1)]
    return grouped["mean"].rename("value").reset_index()


def drop_incomplete_last_month(df: pd.DataFrame) -> pd.DataFrame:
    """Drop the trailing month unless the record reaches that month's last day.

    A half-finished month would otherwise be compared against full-month normals.
    """
    last = df["date"].iloc[-1]
    if last.is_month_end:
        return df
    return df[df["date"] < last.replace(day=1)].reset_index(drop=True)


def rolling_mean(df: pd.DataFrame, window: int) -> pd.DataFrame:
    """Trailing mean over ``window`` calendar months of monthly data.

    Missing months count as gaps, so the mean never reaches across a multi-year outage.
    """
    out = df.copy()
    series = df.set_index("date")["value"]
    calendar = series.resample("MS").mean()
    smoothed = calendar.rolling(window, min_periods=max(1, window // 2)).mean()
    out["value"] = smoothed.reindex(df["date"]).to_numpy()
    return out


def monthly_climatology(df: pd.DataFrame, base: tuple[int, int] = DEFAULT_BASE_PERIOD) -> pd.Series:
    """Mean value per calendar month (1..12) over the base period, inclusive."""
    years = df["date"].dt.year
    in_base = df[(years >= base[0]) & (years <= base[1])]
    if in_base.empty:
        raise ValueError(f"基準期間 {base[0]}–{base[1]} のデータがありません")
    return in_base.groupby(in_base["date"].dt.month)["value"].mean()


def monthly_anomalies(monthly: pd.DataFrame, climatology: pd.Series) -> pd.DataFrame:
    """Departure of each monthly value from its calendar-month climatology."""
    out = monthly.copy()
    out["year"] = out["date"].dt.year
    out["month"] = out["date"].dt.month
    out["anomaly"] = out["value"] - out["month"].map(climatology)
    return out.dropna(subset=["anomaly"]).reset_index(drop=True)


def annual_summary(df: pd.DataFrame, min_count: int = 1) -> pd.DataFrame:
    """Per-year mean/min/max with the dates the extremes occurred."""
    work = df.assign(year=df["date"].dt.year)
    grouped = work.groupby("year")
    summary = pd.DataFrame(
        {
            "mean": grouped["value"].mean(),
            "min": grouped["value"].min(),
            "min_date": work.loc[grouped["value"].idxmin(), "date"].to_numpy(),
            "max": grouped["value"].max(),
            "max_date": work.loc[grouped["value"].idxmax(), "date"].to_numpy(),
            "count": grouped["value"].count(),
        }
    )
    return summary[summary["count"] >= min_count].reset_index()


def complete_years(df: pd.DataFrame, months_required: int = 12) -> list[int]:
    """Years whose data covers at least ``months_required`` distinct months."""
    months = df.groupby(df["date"].dt.year)["date"].apply(lambda d: d.dt.month.nunique())
    return [int(y) for y, n in months.items() if n >= months_required]


def with_day_of_year(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``year`` and a leap-agnostic ``doy`` (Feb 29 dropped) plus a plot date."""
    out = df[~((df["date"].dt.month == 2) & (df["date"].dt.day == 29))].copy()
    out["year"] = out["date"].dt.year
    out["plot_date"] = pd.to_datetime(
        {"year": _REFERENCE_YEAR, "month": out["date"].dt.month, "day": out["date"].dt.day}
    )
    out["doy"] = out["plot_date"].dt.dayofyear
    return out.reset_index(drop=True)


def daily_climatology_band(
    df: pd.DataFrame, base: tuple[int, int] = DEFAULT_BASE_PERIOD
) -> pd.DataFrame:
    """Median and 10th/90th percentile per day of year over the base period."""
    days = with_day_of_year(df)
    days = days[(days["year"] >= base[0]) & (days["year"] <= base[1])]
    if days.empty:
        raise ValueError(f"基準期間 {base[0]}–{base[1]} のデータがありません")
    grouped = days.groupby("plot_date")["value"]
    return pd.DataFrame(
        {
            "median": grouped.median(),
            "p10": grouped.quantile(0.1),
            "p90": grouped.quantile(0.9),
        }
    ).reset_index()


@dataclass(frozen=True)
class SameDayRank:
    date: pd.Timestamp
    value: float
    rank_lowest: int
    total_years: int
    previous_record: float | None


def same_day_rank(df: pd.DataFrame) -> SameDayRank:
    """Rank the latest value among the same calendar day in every year (1 = lowest)."""
    latest = df.iloc[-1]
    day = latest["date"]
    same_day = df[(df["date"].dt.month == day.month) & (df["date"].dt.day == day.day)]
    others = same_day[same_day["date"] != day]["value"]
    rank = int((others < latest["value"]).sum()) + 1
    return SameDayRank(
        date=day,
        value=float(latest["value"]),
        rank_lowest=rank,
        total_years=len(same_day),
        previous_record=float(others.min()) if not others.empty else None,
    )


def seasonal_cycle(monthly: pd.DataFrame) -> pd.DataFrame:
    """Mean detrended departure per calendar month (the average seasonal cycle)."""
    trend = linear_trend(monthly)
    detrended = monthly["value"] - (
        trend.slope_per_year * decimal_year(monthly["date"]) + trend.intercept
    )
    cycle = detrended.groupby(monthly["date"].dt.month).mean()
    return pd.DataFrame({"month": cycle.index.astype(int), "value": cycle.to_numpy()})


def annual_growth(monthly: pd.DataFrame, months_required: int = 12) -> pd.DataFrame:
    """Year-over-year change in the annual mean, for consecutive complete years only."""
    years = complete_years(monthly, months_required)
    subset = monthly[monthly["date"].dt.year.isin(years)]
    annual = subset.groupby(subset["date"].dt.year)["value"].mean()
    growth = annual.diff()[annual.index.to_series().diff() == 1]
    return pd.DataFrame(
        {
            "year": growth.index.astype(int),
            "mean": annual.loc[growth.index].to_numpy(),
            "growth": growth.to_numpy(),
        }
    )

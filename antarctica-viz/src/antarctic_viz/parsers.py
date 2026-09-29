"""Parsers turning the raw text files of each data source into tidy DataFrames.

Every parser returns a DataFrame with a ``date`` (Timestamp) column and a float
``value`` column, sorted by date, so the analysis and chart code can treat all
sources the same way. Ice-core records reach 800,000 years back, beyond what a
Timestamp can hold, so their parsers use an ``age_bp`` column (years before 1950)
instead of ``date``.
"""

from __future__ import annotations

import re
from datetime import date

import pandas as pd

MISSING_THRESHOLD = -999.0
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

"""Synthetic inputs in each source's file format, for tests that need long series."""

import math
from datetime import date, timedelta
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def sea_ice_text(start_year: int = 1979, end: date = date(2025, 9, 15)) -> str:
    lines = [" Year, Month, Day,     Extent,    Missing, Source Data", " YYYY, MM, DD, x, x, x"]
    day = date(start_year, 1, 1)
    while day <= end:
        doy = date(2001, day.month, min(day.day, 28 if day.month == 2 else 31)).timetuple().tm_yday
        extent = 11 - 8 * math.cos(2 * math.pi * (doy - 50) / 365) - 0.01 * (day.year - 1979)
        lines.append(f" {day.year}, {day.month:5d}, {day.day:5d}, {extent:10.3f}, 0.000, ['x']")
        day += timedelta(days=1)
    return "\n".join(lines) + "\n"


def gml_text(start_year: int = 1976, end_year: int = 2024, last_month: int = 6) -> str:
    fields = "site_code year month day value qcflag"
    lines = [f"# data_fields: {fields}"]
    for year in range(start_year, end_year + 1):
        for month in range(1, 13 if year < end_year else last_month + 1):
            value = 330 + 1.8 * (year - start_year) + 0.5 * math.sin(month)
            lines.append(f"SPO {year} {month} 1 {value:.2f} ...")
    return "\n".join(lines) + "\n"


def reader_text(start_year: int = 1957, end_year: int = 2024, offset: float = 0.0) -> str:
    lines = ["Station Temperature", "Year Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec"]
    for year in range(start_year, end_year + 1):
        values = [
            -10 - 9 * math.cos(2 * math.pi * (m - 1) / 12) + 0.02 * (year - 1957) + offset
            for m in range(12)
        ]
        cells = [f"{v:.1f}" for v in values]
        if year == end_year:
            cells[6:] = ["-"] * 6
        lines.append(f"{year} " + " ".join(cells))
    return "\n".join(lines) + "\n"

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


def _glacial(age_bp: float) -> float:
    return math.sin(2 * math.pi * age_bp / 100_000)


def ice_core_co2_text(oldest_bp: int = 800_000, step: int = 2_000) -> str:
    """NCEI composite layout: ``#`` header, column names, tab-separated rows."""
    lines = [
        "\ufeff# Antarctic Ice Cores Revised 800KYr CO2 Data",
        "#",
        "age_gas_calBP\tco2_ppm\tco2_1s_ppm",
    ]
    lines += [f"{age:.2f}\t{360 - 1.5 * (age + 51):.2f}\t0.10" for age in (-51, -20, 0)]
    lines += [f"{age:.2f}\t{280.0:.2f}\t0.50" for age in range(100, 1000, 100)]
    lines += [
        f"{age:.2f}\t{235 + 50 * _glacial(age):.2f}\t1.00" for age in range(step, oldest_bp, step)
    ]
    return "\n".join(lines) + "\n"


def edc_text(oldest_bp: int = 800_000, step: int = 1_000) -> str:
    """EPICA Dome C layout: free-text preamble then ``Bag ztop Age Deuterium Temperature``."""
    lines = ["EPICA Dome C Ice Core 800KYr Deuterium Data", "Column 1: Bag number", ""]
    lines.append(" Bag         ztop          Age         Deuterium    Temperature")
    lines.append("   1            0        -50.00000")
    for bag, age in enumerate(range(0, oldest_bp, step), start=2):
        temp = -4 + 5 * _glacial(age)
        deut = f"{-400 + 8 * temp:.1f}" if bag % 50 else ""
        lines.append(f"{bag:4d} {bag * 0.55:12.2f} {age:16.5f} {deut:>12} {temp:14.2f}")
    return "\n".join(lines) + "\n"

import unittest

import pandas as pd

from antarctic_viz import analysis, parsers
from tests.helpers import gml_text, reader_text, sea_ice_text


def series(dates, values):
    return pd.DataFrame({"date": pd.to_datetime(dates), "value": values})


class TestTrend(unittest.TestCase):
    def test_recovers_linear_slope(self):
        df = series([f"{y}-07-02" for y in range(2000, 2010)], [2.0 * i for i in range(10)])
        trend = analysis.linear_trend(df)
        self.assertAlmostEqual(trend.slope_per_year, 2.0, places=2)
        self.assertAlmostEqual(trend.slope_per_decade, 20.0, places=1)
        self.assertAlmostEqual(trend.r_squared, 1.0, places=6)
        self.assertEqual(trend.n, 10)

    def test_constant_series_has_perfect_fit(self):
        df = series(["2000-01-01", "2001-01-01"], [5.0, 5.0])
        self.assertEqual(analysis.linear_trend(df).r_squared, 1.0)

    def test_needs_two_points(self):
        with self.assertRaises(ValueError):
            analysis.linear_trend(series(["2000-01-01"], [1.0]))

    def test_trend_line_spans_first_and_last_date(self):
        df = series(["2000-01-01", "2010-01-01"], [0.0, 10.0])
        line = analysis.trend_line(df, analysis.linear_trend(df))
        self.assertEqual(line["date"].tolist(), df["date"].tolist())
        self.assertAlmostEqual(line["value"].iloc[1], 10.0, places=6)

    def test_decimal_year_handles_leap_years(self):
        years = analysis.decimal_year(pd.Series(pd.to_datetime(["2020-07-02", "2021-01-01"])))
        self.assertAlmostEqual(years.iloc[0], 2020 + 183 / 366)
        self.assertEqual(years.iloc[1], 2021.0)


class TestResampling(unittest.TestCase):
    def test_monthly_mean_respects_min_count(self):
        df = series(["2000-01-01", "2000-01-02", "2000-02-01"], [1.0, 3.0, 9.0])
        self.assertEqual(analysis.monthly_mean(df)["value"].tolist(), [2.0, 9.0])
        self.assertEqual(analysis.monthly_mean(df, min_count=2)["value"].tolist(), [2.0])

    def test_drop_incomplete_last_month(self):
        partial = series(["2000-01-31", "2000-02-01", "2000-02-15"], [1.0, 2.0, 3.0])
        self.assertEqual(len(analysis.drop_incomplete_last_month(partial)), 1)
        complete = series(["2000-01-30", "2000-01-31"], [1.0, 2.0])
        self.assertEqual(len(analysis.drop_incomplete_last_month(complete)), 2)

    def test_rolling_mean_does_not_mutate_input(self):
        df = series(["2000-01-01", "2000-02-01", "2000-03-01"], [1.0, 2.0, 3.0])
        out = analysis.rolling_mean(df, 2)
        self.assertEqual(out["value"].tolist(), [1.0, 1.5, 2.5])
        self.assertEqual(df["value"].tolist(), [1.0, 2.0, 3.0])


class TestClimatology(unittest.TestCase):
    def setUp(self):
        self.monthly = parsers.parse_reader_monthly(reader_text(1970, 2000))

    def test_climatology_and_anomalies(self):
        clim = analysis.monthly_climatology(self.monthly, (1981, 1990))
        self.assertEqual(list(clim.index), list(range(1, 13)))
        anomalies = analysis.monthly_anomalies(self.monthly, clim)
        base = anomalies[anomalies["year"].between(1981, 1990)]
        self.assertAlmostEqual(base["anomaly"].mean(), 0.0, places=6)
        self.assertGreater(anomalies["anomaly"].iloc[-1], anomalies["anomaly"].iloc[0])

    def test_missing_base_period_raises(self):
        with self.assertRaises(ValueError):
            analysis.monthly_climatology(self.monthly, (1900, 1910))

    def test_complete_years_excludes_partial_final_year(self):
        years = analysis.complete_years(self.monthly)
        self.assertEqual(years[0], 1970)
        self.assertNotIn(2000, years)
        self.assertIn(2000, analysis.complete_years(self.monthly, months_required=6))


class TestDaily(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = parsers.parse_sea_ice_daily(sea_ice_text(1979))

    def test_day_of_year_drops_feb_29_and_aligns_years(self):
        days = analysis.with_day_of_year(self.df)
        self.assertFalse(((days["date"].dt.month == 2) & (days["date"].dt.day == 29)).any())
        march_first = days[(days["date"].dt.month == 3) & (days["date"].dt.day == 1)]
        self.assertEqual(set(march_first["doy"]), {60})

    def test_band_is_ordered(self):
        band = analysis.daily_climatology_band(self.df, (1981, 2010))
        self.assertEqual(len(band), 365)
        self.assertTrue((band["p10"] <= band["median"]).all())
        self.assertTrue((band["median"] <= band["p90"]).all())

    def test_band_without_base_data_raises(self):
        with self.assertRaises(ValueError):
            analysis.daily_climatology_band(self.df, (1950, 1960))

    def test_annual_summary_reports_extremes(self):
        summary = analysis.annual_summary(self.df)
        first = summary.iloc[0]
        self.assertEqual(first["year"], 1979)
        self.assertLess(first["min"], first["max"])
        self.assertEqual(pd.Timestamp(first["min_date"]).month, 2)
        self.assertEqual(len(analysis.annual_summary(self.df, min_count=365)), len(summary) - 1)

    def test_same_day_rank_of_declining_series_is_lowest(self):
        rank = analysis.same_day_rank(self.df)
        self.assertEqual(rank.rank_lowest, 1)
        self.assertEqual(rank.total_years, 2025 - 1979 + 1)
        self.assertGreater(rank.previous_record, rank.value)

    def test_same_day_rank_with_single_year(self):
        rank = analysis.same_day_rank(series(["2020-01-01"], [1.0]))
        self.assertEqual((rank.rank_lowest, rank.total_years), (1, 1))
        self.assertIsNone(rank.previous_record)


class TestCo2(unittest.TestCase):
    def setUp(self):
        self.df = parsers.parse_gml_monthly(gml_text(2000, 2010))

    def test_seasonal_cycle_has_twelve_zero_mean_months(self):
        cycle = analysis.seasonal_cycle(self.df)
        self.assertEqual(cycle["month"].tolist(), list(range(1, 13)))
        self.assertLess(abs(cycle["value"].mean()), 0.05)

    def test_annual_growth_uses_complete_years(self):
        growth = analysis.annual_growth(self.df)
        self.assertEqual(growth["year"].tolist(), list(range(2001, 2010)))
        for value in growth["growth"]:
            self.assertAlmostEqual(value, 1.8, places=6)

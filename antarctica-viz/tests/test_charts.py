import unittest

from antarctic_viz import analysis, charts, parsers
from tests.helpers import reader_text, sea_ice_text


class TestCharts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.monthly = parsers.parse_reader_monthly(reader_text(1975, 2000))
        clim = analysis.monthly_climatology(cls.monthly, (1981, 1990))
        cls.anomalies = analysis.monthly_anomalies(cls.monthly, clim)
        cls.daily = parsers.parse_sea_ice_daily(sea_ice_text(1990))

    def spec(self, chart):
        spec = chart.to_dict()
        self.assertIn("$schema", spec)
        return spec

    def test_time_series_layers(self):
        trend = analysis.linear_trend(self.monthly)
        plain = self.spec(charts.time_series(self.monthly, "T"))
        full = self.spec(
            charts.time_series(
                self.monthly,
                "T",
                smooth=analysis.rolling_mean(self.monthly, 12),
                trend=analysis.trend_line(self.monthly, trend),
            )
        )
        self.assertEqual(len(plain["layer"]), 1)
        self.assertEqual(len(full["layer"]), 3)

    def test_year_overlay_colors_highlighted_years_in_order(self):
        days = analysis.with_day_of_year(self.daily)
        band = analysis.daily_climatology_band(self.daily, (1991, 2000))
        spec = self.spec(charts.year_overlay(days, band, [2025, 2024], "E"))
        focus = spec["layer"][-1]["encoding"]["color"]["scale"]
        self.assertEqual(focus["domain"], ["2025", "2024"])
        self.assertEqual(focus["range"], charts.SERIES[:2])
        without_band = self.spec(charts.year_overlay(days, None, [], "E"))
        self.assertEqual(len(without_band["layer"]), 2)

    def test_anomaly_heatmap_can_reverse_poles(self):
        normal = self.spec(charts.anomaly_heatmap(self.anomalies, "A"))
        flipped = self.spec(charts.anomaly_heatmap(self.anomalies, "A", reverse=True))
        self.assertEqual(normal["encoding"]["color"]["scale"]["range"][0], charts.COLD)
        self.assertEqual(flipped["encoding"]["color"]["scale"]["range"][0], charts.WARM)

    def test_anomaly_heatmap_all_zero_uses_unit_domain(self):
        flat = self.anomalies.assign(anomaly=0.0)
        spec = self.spec(charts.anomaly_heatmap(flat, "A"))
        self.assertEqual(spec["encoding"]["color"]["scale"]["domain"], [-1.0, 0, 1.0])

    def test_other_charts_serialize(self):
        bars = self.spec(charts.anomaly_bars(self.anomalies, "A"))
        flipped = self.spec(charts.anomaly_bars(self.anomalies, "A", reverse=True))
        self.assertEqual(bars["encoding"]["color"]["condition"]["value"], charts.COLD)
        self.assertEqual(flipped["encoding"]["color"]["condition"]["value"], charts.WARM)
        self.spec(charts.seasonal_bars(analysis.seasonal_cycle(self.monthly), "S"))
        summary = analysis.annual_summary(self.daily)
        self.spec(charts.annual_extremes(summary, "E"))
        yearly = self.anomalies.groupby("year", as_index=False)["anomaly"].mean()
        lines = yearly.rename(columns={"anomaly": "value"}).assign(station="A")
        self.spec(charts.multi_line(lines, "station", "T", ["A"]))
        self.spec(charts.simple_bars(yearly, "year", "anomaly", "A"))

    def test_trend_caption(self):
        caption = charts.trend_caption(analysis.Trend(0.05, 0.0, 0.5, 10), "°C")
        self.assertIn("+0.500 °C/10年", caption)
        self.assertIn("n = 10", caption)

import unittest

from antarctic_viz import analysis, charts, parsers
from tests.helpers import edc_text, gml_text, ice_core_co2_text, reader_text, sea_ice_text


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

    def test_break_gaps_inserts_null_inside_outages_only(self):
        gappy = self.monthly[~self.monthly["date"].dt.year.between(1980, 1983)]
        broken = charts.break_gaps(gappy)
        self.assertEqual(len(broken), len(gappy) + 1)
        filler = broken[broken["value"].isna()]["date"].iloc[0]
        self.assertTrue(1980 <= filler.year <= 1983)
        self.assertIs(charts.break_gaps(self.monthly), self.monthly)
        short = self.monthly.head(2)
        self.assertIs(charts.break_gaps(short), short)

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


class TestIceCoreCharts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.co2 = parsers.parse_ice_core_co2(ice_core_co2_text())
        cls.temperature = parsers.parse_edc_temperature(edc_text())

    def test_paleo_co2_reference_line_is_optional(self):
        self.assertEqual(len(charts.paleo_co2(self.co2).to_dict()["layer"]), 1)
        spec = charts.paleo_co2(self.co2, modern=424.0).to_dict()
        self.assertEqual(len(spec["layer"]), 3)
        self.assertIn("現在 424 ppm", str(spec))

    def test_paleo_axes_run_past_to_present(self):
        spec = charts.paleo_temperature(self.temperature).to_dict()
        self.assertTrue(spec["encoding"]["x"]["scale"]["reverse"])

    def test_recent_co2_joins_instrumental_after_since_year(self):
        instrumental = analysis.instrumental_as_age(parsers.parse_gml_monthly(gml_text(1976, 1980)))
        spec = charts.recent_co2(self.co2, instrumental, since_year=1000).to_dict()
        rows = next(iter(spec["datasets"].values()))
        self.assertEqual({r["source"] for r in rows}, {"アイスコア", "南極点 直接観測"})
        self.assertGreaterEqual(min(r["year"] for r in rows), 1000)
        ice_only = charts.recent_co2(self.co2, None, since_year=0).to_dict()
        rows = next(iter(ice_only["datasets"].values()))
        self.assertEqual({r["source"] for r in rows}, {"アイスコア"})

    def test_scatter_encodes_co2_against_temperature(self):
        pairs = analysis.paired_on_ages(self.co2, self.temperature)
        spec = charts.co2_temperature_scatter(pairs).to_dict()
        self.assertEqual(spec["encoding"]["x"]["field"], "co2")
        self.assertEqual(spec["encoding"]["y"]["field"], "temperature")

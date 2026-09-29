import unittest
from datetime import date
from pathlib import Path
from unittest import mock

import streamlit as st
from streamlit.testing.v1 import AppTest

from antarctic_viz import sources
from tests.helpers import gml_text, reader_text, sea_ice_text

APP = str(Path(sources.__file__).with_name("app.py"))
TEXTS = {
    sources.SEA_ICE_EXTENT.url: sea_ice_text(1979, date(2025, 9, 15)),
    sources.SOUTH_POLE_CO2.url: gml_text(1976, 2024),
    sources.reader_temperature("Syowa").url: reader_text(1957, 2024),
    sources.reader_temperature("Vostok").url: reader_text(1958, 2024, offset=-45),
    sources.reader_temperature("Halley").url: reader_text(1995, 2024),
}


def fake_fetch(texts):
    def fetch(url, **kwargs):
        if url not in texts:
            raise sources.FetchError(f"offline: {url}")
        return texts[url]

    return fetch


class AppCase(unittest.TestCase):
    texts = TEXTS

    def setUp(self):
        st.cache_data.clear()
        patcher = mock.patch("antarctic_viz.sources.fetch_text", side_effect=fake_fetch(self.texts))
        self.fetch = patcher.start()
        self.addCleanup(patcher.stop)
        self.at = AppTest.from_file(APP, default_timeout=60)

    def run_page(self, page, base=None):
        self.at.run()
        if base is not None:
            self.at.sidebar.slider[0].set_value(base)
        self.at.sidebar.radio[0].set_value(page)
        self.at.run()
        self.assertEqual(len(self.at.exception), 0, [e.value for e in self.at.exception])
        return self.at

    def metrics(self):
        return {m.label: m.value for m in self.at.metric}


class TestPagesWithData(AppCase):
    def test_overview_shows_latest_values(self):
        self.run_page("概要")
        metrics = self.metrics()
        self.assertIn("海氷面積 (2025-09-15)", metrics)
        self.assertIn("南極点 CO₂ (2024-06)", metrics)
        self.assertEqual(metrics["昭和基地 月平均気温 (2024-06)"], "-4.2 °C")
        self.assertEqual(len(self.at.error), 0)

    def test_sea_ice_page(self):
        self.run_page("海氷面積")
        metrics = self.metrics()
        self.assertEqual(metrics["同日の順位 (小さい順)"], "1 / 47 年")
        self.assertIn("平年 (同日中央値) との差", metrics)
        self.assertEqual(self.at.multiselect[0].value, [2025, 2024, 2023, 2014])
        self.assertTrue(any("年最小" in c.value for c in self.at.caption))

    def test_sea_ice_page_on_feb_29_skips_normal_comparison(self):
        self.texts = dict(TEXTS)
        self.texts[sources.SEA_ICE_EXTENT.url] = sea_ice_text(1979, date(2024, 2, 29))
        self.fetch.side_effect = fake_fetch(self.texts)
        self.run_page("海氷面積")
        self.assertNotIn("平年 (同日中央値) との差", self.metrics())

    def test_co2_page(self):
        self.run_page("南極点 CO₂")
        metrics = self.metrics()
        self.assertEqual(metrics["2023年の年増加量"], "+1.80 ppm/年")
        self.assertTrue(any("ppm/10年" in c.value for c in self.at.caption))

    def test_temperature_page_and_station_comparison(self):
        at = self.run_page("基地の気温")
        self.assertEqual(self.metrics()["年平均気温のトレンド"], "+0.20 °C/10年")
        at.selectbox[0].set_value("Vostok").run()
        self.assertEqual(at.multiselect[0].value, ["Vostok"])
        at.multiselect[0].set_value(["Vostok", "Syowa", "Mawson"]).run()
        self.assertEqual(len(at.exception), 0)
        self.assertTrue(any("Mawson" in e.value for e in at.error))

    def test_sources_page_renders_research_notes(self):
        self.run_page("データソース")
        self.assertIn("南極観測の公開データ", self.at.markdown[0].value)

    def test_refresh_button_bypasses_cache(self):
        self.run_page("概要")
        self.at.sidebar.button[0].click().run()
        max_ages = {call.kwargs["max_age"] for call in self.fetch.call_args_list}
        self.assertEqual(max_ages, {0, sources.DEFAULT_MAX_AGE})


class TestBasePeriodOutsideData(AppCase):
    def test_sea_ice_warns_without_base_period(self):
        self.run_page("海氷面積", base=(1957, 1960))
        self.assertGreaterEqual(len(self.at.warning), 2)
        self.assertNotIn("平年 (同日中央値) との差", self.metrics())

    def test_temperature_comparison_skips_station_without_base(self):
        at = self.run_page("基地の気温", base=(1960, 1990))
        at.multiselect[0].set_value(["Syowa", "Halley"]).run()
        self.assertTrue(any("1960–1990" in w.value for w in at.warning))


class TestOffline(AppCase):
    texts = {}

    def test_every_data_page_reports_the_failure(self):
        for page in ("概要", "海氷面積", "南極点 CO₂", "基地の気温"):
            with self.subTest(page=page):
                self.run_page(page)
                self.assertGreater(len(self.at.error), 0)
                self.assertEqual(len(self.at.metric), 0)


class TestShortRecords(AppCase):
    texts = {
        sources.reader_temperature("Syowa").url: "Year Jan\n2024 -1.0 -2.0\n",
        sources.SOUTH_POLE_CO2.url: gml_text(2024, 2025, last_month=6),
    }

    def test_single_year_has_no_temperature_trend(self):
        self.run_page("基地の気温")
        self.assertNotIn("年平均気温のトレンド", self.metrics())

    def test_single_complete_year_has_no_co2_growth(self):
        self.run_page("南極点 CO₂")
        self.assertEqual(list(self.metrics()), ["最新値 (2025-06)"])


class TestUpload(AppCase):
    def upload(self, content: bytes):
        at = self.run_page("CSVを分析")
        self.assertEqual(len(at.file_uploader), 1)
        at.file_uploader[0].upload("data.csv", content, "text/csv").run()
        self.assertEqual(len(at.exception), 0, [e.value for e in at.exception])
        return at

    def test_no_file_shows_only_the_uploader(self):
        at = self.run_page("CSVを分析")
        self.assertEqual(len(at.selectbox), 0)

    def test_monthly_csv_gets_trend_and_anomalies(self):
        rows = ["date,temp"] + [
            f"{y}-{m:02d}-01,{-10 + m * 0.5 + (y - 1980) * 0.1}"
            for y in range(1980, 1995)
            for m in range(1, 13)
        ]
        at = self.upload("\n".join(rows).encode())
        at.text_input[0].set_value("°C").run()
        self.assertTrue(any("°C/10年" in c.value for c in at.caption))
        self.assertGreater(len(at.get("vega_lite_chart")), 1)

    def test_single_row_has_no_trend(self):
        at = self.upload(b"date,v\n2020-01-01,1\n")
        self.assertFalse(any("トレンド" in c.value for c in at.caption))

    def test_unusable_columns_report_error(self):
        at = self.upload(b"a,b\nfoo,bar\nbaz,qux\n")
        self.assertTrue(any("有効な行" in e.value for e in at.error))

    def test_unparseable_file_reports_error(self):
        at = self.upload(b"")
        self.assertTrue(any("CSVを読み込めません" in e.value for e in at.error))

import json
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

import streamlit as st
from streamlit.testing.v1 import AppTest

from antarctic_viz import sources
from tests.helpers import (
    FIXTURES,
    edc_text,
    gml_text,
    ice_core_co2_text,
    ozone_annual_text,
    ozone_daily_text,
    reader_text,
    sea_ice_text,
)

APP = str(Path(sources.__file__).with_name("app.py"))
THIS_YEAR = date.today().year
TEXTS = {
    sources.SEA_ICE_EXTENT.url: sea_ice_text(1979, date(2025, 9, 15)),
    sources.SOUTH_POLE_CO2.url: gml_text(1976, 2024),
    sources.SOUTH_POLE_CH4.url: gml_text(1984, 2024).replace(" ...", "").replace("qcflag", ""),
    sources.SYOWA_CO2.url: gml_text(1986, 2024).replace(" ...", "").replace("qcflag", ""),
    sources.SYOWA_CH4.url: gml_text(1986, 2024).replace(" ...", "").replace("qcflag", ""),
    sources.OZONE_HOLE_ANNUAL.url: ozone_annual_text(1979, 2025),
    sources.ozone_hole_daily(THIS_YEAR).url: ozone_daily_text(THIS_YEAR, date(THIS_YEAR, 9, 26)),
    sources.ozone_hole_daily(1995).url: ozone_daily_text(1995, date(1994, 12, 31)),
    sources.reader_series("Syowa", "wind_speed").url: reader_text(1957, 2024, offset=30),
    sources.reader_series("Vostok", "pressure").url: reader_text(1958, 2024, offset=640),
    sources.reader_temperature("Syowa").url: reader_text(1957, 2024),
    sources.reader_temperature("Vostok").url: reader_text(1958, 2024, offset=-45),
    sources.reader_temperature("Halley").url: reader_text(1995, 2024),
    sources.ICE_CORE_CO2.url: ice_core_co2_text(),
    sources.EDC_TEMPERATURE.url: edc_text(),
}
REPORT_INDEX = " ".join(f"ant{m}.html" for m in ("201007", "201008", "201009", "201010", "202602"))
REPORT_TEXTS = {
    sources.JMA_REPORT_INDEX_URL: REPORT_INDEX,
    sources.jma_report_url(2010, 7): (FIXTURES / "jma_report_201007.html").read_text("utf-8"),
    # 2010-08 is missing (HTTP error), 2010-09 has no statistics, 2010-10 has no summary.
    sources.jma_report_url(2010, 9): "<h2>概況</h2><p>カタバ風で晴れた。</p>",
    sources.jma_report_url(2010, 10): "<h2>その他</h2><p>x</p>",
    sources.jma_report_url(2026, 2): (FIXTURES / "jma_report_202602.html").read_text("utf-8-sig"),
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
        # Never let the developer's real cache decide whether reports count as downloaded.
        fresh = mock.patch("antarctic_viz.sources.is_fresh", return_value=False)
        self.is_fresh = fresh.start()
        self.addCleanup(fresh.stop)
        pace = mock.patch("antarctic_viz.sources.REQUEST_INTERVAL", 0)
        pace.start()
        self.addCleanup(pace.stop)
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
        self.assertIn("南極点 CH₄ (2024-06)", metrics)
        self.assertIn("昭和基地 CO₂ (2024-06)", metrics)
        self.assertEqual(metrics["オゾンホール面積 (2025年)"], "23.1 百万km²")
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
        self.run_page("温室効果ガス")
        metrics = self.metrics()
        self.assertEqual(metrics["2023年の年増加量"], "+1.80 ppm/年")
        self.assertTrue(any("ppm/10年" in c.value for c in self.at.caption))

    def test_syowa_station_and_comparison(self):
        at = self.run_page("温室効果ガス")
        self.assertIn("観測所の比較 (CO₂ 年平均)", [h.value for h in at.subheader])
        self.assertTrue(any("(昭和基地 − 南極点) は平均" in c.value for c in at.caption))
        at.main.radio[0].set_value("昭和基地").run()
        at.main.radio[1].set_value("CH₄").run()
        self.assertEqual(len(at.exception), 0)
        self.assertIn("昭和基地 大気メタン", at.subheader[0].value)
        self.assertIn("観測所の比較 (CH₄ 年平均)", [h.value for h in at.subheader])
        self.assertEqual(len(at.info), 0)

    def test_methane_page(self):
        at = self.run_page("温室効果ガス")
        at.main.radio[1].set_value("CH₄").run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(self.metrics()["2023年の年増加量"], "+1.80 ppb/年")
        self.assertIn("メタン", at.subheader[0].value)

    def test_ozone_page(self):
        at = self.run_page("オゾンホール")
        metrics = self.metrics()
        self.assertEqual(metrics["2025年の面積"], "23.1 百万km²")
        self.assertEqual(metrics["2025年の最低オゾン全量"], "128 DU")
        self.assertEqual(metrics["観測史上最大 (2004年)"], "25.0 百万km²")
        self.assertIn(f"最新値 ({THIS_YEAR}-09-26)", metrics)
        self.assertEqual(at.selectbox[0].value, THIS_YEAR)
        self.assertEqual(len(at.error), 0)

    def test_ozone_year_without_observations(self):
        at = self.run_page("オゾンホール")
        at.selectbox[0].set_value(1995).run()
        self.assertTrue(any("1995年の日別データはありません" in i.value for i in at.info))

    def test_ozone_year_that_cannot_be_fetched(self):
        at = self.run_page("オゾンホール")
        at.selectbox[0].set_value(2000).run()
        self.assertEqual(len(at.exception), 0)
        self.assertTrue(any("2000年" in e.value for e in at.error))
        self.assertIn("2025年の面積", self.metrics())

    def test_ice_core_page(self):
        self.run_page("アイスコア")
        metrics = self.metrics()
        self.assertEqual(metrics["自然の変動幅 (1750年以前)"], "185〜285 ppm")
        self.assertEqual(metrics["産業革命前 (1000〜1750年の平均)"], "280 ppm")
        self.assertIn("南極点 直接観測 (2024-06)", metrics)
        self.assertIn("相関係数 r", metrics)
        self.assertEqual(len(self.at.tabs), 3)
        self.assertEqual(len(self.at.error), 0)

    def test_temperature_page_and_station_comparison(self):
        at = self.run_page("基地の気象")
        self.assertEqual(self.metrics()["年平均気温のトレンド"], "+0.20 °C/10年")
        at.selectbox[0].set_value("Vostok").run()
        self.assertEqual(at.multiselect[0].value, ["Vostok"])
        at.multiselect[0].set_value(["Vostok", "Syowa", "Mawson"]).run()
        self.assertEqual(len(at.exception), 0)
        self.assertTrue(any("Mawson" in e.value for e in at.error))

    def test_station_wind_and_pressure(self):
        at = self.run_page("基地の気象")
        at.main.radio[0].set_value("wind_speed").run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(self.metrics()["年平均風速のトレンド"], "+0.10 m/s/10年")
        at.selectbox[0].set_value("Vostok").run()
        at.main.radio[0].set_value("pressure").run()
        self.assertEqual(self.metrics()["年平均気圧のトレンド"], "+0.20 hPa/10年")
        self.assertTrue(any("hPa/10年" in c.value for c in at.caption))

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
        at = self.run_page("基地の気象", base=(1960, 1990))
        at.multiselect[0].set_value(["Syowa", "Halley"]).run()
        self.assertTrue(any("1960–1990" in w.value for w in at.warning))


class TestOffline(AppCase):
    texts = {}

    def test_every_data_page_reports_the_failure(self):
        for page in (
            "概要",
            "海氷面積",
            "温室効果ガス",
            "オゾンホール",
            "アイスコア",
            "基地の気象",
            "昭和基地の月報",
        ):
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
        self.run_page("基地の気象")
        self.assertNotIn("年平均気温のトレンド", self.metrics())

    def test_single_complete_year_has_no_co2_growth(self):
        self.run_page("温室効果ガス")
        self.assertEqual(list(self.metrics()), ["最新値 (2025-06)"])
        self.assertTrue(any("比較に必要なデータ" in i.value for i in self.at.info))


class TestOzoneWithoutMinimum(AppCase):
    texts = {sources.OZONE_HOLE_ANNUAL.url: "1990 18.0 -9999.0\n1991 19.0 -9999.0\n"}

    def test_area_only_skips_minimum_metric_and_daily_fails_softly(self):
        self.run_page("オゾンホール")
        metrics = self.metrics()
        self.assertEqual(metrics["1991年の面積"], "19.0 百万km²")
        self.assertFalse(any("最低オゾン全量" in label for label in metrics))
        self.assertEqual(len(self.at.error), 1)


class TestStationsWithoutOverlap(AppCase):
    texts = {
        sources.SOUTH_POLE_CO2.url: gml_text(1976, 1980),
        sources.SYOWA_CO2.url: gml_text(1990, 1995),
    }

    def test_comparison_without_common_years_has_no_difference_note(self):
        self.run_page("温室効果ガス")
        self.assertIn("観測所の比較 (CO₂ 年平均)", [h.value for h in self.at.subheader])
        self.assertFalse(any("は平均" in c.value for c in self.at.caption))


class TestIceCoreWithoutCompanions(AppCase):
    texts = {sources.ICE_CORE_CO2.url: ice_core_co2_text()}

    def test_co2_alone_still_renders(self):
        self.run_page("アイスコア")
        metrics = self.metrics()
        self.assertIn("自然の変動幅 (1750年以前)", metrics)
        self.assertFalse(any(label.startswith("南極点") for label in metrics))
        self.assertNotIn("相関係数 r", metrics)
        captions = [c.value for c in self.at.caption]
        self.assertTrue(any("南極点の直接観測を取得できなかった" in c for c in captions))
        self.assertTrue(any("気温データを取得できなかった" in i.value for i in self.at.info))


class TestIceCoreModernOnly(AppCase):
    texts = {
        sources.ICE_CORE_CO2.url: "-51\t368\n-20\t340\n",
        sources.EDC_TEMPERATURE.url: "1 0 -50 -400 0.1\n2 0.5 -45 -401 0.2\n",
    }

    def test_no_preindustrial_mean_or_correlation_without_overlap(self):
        self.run_page("アイスコア")
        metrics = self.metrics()
        self.assertNotIn("産業革命前 (1000〜1750年の平均)", metrics)
        self.assertNotIn("相関係数 r", metrics)


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

    def test_jma_download_is_analysed(self):
        at = self.upload((FIXTURES / "jma_syowa_monthly.csv").read_bytes())
        self.assertEqual(at.selectbox[0].value, "年月")
        self.assertEqual(at.selectbox[1].value, "平均気温(℃)")
        self.assertEqual(at.text_input[0].value, "℃")
        self.assertTrue(any("℃/10年" in c.value for c in at.caption))
        self.assertEqual(len(at.error), 0)
        self.assertGreater(len(at.get("vega_lite_chart")), 0)

    def test_single_row_has_no_trend(self):
        at = self.upload(b"date,v\n2020-01-01,1\n")
        self.assertFalse(any("トレンド" in c.value for c in at.caption))

    def test_unusable_columns_report_error(self):
        at = self.upload(b"a,b\nfoo,bar\nbaz,qux\n")
        self.assertTrue(any("有効な行" in e.value for e in at.error))

    def test_unparseable_file_reports_error(self):
        at = self.upload(b"")
        self.assertTrue(any("CSVを読み込めません" in e.value for e in at.error))


class TestReports(AppCase):
    texts = {**TEXTS, **REPORT_TEXTS}

    def corpus_page(self):
        at = self.run_page("昭和基地の月報")
        next(b for b in at.button if b.label == "全期間の月報を取得").click().run()
        self.assertEqual(len(at.exception), 0, [e.value for e in at.exception])
        return at

    def test_month_view_shows_summary_and_numbers(self):
        at = self.run_page("昭和基地の月報")
        metrics = {m.label: m for m in at.metric}
        self.assertEqual(metrics["月平均気温"].value, "-2.8 °C")
        self.assertIn("(平年差)", metrics["月平均気温"].delta)
        self.assertIn("概況の表現: 平年並", metrics["月平均気温"].help)
        self.assertIn("平年値の期間での区分", metrics["月平均風速"].help)
        self.assertFalse(metrics["月平均気圧"].help)
        self.assertTrue(any("ブリザードは0回" in m.value for m in at.markdown))
        self.assertTrue(any("1991–2020年" in c.value for c in at.caption))
        self.assertTrue(any("未取得の5か月分" in i.value for i in at.info))
        self.assertEqual(
            sum("全期間の月報を取得すると" in i.value for i in at.info), 3, "three corpus tabs"
        )
        self.assertEqual(
            self.fetch.call_count, len(set(c.args[0] for c in self.fetch.call_args_list))
        )

    def test_month_view_older_and_failing_months(self):
        at = self.run_page("昭和基地の月報")
        at.selectbox(key="report_year").set_value(2010).run()
        self.assertEqual(at.selectbox(key="report_month").value, 10)
        self.assertTrue(any("2010年10月の月報を読み込めませんでした" in e.value for e in at.error))
        at.selectbox(key="report_month").set_value(9).run()
        self.assertEqual(len(at.metric), 0)
        at.selectbox(key="report_month").set_value(7).run()
        self.assertEqual(len(at.exception), 0)
        self.assertIn("旬別の天候経過", [e.label for e in at.expander])
        self.assertTrue(any("1971–2000年" in c.value for c in at.caption))

    def test_corpus_tabs_after_download(self):
        at = self.corpus_page()
        captions = [c.value for c in at.caption]
        self.assertTrue(any("2010年8月、2010年10月" in c for c in captions))
        self.texts = {**self.texts, sources.jma_report_url(2010, 8): "<h2>概況</h2><p>晴れ。</p>"}
        self.fetch.side_effect = fake_fetch(self.texts)
        next(b for b in at.button if b.label == "取得できなかった月を再取得").click().run()
        self.assertEqual(len(at.exception), 0, [e.value for e in at.exception])
        self.assertTrue(any(c.value.endswith(": 2010年10月") for c in at.caption))
        metrics = self.metrics()
        self.assertEqual(metrics["収録した月"], "4 か月")
        self.assertEqual(metrics["ブリザードの記述がある月"], "1 か月")
        self.assertEqual(metrics["回数が書かれている月"], "2 か月")
        self.assertEqual(metrics["該当する月"], "2 / 4 か月")
        self.assertEqual(metrics["比べた月"], "2 か月")
        self.assertEqual(at.session_state["reports_requested"], True)
        at.text_input[0].set_value("オーロラ").run()
        self.assertTrue(any("該当する文はありませんでした" in i.value for i in at.info))
        at.radio(key="expression_element").set_value("風速").run()
        self.assertEqual(self.metrics()["比べた月"], "1 か月")
        self.assertEqual(len(at.exception), 0)

    def test_cached_corpus_needs_no_button(self):
        self.is_fresh.return_value = True
        at = self.run_page("昭和基地の月報")
        self.assertFalse(any(b.label == "全期間の月報を取得" for b in at.button))
        self.assertIn("収録した月", self.metrics())

    def test_station_page_offers_the_report(self):
        at = self.run_page("基地の気象")
        self.assertIn("気象庁の月報で確認する", [h.value for h in at.subheader])
        self.assertTrue(any("「昭和基地の月報」ページで全期間" in c.value for c in at.caption))
        self.assertEqual(self.metrics()["月平均気温"], "-2.8 °C")
        at.selectbox[0].set_value("Vostok").run()
        self.assertNotIn("気象庁の月報で確認する", [h.value for h in at.subheader])

    def test_station_heatmap_gets_notes_once_reports_are_cached(self):
        self.is_fresh.return_value = True
        at = self.run_page("基地の気象")
        self.assertTrue(any("セルにマウスを乗せると、その月" in c.value for c in at.caption))
        specs = [json.loads(chart.proto.spec) for chart in at.get("vega_lite_chart")]
        heatmap = next(spec for spec in specs if spec.get("mark", {}).get("type") == "rect")
        self.assertEqual(heatmap["encoding"]["tooltip"][-1]["title"], "概況")


class TestReportsWithoutReader(AppCase):
    texts = REPORT_TEXTS

    def test_expressions_need_reader_and_corpus_can_be_empty(self):
        at = self.run_page("昭和基地の月報")
        next(b for b in at.button if b.label == "全期間の月報を取得").click().run()
        self.assertTrue(any("比べられる月がありませんでした" in i.value for i in at.info))
        self.assertNotIn("(平年差)", str([m.delta for m in at.metric]))


class TestReportsShortReader(AppCase):
    texts = {**REPORT_TEXTS, sources.reader_temperature("Syowa").url: reader_text(2015, 2024)}

    def test_too_few_normal_years_gives_no_class(self):
        self.run_page("昭和基地の月報")
        temp = next(m for m in self.at.metric if m.label == "月平均気温")
        self.assertIn("(平年差)", temp.delta)
        self.assertEqual(temp.help, "概況の表現: 平年並")


class TestReportIndexProblems(AppCase):
    texts = {
        sources.reader_temperature("Syowa").url: reader_text(1957, 2024),
        sources.JMA_REPORT_INDEX_URL: "<html>no links</html>",
    }

    def test_empty_index_is_reported_and_station_page_continues(self):
        at = self.run_page("昭和基地の月報")
        self.assertTrue(any("リンクが見つかりませんでした" in e.value for e in at.error))
        at = self.run_page("基地の気象")
        self.assertTrue(any("気象庁の月報を取得できませんでした" in c.value for c in at.caption))
        self.assertEqual(len(at.error), 0)


class TestReportCorpusAllFailing(AppCase):
    texts = {sources.JMA_REPORT_INDEX_URL: "ant201008.html"}

    def test_tabs_explain_when_no_report_could_be_read(self):
        at = self.run_page("昭和基地の月報")
        next(b for b in at.button if b.label == "全期間の月報を取得").click().run()
        self.assertTrue(any("2010年8月の月報を読み込めませんでした" in e.value for e in at.error))
        self.assertEqual(sum("全期間の月報を取得すると" in i.value for i in at.info), 3)


class TestReportCorpusComplete(AppCase):
    texts = {
        sources.JMA_REPORT_INDEX_URL: "ant202602.html",
        sources.jma_report_url(2026, 2): REPORT_TEXTS[sources.jma_report_url(2026, 2)],
    }

    def test_no_failure_note_when_every_month_is_read(self):
        self.is_fresh.return_value = True
        at = self.run_page("昭和基地の月報")
        self.assertEqual(self.metrics()["収録した月"], "1 か月")
        self.assertFalse(any("取得・解析できなかった月" in c.value for c in at.caption))

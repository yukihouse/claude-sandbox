"""Tests for the JMA monthly reports.

The two fixtures are real pages of 気象庁「南極の気象」 (2010年7月 with the older
ten-day layout, 2026年2月 with the current one), used under the JMA terms of use.
"""

import unittest

import pandas as pd

from antarctic_viz import parsers, reports
from tests.helpers import FIXTURES, reader_text

TEMP = reports.ELEMENTS["temperature"]
WIND = reports.ELEMENTS["wind_speed"]
PRESSURE = reports.ELEMENTS["pressure"]


def page(name: str) -> str:
    return (FIXTURES / name).read_bytes().decode("utf-8")


def report(summary: str, year: int = 2023, month: int = 5, **stats: str) -> reports.MonthlyReport:
    return reports.MonthlyReport(year, month, (summary,), (), stats)


def html(*sections: str) -> str:
    return "<html><body>" + "".join(sections) + "</body></html>"


class TestParsing(unittest.TestCase):
    def test_current_layout(self):
        r = reports.parse_report(page("jma_report_202602.html"), 2026, 2)
        self.assertEqual(r.date, pd.Timestamp(2026, 2, 1))
        self.assertEqual(len(r.summary), 6)
        self.assertEqual(r.summary[0], "2月は、低気圧の接近・通過に伴い周期的に天気が変化した。")
        self.assertNotIn("用語解説", r.summary_text)
        self.assertEqual(r.periods, ())
        self.assertEqual(r.stats["平均気温"], "-2.8°C")
        self.assertEqual(r.stats["平均気圧(海面)"], "982.1hPa")
        self.assertEqual(len(r.stats), 14)
        self.assertEqual(r.full_text, "\n".join(r.summary))

    def test_older_layout_with_ten_day_periods(self):
        r = reports.parse_report(page("jma_report_201007.html"), 2010, 7)
        self.assertEqual([label for label, _ in r.periods], ["上旬", "中旬", "下旬"])
        self.assertIn("A級ブリザード", r.periods[2][1])
        self.assertTrue(r.full_text.endswith(r.periods[2][1]))
        self.assertEqual(reports.stat_value(r, TEMP), -21.3)

    def test_markup_edge_cases(self):
        text = html(
            "<p>before any heading</p>",
            "<h2>１．概　況</h2><script>var x = 1;</script>",
            "<p class='mtx'>一文目。<br>　二文目。<br><br></p>",
            "<p class='stx'>脚注<a href='x'>リンク</a></p>",
            "<h2>２．旬別の天候経過</h2><dl><dt>上旬：</dt><dd>晴れ。</dd></dl><p>注記</p>",
            "<h2>３．統計値</h2><table><tr><th>平均気温<td>-1.0℃<th>余り</table>",
        )
        r = reports.parse_report(text, 2020, 1)
        self.assertEqual(r.summary, ("一文目。", "二文目。"))
        self.assertEqual(r.stats, {"平均気温": "-1.0°C"})
        self.assertEqual(r.periods, (("上旬", "晴れ。"),))

    def test_page_without_summary_is_a_parse_error(self):
        with self.assertRaises(parsers.ParseError):
            reports.parse_report(html("<h2>その他</h2><p>x</p>"), 2020, 1)

    def test_index_lists_valid_months_in_order(self):
        text = '<a href="ant201002.html"></a><a href="ant201001.html"></a>'
        text += "ant201001.html ant201013.html"
        self.assertEqual(reports.parse_index(text), [(2010, 1), (2010, 2)])

    def test_normalize_and_sentences(self):
        self.assertEqual(reports.normalize("　ＡＢ１\n  ２ "), "AB1 2")
        self.assertEqual(reports.sentences("一。二。 三"), ["一。", "二。", " 三"])

    def test_headline_is_shortened(self):
        self.assertEqual(reports.headline(report("短い。次。")), "短い。")
        long = reports.headline(report("あ" * 80 + "。"), limit=10)
        self.assertEqual(long, "あ" * 9 + "…")
        self.assertEqual(reports.headline(reports.MonthlyReport(2020, 1, ())), "")


class TestEvents(unittest.TestCase):
    def test_mentions_ignore_negated_blizzards(self):
        self.assertTrue(reports.mentions("A級ブリザードとなった。", "ブリザード"))
        self.assertFalse(reports.mentions("ブリザードとはならなかった。", "ブリザード"))
        self.assertFalse(reports.mentions("2月のブリザードは0回となった。", "ブリザード"))
        self.assertTrue(reports.mentions("カタバ風が吹いた。", "カタバ風"))
        self.assertFalse(reports.mentions("晴れた。", "カタバ風"))

    def test_blizzard_count(self):
        cases = {
            "晴れた。": None,
            "ブリザードは発生しなかった。": 0.0,
            "A級1回を含む4回のブリザードを記録した。": 4.0,
            "ブリザードはC級が3回あった。": 3.0,
            "B級2回、C級5回、計8回のブリザードとなった。": 8.0,
            "計3.5回(0.5回は月跨ぎ)のブリザードとなった。": 3.5,
            "中旬は計3回のブリザードとなった。下旬にもB級2回のブリザード。": None,
            "中旬にも低気圧が通過したが、2月のブリザードは0回となった。": 0.0,
            "16日はB級ブリザードとなった。": None,
            "期間の前半にブリザードを3回記録した。7月はブリザードが合計4回あった。": 4.0,
            "A級ブリザードは発生しなかったが、B級ブリザードを2回記録した。": 2.0,
            "A級ブリザードは発生しなかった。": None,
            "ブリザードはA級1回を含む4回となった。": 4.0,
            "ブリザードが3回(A級2回、B級1回)あった。": 3.0,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(reports.blizzard_count(text), expected)

    def test_period_notes_are_separate_sentences_and_not_month_counts(self):
        r = reports.MonthlyReport(
            2010, 8, ("今月はブリザードが多かった",), (("上旬", "ブリザードが2回あった。"),)
        )
        self.assertEqual(
            reports.sentences(r.full_text),
            ["今月はブリザードが多かった", "ブリザードが2回あった。"],
        )
        self.assertTrue(pd.isna(reports.event_table([r])["blizzard_count"].iloc[0]))

    def test_event_table_and_yearly_counts(self):
        corpus = [
            reports.parse_report(page("jma_report_201007.html"), 2010, 7),
            reports.parse_report(page("jma_report_202602.html"), 2026, 2),
            report("カタバ風が吹いた。", 2026, 3),
        ]
        events = reports.event_table(corpus)
        self.assertEqual(list(events["blizzard_count"].fillna(-1)), [4.0, 0.0, -1])
        self.assertEqual(list(events["ブリザード"]), [True, False, False])
        self.assertEqual(list(events["カタバ風"]), [False, True, True])
        self.assertTrue(events.loc[0, "記録・順位"])
        long = reports.yearly_event_months(events)
        self.assertEqual(len(long), 2 * len(reports.EVENTS))
        kataba = long[(long["event"] == "カタバ風") & (long["year"] == 2026)]
        self.assertEqual(int(kataba["value"].iloc[0]), 2)

    def test_search_matches_any_keyword(self):
        corpus = [report("カタバ風が吹いた。晴れた。", 2020, 1), report("蜃気楼を見た。", 2020, 2)]
        hits = reports.search(corpus, " カタバ風　蜃気楼 ")
        self.assertEqual(list(hits["sentence"]), ["カタバ風が吹いた。", "蜃気楼を見た。"])
        self.assertTrue(reports.search(corpus, "  ").empty)
        self.assertTrue(reports.search(corpus, "オーロラ").empty)


class TestExpressions(unittest.TestCase):
    def test_text_level(self):
        cases = [
            ("月平均気温は平年並だったが、2日は5位の高さとなった。", TEMP, 0),
            ("月平均気温は平年より高かった。", TEMP, 1),
            ("月平均気温は平年よりかなり低かった。", TEMP, -2),
            ("月平均気温が7月の低い方から4位となった。", TEMP, -2),
            ("月平均気温は月の低いほうから9位タイとなった。", TEMP, -1),
            ("8月の月平均気温は高い方からの8月の極値を更新した。", TEMP, 2),
            ("月平均気温は-7.0°Cとなり、4月としては4位の高さとなった。", TEMP, 2),
            ("月平均気温は-7.0°Cとなり、8位の低さとなった。", TEMP, -1),
            ("月平均気温は-9.5°Cとなり、5月として最も高くなった。", TEMP, 2),
            ("月平均風速と旬平均風速は過去最大となった。", WIND, 2),
            ("月平均風速は過去最小となった。", WIND, -2),
            ("月平均風速は平年よりかなり小さくなった。", WIND, -2),
            ("月平均風速も大きくなった。", WIND, 1),
            ("月平均海面気圧は平年よりも高く、晴れ日数も多かった。", PRESSURE, 1),
            ("月平均気温は平年より著しく高く、1位を記録した。", TEMP, 2),
            ("月平均気温は平年より2.5°C高く、2月としては過去最高となった。", TEMP, 2),
            ("月平均気温は平年より高く、晴れ日数は少なかった。", TEMP, 1),
            ("月平均気温は-20.1°Cで、最低気温は低い方から3位だったが、平年より高かった。", TEMP, 1),
            ("月平均気温、月間日照時間はいずれも平年並だった。", TEMP, 0),
        ]
        for text, element, expected in cases:
            with self.subTest(text=text):
                level, sentence = reports.text_level(text, element)
                self.assertEqual(level, expected)
                self.assertEqual(sentence, text)

    def test_text_level_stops_at_the_next_quantity(self):
        text = "月平均気温、月平均風速は平年より強かった。"
        self.assertIsNone(reports.text_level(text, TEMP))
        self.assertEqual(reports.text_level(text, WIND)[0], 1)
        self.assertIsNone(reports.text_level("気温は高かった。", TEMP))

    def test_level_labels(self):
        self.assertEqual(
            [TEMP.level_label(lv) for lv in reports.LEVELS][::2],
            ["かなり低い", "平年並", "かなり高い"],
        )
        self.assertEqual(WIND.level_label(-1), "弱い")

    def test_stat_value(self):
        self.assertEqual(reports.stat_value(report("", 平均風速="5.1m/s"), WIND), 5.1)
        self.assertIsNone(reports.stat_value(report("", 平均風速="×"), WIND))
        self.assertIsNone(reports.stat_value(report(""), WIND))

    def test_jma_normal_period(self):
        self.assertEqual(reports.jma_normal_period(2011, 4), (1971, 2000))
        self.assertEqual(reports.jma_normal_period(2011, 5), (1981, 2010))
        self.assertEqual(reports.jma_normal_period(2021, 5), (1991, 2020))

    def test_classify(self):
        normals = pd.Series(range(30), dtype=float)
        expected = {-1.0: -2, 5.0: -1, 15.0: 0, 25.0: 1, 40.0: 2}
        for value, level in expected.items():
            with self.subTest(value=value):
                self.assertEqual(reports.classify(value, normals), level)
        self.assertIsNone(reports.classify(1.0, pd.Series([1.0] * 9 + [None])))

    def test_expression_table(self):
        temperature = parsers.parse_reader_monthly(reader_text(1957, 2024))
        normals = reports.normal_values(temperature, 2023, 5)
        self.assertEqual(len(normals), 30)
        self.assertEqual(normals.index.size, normals.dropna().size)
        warm = normals.max() + 1
        corpus = [
            report("月平均気温は平年よりかなり高かった。", 2023, 5, 平均気温=f"{warm}℃"),
            report("月平均気温は平年より低かった。", 2023, 6, 平均気温=f"{warm + 30}℃"),
            report("月平均気温は平年並だった。", 2023, 7),
            report("晴れた。", 2023, 8, 平均気温="-10.0℃"),
        ]
        table = reports.expression_table(corpus, {"temperature": temperature})
        self.assertEqual(list(table["text_label"]), ["かなり高い", "低い"])
        self.assertEqual(list(table["computed_label"]), ["かなり高い", "かなり高い"])
        self.assertEqual(list(table["exact_match"]), [True, False])
        self.assertEqual(list(table["direction_match"]), [True, False])
        self.assertEqual(table["normal_period"].iloc[0], "1991–2020")
        self.assertAlmostEqual(table["anomaly"].iloc[0], warm - normals.mean())
        short = parsers.parse_reader_monthly(reader_text(2015, 2024))
        few_normals = [report("月平均気温は平年並だった。", 2023, 1, 平均気温="-1.0℃")]
        self.assertTrue(reports.expression_table(few_normals, {"temperature": short}).empty)
        empty = reports.expression_table([], {"temperature": temperature})
        self.assertTrue(empty.empty)
        self.assertIn("exact_match", empty)

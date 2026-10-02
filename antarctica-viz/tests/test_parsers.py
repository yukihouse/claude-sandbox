import unittest
from datetime import date

import pandas as pd

from antarctic_viz import parsers
from tests.helpers import (
    FIXTURES,
    edc_text,
    fixture,
    ice_core_co2_text,
    ozone_annual_text,
    ozone_daily_text,
    reader_text,
)


class TestSeaIce(unittest.TestCase):
    def test_parses_rows_and_skips_headers_malformed_and_missing(self):
        df = parsers.parse_sea_ice_daily(fixture("sea_ice_sample.csv"))
        self.assertEqual(list(df.columns), ["date", "value"])
        self.assertEqual(len(df), 3)
        self.assertEqual(df["date"].iloc[0], pd.Timestamp("1978-10-26"))
        self.assertAlmostEqual(df["value"].iloc[-1], 17.670)

    def test_empty_input_raises(self):
        with self.assertRaises(parsers.ParseError):
            parsers.parse_sea_ice_daily("Year, Month, Day, Extent\n")


class TestGml(unittest.TestCase):
    def test_parses_values_and_drops_missing_flagged_and_bad(self):
        df = parsers.parse_gml_monthly(fixture("gml_sample.txt"))
        self.assertEqual(df["date"].dt.month.tolist(), [2, 3])
        self.assertEqual(df["value"].tolist(), [328.51, 328.38])

    def test_header_line_without_data_fields_comment(self):
        text = "# comment\nsite year month value\nSPO 2000 1 370.1\nSPO 2000 2 370.4\n"
        df = parsers.parse_gml_monthly(text)
        self.assertEqual(df["value"].tolist(), [370.1, 370.4])

    def test_rows_before_any_header_are_ignored(self):
        text = "SPO 2000 1 370.1\nsite year month value\nSPO 2000 2 370.4\n"
        self.assertEqual(len(parsers.parse_gml_monthly(text)), 1)

    def test_missing_column_rows_are_skipped(self):
        text = "site year month value\nSPO 2000\nSPO 2000 2 370.4\n"
        self.assertEqual(len(parsers.parse_gml_monthly(text)), 1)

    def test_no_data_raises(self):
        with self.assertRaises(parsers.ParseError):
            parsers.parse_gml_monthly("# nothing here\n")


class TestReader(unittest.TestCase):
    def test_parses_table_with_missing_and_flagged_cells(self):
        df = parsers.parse_reader_monthly(fixture("reader_sample.txt"))
        self.assertEqual(len(df), 21)  # 9 months in 1957 + 12 in 1958
        self.assertEqual(df["date"].iloc[0], pd.Timestamp("1957-04-01"))
        march_1958 = df[df["date"] == pd.Timestamp("1958-03-01")]["value"].item()
        self.assertAlmostEqual(march_1958, -7.8)

    def test_no_data_raises(self):
        with self.assertRaises(parsers.ParseError):
            parsers.parse_reader_monthly("Year Jan Feb\n")

    def test_wind_is_converted_from_knots_to_metres_per_second(self):
        knots = parsers.parse_reader_monthly(reader_text(1990, 1991))
        wind = parsers.parse_reader_wind(reader_text(1990, 1991))
        self.assertAlmostEqual(wind["value"].iloc[0], knots["value"].iloc[0] * 0.514444)


class TestOzone(unittest.TestCase):
    def test_annual_skips_headers_and_marks_missing(self):
        text = ozone_annual_text(1979, 1981) + "1982 -9999.0 150.0\n1983 x 1.0\n"
        df = parsers.parse_ozone_annual(text)
        self.assertEqual(list(df.columns), ["date", "area", "min_ozone"])
        self.assertEqual(df["date"].dt.year.tolist(), [1979, 1980, 1981, 1982])
        self.assertEqual(df["date"].iloc[0], pd.Timestamp("1979-07-01"))
        self.assertTrue(pd.isna(df["area"].iloc[-1]))
        self.assertEqual(df["min_ozone"].iloc[-1], 150.0)

    def test_annual_empty_raises(self):
        with self.assertRaises(parsers.ParseError):
            parsers.parse_ozone_annual("Year (mil km2) (DU)\n")

    def test_daily_keeps_every_day_and_blanks_unobserved(self):
        df = parsers.parse_ozone_daily(ozone_daily_text(2024, date(2024, 9, 30)))
        self.assertEqual(len(df), 366)
        self.assertEqual(list(df.columns), ["date", *parsers.OZONE_DAILY_COLUMNS])
        self.assertEqual(df["value"].last_valid_index(), df.index[df["date"] == "2024-09-30"][0])
        self.assertTrue(df["mean"].notna().all())

    def test_daily_skips_unparseable_rows(self):
        text = "Date Data Minimum 10% 30% Mean 70% 90% Maximum\n2024-13-01 1 2 3 4 5 6 7 8\n"
        text += "2024-01-01 x 2 3 4 5 6 7 8\n2024-01-02 1 2 3 4 5 6 7 8\n"
        df = parsers.parse_ozone_daily(text)
        self.assertEqual(df["date"].tolist(), [pd.Timestamp("2024-01-02")])

    def test_daily_empty_raises(self):
        with self.assertRaises(parsers.ParseError):
            parsers.parse_ozone_daily("Name: Ozone Hole Area\n")


class TestUserTable(unittest.TestCase):
    def test_coerces_types_drops_bad_rows_and_averages_duplicates(self):
        raw = pd.DataFrame(
            {
                "time": ["2020-01-01", "2020-01-01", "not a date", "2020-02-01"],
                "v": ["1", "3", "5", "x"],
            }
        )
        df = parsers.parse_user_table(raw, "time", "v")
        self.assertEqual(len(df), 1)
        self.assertEqual(df["value"].item(), 2.0)

    def test_nothing_usable_raises(self):
        raw = pd.DataFrame({"time": ["nope"], "v": ["x"]})
        with self.assertRaises(parsers.ParseError):
            parsers.parse_user_table(raw, "time", "v")


class TestIceCore(unittest.TestCase):
    def test_co2_skips_comments_bom_and_column_header(self):
        df = parsers.parse_ice_core_co2(ice_core_co2_text())
        self.assertEqual(list(df.columns), ["age_bp", "value"])
        self.assertEqual(df["age_bp"].iloc[0], -51.0)
        self.assertTrue(df["age_bp"].is_monotonic_increasing)
        self.assertGreater(df["age_bp"].iloc[-1], 790_000)

    def test_co2_ignores_short_and_non_numeric_rows(self):
        df = parsers.parse_ice_core_co2("age co2\n100\n200\t280.5\tx\nfoo\tbar\n")
        self.assertEqual(df.to_dict("list"), {"age_bp": [200.0], "value": [280.5]})

    def test_co2_empty_raises(self):
        with self.assertRaises(parsers.ParseError):
            parsers.parse_ice_core_co2("# only comments\n")

    def test_edc_keeps_rows_missing_deuterium_and_skips_rows_missing_temperature(self):
        df = parsers.parse_edc_temperature(edc_text())
        self.assertEqual(len(df), 800)
        self.assertNotIn(-50.0, df["age_bp"].tolist())
        self.assertAlmostEqual(df["value"].iloc[0], -4.0)

    def test_edc_skips_unparseable_rows(self):
        text = "Column 1: Bag number here\n12 6.6 x -390.9 0.88\n13 7.15 46.8 -385.1 1.84\n"
        df = parsers.parse_edc_temperature(text)
        self.assertEqual(df.to_dict("list"), {"age_bp": [46.8], "value": [1.84]})

    def test_edc_empty_raises(self):
        with self.assertRaises(parsers.ParseError):
            parsers.parse_edc_temperature("Bag ztop Age Deuterium Temperature\n")


class TestReadUpload(unittest.TestCase):
    def test_plain_utf8_csv_with_bom_and_comments(self):
        raw = parsers.read_upload("\ufeff# note\ndate;v\n2020-01-01;1\n".encode())
        self.assertEqual(list(raw.columns), ["date", "v"])

    def test_undecodable_bytes_raise(self):
        with self.assertRaises(parsers.ParseError):
            parsers.read_upload(b"date,v\n\x81 ,1\n")

    def test_empty_file_raises(self):
        with self.assertRaises(parsers.ParseError):
            parsers.read_upload(b"")

    def test_jma_download_drops_header_rows_and_flag_columns(self):
        raw = parsers.read_upload((FIXTURES / "jma_syowa_monthly.csv").read_bytes())
        self.assertEqual(list(raw.columns), ["年月", "平均気温(℃)"])
        self.assertEqual(len(raw), 14)
        df = parsers.parse_user_table(raw, "年月", "平均気温(℃)")
        self.assertEqual(df["date"].iloc[0], pd.Timestamp("1981-01-01"))
        self.assertAlmostEqual(df["value"].iloc[0], -1.2)

    def test_jma_several_stations_and_repeated_elements(self):
        text = (
            "ダウンロードした時刻：2026/10/02 15:24:37\n\n"
            ",昭和,昭和,昭和,南極点,\n"
            "年月日,平均気温(℃),平均気温(℃),平均気温(℃),平均気温(℃),\n"
            ",,品質情報,均質番号,,\n"
            "2025/1/1,-1.0,8,1,-28.0\n"
        )
        raw = parsers.read_upload(text.encode("cp932"))
        self.assertEqual(
            list(raw.columns), ["年月日", "昭和 平均気温(℃)", "南極点 平均気温(℃)", "列5"]
        )
        single = text.replace("南極点", "昭和")
        raw = parsers.read_upload(single.encode("cp932"))
        self.assertEqual(list(raw.columns), ["年月日", "平均気温(℃)", "平均気温(℃)'", "列5"])

    def test_jma_without_data_rows_raises(self):
        for text in (
            "ダウンロードした時刻：x\n,昭和\n年月,平均気温\n",
            "ダウンロードした時刻：x\n2025/1,1.0\n",
        ):
            with self.subTest(text=text), self.assertRaises(parsers.ParseError):
                parsers.read_upload(text.encode("cp932"))

    def test_pangaea_text_export(self):
        raw = parsers.read_upload((FIXTURES / "pangaea_monthly.tab").read_bytes())
        self.assertEqual(list(raw.columns), ["Date/Time", "t [°C]", "δ18O H2O [‰ SMOW]"])
        self.assertEqual(len(raw), 5)
        df = parsers.parse_user_table(raw, "Date/Time", "t [°C]")
        self.assertEqual(df["date"].iloc[-1], pd.Timestamp("2007-01-01"))

    def test_pangaea_without_closing_marker_raises(self):
        with self.assertRaises(parsers.ParseError):
            parsers.read_upload(b"/* DATA DESCRIPTION:\nCitation:\tx\n")


class TestUnitFromLabel(unittest.TestCase):
    def test_unit_in_brackets_at_end(self):
        self.assertEqual(parsers.unit_from_label("平均気温(℃)"), "℃")
        self.assertEqual(parsers.unit_from_label("t [°C]"), "°C")
        self.assertEqual(parsers.unit_from_label("δ18O H2O [‰ SMOW]"), "‰ SMOW")
        self.assertEqual(parsers.unit_from_label("気圧（hPa）"), "hPa")
        self.assertEqual(parsers.unit_from_label("value"), "")

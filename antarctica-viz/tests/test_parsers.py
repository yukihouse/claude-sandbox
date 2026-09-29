import unittest

import pandas as pd

from antarctic_viz import parsers
from tests.helpers import fixture


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

import os
import tempfile
import unittest
import urllib.error
from pathlib import Path

from antarctic_viz import sources


class FakeResponse:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self.body


class TestCatalog(unittest.TestCase):
    def test_reader_temperature_builds_station_url(self):
        ds = sources.reader_temperature("Syowa")
        self.assertTrue(ds.url.endswith("/Syowa.All.temperature.txt"))
        self.assertIn("昭和基地", ds.title)

    def test_reader_temperature_rejects_unknown_station(self):
        with self.assertRaises(KeyError):
            sources.reader_temperature("Atlantis")

    def test_reader_series_picks_the_element_file(self):
        wind = sources.reader_series("Syowa", "wind_speed")
        self.assertTrue(wind.url.endswith("/Syowa.All.wind_speed.txt"))
        self.assertIn("風速", wind.title)
        self.assertTrue(
            sources.reader_series("Syowa", "pressure").url.endswith("/Syowa.All.msl_pressure.txt")
        )

    def test_plateau_stations_use_station_level_pressure(self):
        for station in ("Amundsen_Scott", "Vostok"):
            url = sources.reader_series(station, "pressure").url
            self.assertTrue(url.endswith(f"/{station}.All.station_level_pressure.txt"))

    def test_ozone_daily_builds_year_url(self):
        ds = sources.ozone_hole_daily(2024)
        self.assertIn("to3areas_2024_", ds.url)
        self.assertEqual(ds.key, "ozone_hole_daily_2024")

    def test_catalog_keys_are_unique(self):
        keys = [d.key for d in sources.CATALOG]
        self.assertEqual(len(keys), len(set(keys)))


class TestFetchText(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = Path(self.tmp.name) / "cache"
        self.calls = []

    def tearDown(self):
        self.tmp.cleanup()

    def opener(self, body=b"hello"):
        def _open(request, timeout):
            self.calls.append((request.full_url, request.get_header("User-agent"), timeout))
            return FakeResponse(body)

        return _open

    def failing(self, request, timeout):
        self.calls.append(request.full_url)
        raise urllib.error.URLError("offline")

    def test_downloads_and_writes_cache(self):
        text = sources.fetch_text("https://x/a", cache_dir=self.cache, opener=self.opener())
        self.assertEqual(text, "hello")
        self.assertEqual(self.calls[0][1], sources.USER_AGENT)
        self.assertTrue(sources.cache_path("https://x/a", self.cache).exists())

    def test_fresh_cache_skips_download(self):
        sources.fetch_text("https://x/a", cache_dir=self.cache, opener=self.opener())
        text = sources.fetch_text("https://x/a", cache_dir=self.cache, opener=self.failing)
        self.assertEqual(text, "hello")
        self.assertEqual(len(self.calls), 1)

    def test_stale_cache_is_refreshed(self):
        sources.fetch_text("https://x/a", cache_dir=self.cache, opener=self.opener())
        path = sources.cache_path("https://x/a", self.cache)
        os.utime(path, (0, 0))
        text = sources.fetch_text("https://x/a", cache_dir=self.cache, opener=self.opener(b"new"))
        self.assertEqual(text, "new")

    def test_stale_cache_is_used_when_offline(self):
        sources.fetch_text("https://x/a", cache_dir=self.cache, opener=self.opener())
        text = sources.fetch_text(
            "https://x/a", cache_dir=self.cache, opener=self.failing, max_age=0
        )
        self.assertEqual(text, "hello")

    def test_server_error_without_cache_names_the_provider(self):
        def unavailable(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 503, "Service Unavailable", {}, None)

        with self.assertRaises(sources.FetchError) as ctx:
            sources.fetch_text("https://x/c", cache_dir=self.cache, opener=unavailable)
        self.assertIn("HTTP 503", str(ctx.exception))
        self.assertIn("提供元", str(ctx.exception))

    def test_offline_without_cache_raises_fetch_error(self):
        with self.assertRaises(sources.FetchError):
            sources.fetch_text("https://x/b", cache_dir=self.cache, opener=self.failing)

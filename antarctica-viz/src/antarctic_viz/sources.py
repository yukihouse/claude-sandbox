"""Catalog of public Antarctic datasets and a small caching downloader."""

from __future__ import annotations

import hashlib
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CACHE_DIR = Path.home() / ".cache" / "antarctic-viz"
DEFAULT_MAX_AGE = 24 * 60 * 60
USER_AGENT = "antarctic-viz/0.1 (+https://github.com/yukihouse/claude-sandbox)"


@dataclass(frozen=True)
class Dataset:
    key: str
    title: str
    provider: str
    url: str
    homepage: str
    description: str
    citation: str


SEA_ICE_EXTENT = Dataset(
    key="sea_ice",
    title="南極海 海氷面積 (日別)",
    provider="NSIDC / NOAA",
    url="https://noaadata.apps.nsidc.org/NOAA/G02135/south/daily/data/S_seaice_extent_daily_v4.0.csv",
    homepage="https://nsidc.org/data/g02135",
    description=(
        "衛星パッシブマイクロ波観測による南半球の海氷面積 (密接度15%以上の領域)。"
        "1978年10月から現在まで、単位は百万 km²。"
    ),
    citation="Fetterer, F. et al. Sea Ice Index (G02135). NSIDC.",
)

SOUTH_POLE_CO2 = Dataset(
    key="spo_co2",
    title="南極点 大気CO₂濃度 (月別)",
    provider="NOAA Global Monitoring Laboratory",
    url=(
        "https://gml.noaa.gov/aftp/data/trace_gases/co2/in-situ/surface/txt/"
        "co2_spo_surface-insitu_1_ccgg_MonthlyData.txt"
    ),
    homepage="https://gml.noaa.gov/dv/site/?stacode=SPO",
    description="南極点観測所 (SPO) での現場連続観測による大気中CO₂のモル分率 (ppm)。",
    citation="NOAA GML Carbon Cycle Greenhouse Gases group, South Pole in-situ CO2.",
)

READER_URL_TEMPLATE = "https://legacy.bas.ac.uk/met/READER/surface/{station}.All.temperature.txt"

# READER file-name stem -> display label. Syowa first: it is the default station.
READER_STATIONS: dict[str, str] = {
    "Syowa": "昭和基地 (日本)",
    "Amundsen_Scott": "アムンゼン・スコット南極点基地 (米国)",
    "Vostok": "ボストーク基地 (ロシア)",
    "McMurdo": "マクマード基地 (米国)",
    "Scott_Base": "スコット基地 (NZ)",
    "Mawson": "モーソン基地 (豪州)",
    "Davis": "デービス基地 (豪州)",
    "Casey": "ケーシー基地 (豪州)",
    "Mirny": "ミールヌイ基地 (ロシア)",
    "Novolazarevskaya": "ノボラザレフスカヤ基地 (ロシア)",
    "Neumayer": "ノイマイヤー基地 (ドイツ)",
    "Halley": "ハレー基地 (英国)",
    "Rothera": "ロゼラ基地 (英国)",
    "Faraday": "ファラデー/ベルナツキー基地 (英国→ウクライナ)",
    "Dumont_Durville": "デュモン・デュルヴィル基地 (フランス)",
    "Bellingshausen": "ベリングスハウゼン基地 (ロシア)",
}


def reader_temperature(station: str) -> Dataset:
    """Monthly mean surface air temperature for a SCAR READER station."""
    if station not in READER_STATIONS:
        raise KeyError(f"unknown READER station: {station}")
    return Dataset(
        key=f"reader_{station}",
        title=f"{READER_STATIONS[station]} 月平均気温",
        provider="SCAR READER / British Antarctic Survey",
        url=READER_URL_TEMPLATE.format(station=station),
        homepage="https://legacy.bas.ac.uk/met/READER/",
        description="有人観測基地の地上気象観測から作成された月平均気温 (°C)。",
        citation=("Turner, J. et al. (2004) The SCAR READER project, J. Climate 17, 2890-2898."),
    )


CATALOG: tuple[Dataset, ...] = (
    SEA_ICE_EXTENT,
    SOUTH_POLE_CO2,
    reader_temperature("Syowa"),
)


class FetchError(RuntimeError):
    """Raised when a dataset can be neither downloaded nor read from cache."""


Opener = Callable[..., object]


def cache_path(url: str, cache_dir: Path) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return cache_dir / f"{digest}.txt"


def fetch_text(
    url: str,
    *,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    max_age: float = DEFAULT_MAX_AGE,
    opener: Opener = urllib.request.urlopen,
    now: Callable[[], float] = time.time,
    timeout: float = 30,
) -> str:
    """Return the body of ``url``, using an on-disk cache younger than ``max_age``.

    If the download fails, a stale cache entry is returned instead so the UI keeps
    working offline; only when there is no cache at all is ``FetchError`` raised.
    """
    path = cache_path(url, cache_dir)
    if path.exists() and now() - path.stat().st_mtime < max_age:
        return path.read_text(encoding="utf-8")

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with opener(request, timeout=timeout) as response:
            text = response.read().decode("utf-8", errors="replace")
    except OSError as exc:  # URLError and timeouts are OSErrors
        if path.exists():
            return path.read_text(encoding="utf-8")
        raise FetchError(f"{url} を取得できませんでした: {exc}") from exc

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return text

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

SOUTH_POLE_CH4 = Dataset(
    key="spo_ch4",
    title="南極点 大気メタン濃度 (月別)",
    provider="NOAA Global Monitoring Laboratory",
    url=(
        "https://gml.noaa.gov/aftp/data/trace_gases/ch4/flask/surface/txt/"
        "ch4_spo_surface-flask_1_ccgg_month.txt"
    ),
    homepage="https://gml.noaa.gov/dv/site/?stacode=SPO",
    description=(
        "南極点観測所 (SPO) でのフラスコ採取による大気中メタン (CH₄) のモル分率 (ppb)。1983年から。"
    ),
    citation="NOAA GML Carbon Cycle Greenhouse Gases group, South Pole flask CH4.",
)

ICE_CORE_CO2 = Dataset(
    key="ice_core_co2",
    title="アイスコア 大気CO₂濃度 (過去80万年)",
    provider="NOAA NCEI Paleoclimatology",
    url="https://www.ncei.noaa.gov/pub/data/paleo/icecore/antarctica/antarctica2015co2composite.txt",
    homepage="https://www.ncei.noaa.gov/access/paleo-search/study/17975",
    description=(
        "EPICA Dome C・ボストーク・ロードームなど南極の複数のアイスコアの気泡から復元した"
        "大気CO₂濃度 (ppm) の合成記録。約80万年前から2001年まで。"
    ),
    citation=(
        "Bereiter, B. et al. (2015) Revision of the EPICA Dome C CO2 record from 800 to "
        "600 kyr before present, Geophys. Res. Lett. 42, 542-549."
    ),
)

EDC_TEMPERATURE = Dataset(
    key="edc_temperature",
    title="EPICA Dome C 気温偏差 (過去80万年)",
    provider="NOAA NCEI Paleoclimatology",
    url="https://www.ncei.noaa.gov/pub/data/paleo/icecore/antarctica/epica_domec/edc3deuttemp2007.txt",
    homepage="https://www.ncei.noaa.gov/access/paleo-search/study/6080",
    description=(
        "EPICA Dome C アイスコアの水素同位体比 (δD) から推定した南極の気温。"
        "過去1000年平均からの差 (°C)、年代はEDC3。"
    ),
    citation=(
        "Jouzel, J. et al. (2007) Orbital and Millennial Antarctic Climate Variability over "
        "the Past 800,000 Years, Science 317, 793-797."
    ),
)

READER_URL_TEMPLATE = "https://legacy.bas.ac.uk/met/READER/surface/{station}.All.{element}.txt"

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


@dataclass(frozen=True)
class ReaderElement:
    label: str
    unit: str
    description: str


READER_ELEMENTS: dict[str, ReaderElement] = {
    "temperature": ReaderElement(
        "気温", "°C", "有人観測基地の地上気象観測から作成された月平均気温 (°C)。"
    ),
    "pressure": ReaderElement(
        "気圧",
        "hPa",
        "有人観測基地の地上気象観測から作成された月平均の海面気圧 (hPa)。"
        "高原上の基地 (南極点・ボストーク) は海面更正できないため現地気圧です。",
    ),
    "wind_speed": ReaderElement(
        "風速",
        "m/s",
        "有人観測基地の地上気象観測から作成された月平均風速。"
        "READERの値 (ノット) を m/s に換算しています。",
    ),
}

# The high-plateau stations publish only station-level pressure, no sea-level reduction.
READER_STATION_LEVEL_ONLY = frozenset({"Amundsen_Scott", "Vostok"})


def reader_series(station: str, element: str = "temperature") -> Dataset:
    """Monthly mean of one surface element (see ``READER_ELEMENTS``) at a READER station."""
    if station not in READER_STATIONS:
        raise KeyError(f"unknown READER station: {station}")
    spec = READER_ELEMENTS[element]
    file_element = element
    if element == "pressure":
        file_element = (
            "station_level_pressure" if station in READER_STATION_LEVEL_ONLY else "msl_pressure"
        )
    return Dataset(
        key=f"reader_{station}_{element}",
        title=f"{READER_STATIONS[station]} 月平均{spec.label}",
        provider="SCAR READER / British Antarctic Survey",
        url=READER_URL_TEMPLATE.format(station=station, element=file_element),
        homepage="https://legacy.bas.ac.uk/met/READER/",
        description=spec.description,
        citation=("Turner, J. et al. (2004) The SCAR READER project, J. Climate 17, 2890-2898."),
    )


def reader_temperature(station: str) -> Dataset:
    """Monthly mean surface air temperature for a SCAR READER station."""
    return reader_series(station, "temperature")


OZONE_HOLE_ANNUAL = Dataset(
    key="ozone_hole_annual",
    title="オゾンホール 面積・最低オゾン全量 (年別)",
    provider="NASA Ozone Watch",
    url="https://ozonewatch.gsfc.nasa.gov/statistics/annual_data.txt",
    homepage="https://ozonewatch.gsfc.nasa.gov/",
    description=(
        "衛星 (TOMS・OMI・OMPS) 観測による南半球のオゾンホール。面積は9月7日〜10月13日の"
        "平均 (百万 km², オゾン全量220 DU未満の領域)、最低オゾン全量は9月21日〜10月16日の"
        "最小値 (DU)。1979年から。"
    ),
    citation="NASA Ozone Watch, NASA Goddard Space Flight Center.",
)

OZONE_DAILY_URL_TEMPLATE = (
    "https://ozonewatch.gsfc.nasa.gov/meteorology/figures/ozone/to3areas_{year}_toms+omi+omps.txt"
)


def ozone_hole_daily(year: int) -> Dataset:
    """Daily ozone-hole area for one year, with the climatological percentiles."""
    return Dataset(
        key=f"ozone_hole_daily_{year}",
        title=f"オゾンホール面積 {year}年 (日別)",
        provider="NASA Ozone Watch",
        url=OZONE_DAILY_URL_TEMPLATE.format(year=year),
        homepage="https://ozonewatch.gsfc.nasa.gov/",
        description=(
            "南半球でオゾン全量が220 DU未満の領域の面積 (百万 km²) の日別値と、"
            "1979年以降の同日の統計 (最小・10%・平均・90%・最大)。"
        ),
        citation=OZONE_HOLE_ANNUAL.citation,
    )


CATALOG: tuple[Dataset, ...] = (
    SEA_ICE_EXTENT,
    SOUTH_POLE_CO2,
    SOUTH_POLE_CH4,
    OZONE_HOLE_ANNUAL,
    reader_series("Syowa", "temperature"),
    reader_series("Syowa", "pressure"),
    reader_series("Syowa", "wind_speed"),
    ICE_CORE_CO2,
    EDC_TEMPERATURE,
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

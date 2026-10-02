# 南極観測の公開データ 調査メモ

南極で取得される観測データのうち、誰でも登録なしで取得でき、定期的に更新され、
時系列として扱いやすいものを優先して調べました。
「収録済み」はこのアプリが直接ダウンロードして可視化するデータ、
「候補」は今後の追加候補、または「CSVを分析」ページでの読み込みを想定したデータです。

## 収録済み

| データ | 提供元 | 期間・頻度 | 形式 | 主な分析 |
|---|---|---|---|---|
| 南極海 海氷面積 (Sea Ice Index G02135 v4) | NSIDC / NOAA | 1978年10月〜・日別 | CSV | 年ごとの季節変化の重ね描き、平年差、同日順位、年最小・最大のトレンド |
| 南極点 大気CO₂ (現場連続観測) | NOAA GML (South Pole Observatory, SPO) | 1975年〜・月別 | テキスト (空白区切り) | 長期トレンド、季節変化 (トレンド除去)、年増加量 |
| 南極点 大気メタン (フラスコ採取) | NOAA GML (South Pole Observatory, SPO) | 1983年〜・月別 | テキスト (空白区切り) | CO₂と同じ |
| オゾンホール 面積・最低オゾン全量 | NASA Ozone Watch | 1979年〜・年別／日別 | テキスト (固定幅) | 年ごとの推移、選んだ年の日別面積と平年の帯 |
| 南極アイスコア CO₂ 合成記録 (Bereiter et al. 2015) | NOAA NCEI Paleoclimatology | 約80万年前〜2001年・不等間隔 | テキスト (タブ区切り) | 自然の変動幅、産業革命前の平均、直接観測との接続 |
| EPICA Dome C 気温偏差 (Jouzel et al. 2007) | NOAA NCEI Paleoclimatology | 約80万年前〜現在・不等間隔 | テキスト (固定幅) | 氷期サイクル、CO₂との相関 |
| 観測基地の月平均 気温・気圧・風速 (READER) | SCAR / British Antarctic Survey | 1950年代〜 (基地により異なる)・月別 | テキスト (年×月の表) | 年平均値のトレンド、月別平年値、偏差ヒートマップ、基地の比較 |

- **海氷面積**: `https://noaadata.apps.nsidc.org/NOAA/G02135/south/daily/data/S_seaice_extent_daily_v4.0.csv`
  1987年以前は隔日データ、1987年12月〜1988年1月に欠測があります。
  月平均は10日以上データがある月のみ計算しています。
- **南極点CO₂**: `https://gml.noaa.gov/aftp/data/trace_gases/co2/in-situ/surface/txt/co2_spo_surface-insitu_1_ccgg_MonthlyData.txt`
  欠測値 (`-999.99`) と品質フラグが `.` で始まらない行は除外しています。
- **南極点メタン**: `https://gml.noaa.gov/aftp/data/trace_gases/ch4/flask/surface/txt/ch4_spo_surface-flask_1_ccgg_month.txt`
  南極点のメタンは現場連続観測がないため、フラスコ採取の月平均を使っています (単位 ppb)。
- **オゾンホール**: 年別 `https://ozonewatch.gsfc.nasa.gov/statistics/annual_data.txt`、
  日別 `https://ozonewatch.gsfc.nasa.gov/meteorology/figures/ozone/to3areas_<年>_toms+omi+omps.txt`
  面積はオゾン全量220 DU未満の領域で、年別値は9月7日〜10月13日の平均、最低オゾン全量は
  9月21日〜10月16日の最小値です。日別ファイルには1979年以降の同日の統計 (最小・10%・平均・90%・最大) が
  含まれます。1995年は衛星観測がなく日別データはありません (年別値は再解析で補完)。
- **アイスコア CO₂**: `https://www.ncei.noaa.gov/pub/data/paleo/icecore/antarctica/antarctica2015co2composite.txt`
  年代は1950年を基準とした「何年前」(BP) で、最新 (-51) は2001年に当たります。
  自然の変動幅は1750年以前 (200 BP以前)、産業革命前の値は1000〜1750年の平均です。
- **EPICA Dome C 気温**: `https://www.ncei.noaa.gov/pub/data/paleo/icecore/antarctica/epica_domec/edc3deuttemp2007.txt`
  気温は過去1000年平均からの差で、δD から換算した推定値です。
  δD が欠測でも気温がある行は使い、気温のない行は除外しています。
  CO₂との相関は、CO₂の各サンプルの年代に気温を線形補間して計算しています。
- **READER 気温・気圧・風速**: `https://legacy.bas.ac.uk/met/READER/surface/<基地名>.All.<要素>.txt`
  (要素は `temperature`・`msl_pressure`・`wind_speed`)
  昭和基地 (`Syowa`) のほか、南極点・ボストーク・マクマードなど16基地を選べます。
  気圧は海面気圧ですが、海面気圧のない高原上の南極点・ボストークは現地気圧 (`station_level_pressure`) です。
  風速はノットで公開されているため m/s に換算しています。

## 候補 (未収録)

### 日本の南極地域観測 (JARE) 関連
- **国立極地研究所 学術データベース** (<https://scidbase.nipr.ac.jp/>)
  昭和基地のオーロラ・地磁気・大気・雪氷などの観測データのメタデータ集。
  データ本体は記録紙・マイクロフィルム・独自形式のデジタルデータなどで、CSVを直接ダウンロードできる
  データセットは多くありません。入手できたデータは、日付と値の2列のCSVに整えてから
  「CSVを分析」ページで読み込んでください。
- **気象庁 南極昭和基地の気象・オゾン観測**
  昭和基地 (国際地点番号 89532) の地上気象は気象庁「過去の気象データ検索」の「南極」から、
  オゾン全量・オゾンゾンデ・紫外線は気象庁オゾン層・紫外線のページから入手できます。
  地上気象は「過去の気象データ・ダウンロード」(<https://www.data.jma.go.jp/risk/obsdl/>) で
  地点に「南極 → 昭和」を選ぶとCSVで入手でき、ダウンロードしたファイル
  (Shift_JIS・複数行の見出し・品質情報の列つき) を「CSVを分析」ページでそのまま読み込めます。
- **PANGAEA** (<https://www.pangaea.de/>): 南極の氷床コア・気象・海洋などの研究データ。
  各データセットの「Download dataset as tab-delimited text」で得られるテキスト
  (先頭に `/* ... */` の説明ブロックつき) を「CSVを分析」ページでそのまま読み込めます。

### 大気・オゾン
- **NOAA GML 南極点のその他の成分**: 一酸化二窒素、フロン類、エアロゾル、放射などを同じサイトから公開
  (CO₂とメタンは収録済み)。

### 気象・雪氷
- **AMRDC / Antarctic Automatic Weather Stations** (ウィスコンシン大学): 無人気象観測点 (AWS) の高頻度データ。
- **GRACE / GRACE-FO 南極氷床質量変化** (NASA): 2002年〜の月別氷床質量 (Gt)。NASA Earthdata のログインが必要なものがあります。
- **ERA5 再解析** (Copernicus): 格子データ。アカウント登録と容量の大きいNetCDF処理が必要です。

### 古気候・地理
- **その他の氷床コア記録** (NOAA NCEI Paleoclimatology / PANGAEA): ボストークの気温、メタン (CH₄)、
  ドームふじ (日本) のδ¹⁸O など。CO₂とEPICA Dome C の気温は収録済みです。
- **SCAR Antarctic Digital Database / Quantarctica**: 海岸線・基地位置などの地理データ (地図表示の追加に使えます)。

## 利用上の注意
- 各データの利用条件・引用方法は提供元のページに従ってください。各ページ下部に出典を表示しています。
- ダウンロードしたデータは `~/.cache/antarctic-viz/` に24時間キャッシュされ、
  取得に失敗したときは古いキャッシュを使います。サイドバーの「データを再取得」で強制的に更新できます。
- 準リアルタイムのデータ (海氷面積の直近数日など) は後日修正されることがあります。

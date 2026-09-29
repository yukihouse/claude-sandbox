# antarctic-viz — 南極観測データ ビューア

南極で取得されている公開観測データをダウンロードし、ブラウザで可視化・分析する
[Streamlit](https://streamlit.io/) 製のWeb UIです。

| ページ | データ | 分析 |
|---|---|---|
| 海氷面積 | NSIDC Sea Ice Index (南半球・日別) | 年ごとの重ね描き＋平年の帯、同日順位、月別偏差ヒートマップ、年最小・最大のトレンド |
| 南極点 温室効果ガス | NOAA GML 南極点観測所 (CO₂・CH₄、月別) | 長期トレンド、トレンド除去後の季節変化、年増加量 |
| オゾンホール | NASA Ozone Watch (年別・日別) | 面積と最低オゾン全量の推移、選んだ年の日別面積と平年の帯の比較 |
| アイスコア | NOAA NCEI (南極アイスコアCO₂合成記録・EPICA Dome C 気温) | 過去80万年のCO₂と気温、自然の変動幅・産業革命前との比較、南極点の直接観測との接続、CO₂と気温の相関 |
| 基地の気象 | SCAR READER (昭和基地ほか16基地の気温・気圧・風速、月別) | 年平均値のトレンド、月別平年値、偏差ヒートマップ、複数基地の比較 |
| CSVを分析 | 手元のCSV (国立極地研究所などから入手したデータ) | 上記と同じトレンド・偏差分析 |
| データソース | 調査メモ | 収録済み・候補のデータ一覧 ([`data_sources.md`](src/antarctic_viz/data_sources.md)) |

気候値・偏差の基準期間はサイドバーで変更できます (既定値は1981–2010年)。

## 起動

```bash
cd antarctica-viz
uv sync
uv run antarctic-viz        # = streamlit run src/antarctic_viz/app.py
```

ブラウザで <http://localhost:8501> を開きます。データは初回表示時に各機関のサーバーから
ダウンロードされ、`~/.cache/antarctic-viz/` に24時間キャッシュされます
(取得に失敗したときは古いキャッシュで表示を続けます)。

## 構成

```
src/antarctic_viz/
  sources.py       データセットのカタログと、キャッシュ付きダウンローダー
  parsers.py       各配布形式 → date/value の DataFrame
  analysis.py      トレンド、気候値・偏差、日別の平年帯、同日順位、季節変化など
  charts.py        Altair のグラフ (色覚多様性に配慮した配色)
  app.py           Streamlit の画面
  data_sources.md  公開データの調査メモ (アプリの「データソース」ページ)
```

## 開発

```bash
uv sync --dev
uv run coverage run -m unittest discover -s tests -t .
uv run coverage report -m     # 100% 必須
uv run ruff check . && uv run ruff format --check .
```

UIのテスト (`tests/test_app.py`) は `streamlit.testing` の `AppTest` で画面を実行し、
ネットワーク取得は各データ形式の合成データに差し替えています。

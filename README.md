# claude-sandbox
claude code向けのsandbox

## 構成

同じ「カウンター」アプリを複数の言語・フレームワークで実装したデモ集です。
各デモは `xxx-demo` フォルダの下に自己完結しており、共通の「ホーム画面」（リポジトリ
ルートの `index.html` / `style.css`）からのみリンクされます。

デモ同士が直接リンクし合うことはありません（依存方向を一方向にするため）。
各デモは「ホームへ戻る」リンクだけを持ち、ホーム画面が全デモへのリンクを持ちます。

```
/                 ホーム画面（静的HTML、フレームワーク・ビルド不要）
├── index.html
└── style.css

/vite-demo        Vite (React) 版
/python-demo      Python (Flask) 版
├── gradio-ver    同デモのGUIをGradioで構築した版
└── nicegui-ver   同デモのGUIをNiceGUIで構築した版
/rust-demo        Rust (axum) 版
/go-demo          Go (net/http) 版
/csharp-demo      C# (ASP.NET Core) 版
/typescript-demo  TypeScript (Deno) 版
/zig-demo         Zig (std.net) 版
└── zig-perf-demo Zig vs Python 速度対決デモ
/kotlin-demo      Kotlin (Ktor) 版
/php-demo         PHP 版
```

新しい言語のデモを追加する場合は、

1. その言語用の `xxx-demo` フォルダを追加し、ホーム画面への「戻る」リンクだけを持たせる
2. ホーム画面（`index.html`）にそのデモへのリンクカードを1つ追加する

の2箇所を変更するだけで完結します。既存デモやホーム画面のロジックには手を入れません。

### 各デモ画面の共通ルール

各デモのカウンター画面（`index.html`）は、見た目・構造を揃えるために次の契約に
従っています。専用のテンプレートフォルダは用意していないので、新しい言語のデモを
追加する際は既存デモ（例: `go-demo/templates/index.html`）をコピーして書き換えて
ください。

- `style.css` はそのまま流用する（内容を変更しない。ビルドツールで独自にスタイルを
  管理する `vite-demo` のようなケースは除く）
- カウンターの数値は `id="count"` の要素に表示する
- ボタンは `.btn-increment`（+1）・`.btn-reset`（リセット）の class を持つ
- 「ホームへ戻る」リンクは `.nav-link` class を持ち、`href` は `http://localhost:8080/` 固定
- タイトル・見出しは `カウンターデモ (○○版)` の形式にする

## まとめて起動する

各デモをひとつずつ手動で起動するのが手間な場合は、リポジトリルートの
`start-all.sh` を使うと、インストール済みのツールチェインが揃っているデモを
まとめて起動できます（未インストールの言語のデモは自動的にスキップされます）。

```bash
./start-all.sh
```

各デモは `logs/<デモ名>.log` にログを出力しながらバックグラウンドで起動します。
停止するには `Ctrl+C` を押してください（起動した全プロセスをまとめて停止します）。

## ホーム画面

フレームワークやビルドツールに依存しない、素の HTML/CSS のみで作られた静的ページです。
どの言語のデモにも肩入れしないよう、あえて特定の言語ランタイムを要求しない構成にしています。

### 起動方法

```bash
# リポジトリルートで、任意の静的サーバーを使って起動します
python3 -m http.server 8080
```

ブラウザで http://localhost:8080 を開くと、各デモへのリンク一覧が表示されます。

## カウンターデモアプリ（Vite / React版）

React + Vite + Tailwind CSS で作られたシンプルなカウンターアプリです（[vite-demo](vite-demo)）。
ボタンを押すとカウントがリアルタイムで増加します。

### セットアップ手順

```bash
cd vite-demo

# 依存パッケージをインストール
npm install

# 開発サーバーを起動
npm run dev
```

ブラウザで表示されたURL（デフォルトは http://localhost:5173 ）を開くと、
カウンターデモが表示されます。

### ビルド

```bash
cd vite-demo

# 本番用ビルド
npm run build

# ビルド結果をローカルでプレビュー
npm run preview
```

### 使い方

- 「+1」ボタン：カウントを1増やします
- 「リセット」ボタン：カウントを0に戻します

### 単体テスト

```bash
cd vite-demo
npm run test
```

### 静的解析（ESLint）

```bash
cd vite-demo
npm run lint
```

### E2Eテスト（Playwright）

実際のブラウザ（Chromium）でデモアプリを操作し、動作確認を自動化するE2Eテストです。
Playwright が開発サーバー（`npm run dev`）を自動で起動・停止するため、事前にサーバーを
立ち上げておく必要はありません。

```bash
cd vite-demo

# 初回のみ: テストで使うブラウザをインストール
npx playwright install --with-deps chromium

# E2Eテストを実行
npm run test:e2e
```

`npm run test`（Vitest + Testing Library）が仮想DOM上でコンポーネントの振る舞いを
検証するのに対し、こちらは実際に起動したアプリに対してブラウザから「+1」「リセット」
ボタンをクリックし、画面表示やリンク遷移までを含めて確認します。

### CI

`main` ブランチへのプルリクエスト作成時に GitHub Actions
（[.github/workflows/ci.yml](.github/workflows/ci.yml)）が自動実行され、
`vite-demo` に対して静的解析・単体テスト・ビルド・E2Eテスト（Playwright）の
4つを検証します。

## カウンターデモアプリ（Python版）

Flask で作られた同じカウンターデモアプリです（[python-demo](python-demo)）。

「🎉 テンションが上がるカウンター」機能つきです。+1ボタンを押すたびに、節目の回数や
クリックの速さに応じたコメントが表示されます。実際のLLMは呼ばず、ルールベース＋
ランダム選択でそれっぽく反応しているだけですが、手軽にAPIを立てられるPythonらしい
機能です。

### セットアップ手順

```bash
cd python-demo

# 依存パッケージをインストール
uv sync

# 開発サーバーを起動
uv run python app.py
```

ブラウザで http://127.0.0.1:5000 を開くと、Python版のカウンターデモが表示されます。

> **Note:** macOS では「AirPlay受信機能」がデフォルトでポート5000を使っており、
> `http://localhost:5000` を開くとAirPlay側に接続されて403エラーになることがあります。
> `http://127.0.0.1:5000`（IPv4を明示したアドレス）でアクセスすれば回避できます。
> `localhost` のままアクセスしたい場合は、システム設定 →「一般」→
> 「AirDropとHandoff」→「AirPlayレシーバー」をオフにしてください。

### 単体テスト

```bash
cd python-demo
uv run pytest
```

### CI

`main` ブランチへのプルリクエスト作成時に GitHub Actions
（[.github/workflows/ci.yml](.github/workflows/ci.yml)）が自動実行され、
`python-demo` に対して単体テストを検証します。

### GUIライブラリ版

`python-demo` 配下には、同じカウンターアプリを別のPython GUIライブラリで組んだ版も
サブフォルダとして置いています。ロジック（`compute_increment` / `compute_reset`）は
Flask版と同じですが、画面の組み立て方（宣言的UIコンポーネント vs 命令的なイベント
ハンドラ）の違いを見比べられます。

#### Gradio版

Gradio の `Blocks` API でUIを組み立てた版です（[python-demo/gradio-ver](python-demo/gradio-ver)）。

```bash
cd python-demo/gradio-ver

# 依存パッケージをインストール
uv sync

# 開発サーバーを起動
uv run python app.py
```

ブラウザで http://127.0.0.1:5007 を開くと、Gradio版のカウンターデモが表示されます。

単体テストは `cd python-demo/gradio-ver && uv run pytest` で実行できます。

#### NiceGUI版

NiceGUI の `ui` API でUIを組み立てた版です（[python-demo/nicegui-ver](python-demo/nicegui-ver)）。

```bash
cd python-demo/nicegui-ver

# 依存パッケージをインストール
uv sync

# 開発サーバーを起動
uv run python app.py
```

ブラウザで http://127.0.0.1:5008 を開くと、NiceGUI版のカウンターデモが表示されます。

単体テストは `cd python-demo/nicegui-ver && uv run pytest` で実行できます。

#### CI（GUIライブラリ版）

`gradio-ver` / `nicegui-ver` はそれぞれ独立した `pyproject.toml` / `uv.lock` を持つため、
CIでも `python-demo` 本体とは別ジョブ（`python-gradio-demo` / `python-nicegui-demo`）として
単体テストを検証します。

## カウンターデモアプリ（Rust版）

axum で作られた同じカウンターデモアプリです（[rust-demo](rust-demo)）。

### セットアップ手順

```bash
cd rust-demo

# 依存パッケージの取得とサーバー起動
cargo run
```

ブラウザで http://localhost:5001 を開くと、Rust版のカウンターデモが表示されます。

### 単体テスト

```bash
cd rust-demo
cargo test
```

### CI

`main` ブランチへのプルリクエスト作成時に GitHub Actions
（[.github/workflows/ci.yml](.github/workflows/ci.yml)）が自動実行され、
`rust-demo` に対して静的解析・単体テスト・ビルドの3つを検証します。

## カウンターデモアプリ（Go版）

標準ライブラリの `net/http` だけで作られた同じカウンターデモアプリです（[go-demo](go-demo)）。

カウンターに加えて、Goの goroutine と `sync.Mutex` の特徴を体感できる
「🏁 100人同時押しチャレンジ」機能つきです。100個のgoroutineを同時に
起動してカウンターを叩き、排他制御ありなしで結果がどう変わるかを比較できます
（排他制御なしだと race condition により押した回数より少ない結果になることがあります）。

### セットアップ手順

```bash
cd go-demo

# サーバー起動
go run .
```

ブラウザで http://localhost:5002 を開くと、Go版のカウンターデモが表示されます。

### 単体テスト

```bash
cd go-demo
go test ./...
```

### CI

`main` ブランチへのプルリクエスト作成時に GitHub Actions
（[.github/workflows/ci.yml](.github/workflows/ci.yml)）が自動実行され、
`go-demo` に対して静的解析・単体テスト・ビルドの3つを検証します。

## カウンターデモアプリ（C#版）

ASP.NET Core（Minimal API）で作られた同じカウンターデモアプリです（[csharp-demo](csharp-demo)）。

カウンターに加えて、C#のLINQの強さを体感できる「📊 クリック統計」機能つきです。
+1ボタンを押した時刻をサーバー側で記録し、LINQの `Zip` / `Average` / `Min` / `Max`
でクリック間隔（平均・最速・最遅）を集計して表示します。

### セットアップ手順

```bash
cd csharp-demo

# サーバー起動
dotnet run
```

ブラウザで http://localhost:5003 を開くと、C#版のカウンターデモが表示されます。

### 単体テスト

```bash
cd csharp-demo/CsharpDemo.Tests
dotnet test
```

### CI

`main` ブランチへのプルリクエスト作成時に GitHub Actions
（[.github/workflows/ci.yml](.github/workflows/ci.yml)）が自動実行され、
`csharp-demo` に対して単体テストを検証します。

## カウンターデモアプリ（TypeScript版）

Deno（`Deno.serve`）で作られた同じカウンターデモアプリです（[typescript-demo](typescript-demo)）。
Node.js版のフロントエンドである Vite 版とは異なり、サーバーサイドを TypeScript で
書いたバックエンド実装です。

カウンターの値はサーバー側で共有されており、複数のタブ・複数のブラウザで同時に開くと
`Deno.upgradeWebSocket` によるWebSocketでリアルタイムに同期します（「👥 みんなで見てる
カウンター」機能）。今何人が同時に見ているかも表示されます。

### セットアップ手順

```bash
cd typescript-demo

# サーバー起動
deno task start
```

ブラウザで http://localhost:5004 を開くと、TypeScript版のカウンターデモが表示されます。

### 単体テスト

```bash
cd typescript-demo
deno task test
```

### CI

`main` ブランチへのプルリクエスト作成時に GitHub Actions
（[.github/workflows/ci.yml](.github/workflows/ci.yml)）が自動実行され、
`typescript-demo` に対して型チェック・単体テストを検証します。

## カウンターデモアプリ（Zig版）

Zig 標準ライブラリの `std.net` だけで作られた同じカウンターデモアプリです
（[zig-demo](zig-demo)）。**Zig 0.15系を対象にしています。**

> **Note:** Zig 0.16（現行の最新安定版）では `std.net` 自体が撤廃され、
> `std.Io.net` という新しいI/O抽象化（vtableベース）に置き換わっています。
> Homebrewなどで入る `zig` コマンドが既に 0.16 系になっている場合はこのまま動かず、
> [zigup](https://github.com/marler8997/zigup) や
> [zvm](https://www.zvm.app/) などのバージョン管理ツール、
> または [ziglang.org/download](https://ziglang.org/download/) から
> 0.15系のバイナリを別途用意してください（例:
> `brew install zig@0.15 && brew link zig@0.15`）。

### セットアップ手順

```bash
cd zig-demo

# サーバー起動
zig run src/main.zig
```

ブラウザで http://localhost:5005 を開くと、Zig版のカウンターデモが表示されます。

### 単体テスト

```bash
cd zig-demo
zig test src/main.zig
```

### CI

`main` ブランチへのプルリクエスト作成時に GitHub Actions
（[.github/workflows/ci.yml](.github/workflows/ci.yml)）が自動実行され、
`zig-demo` に対して単体テストを検証します。

## Zig vs Python 速度対決デモ

カウンターアプリではなく、Zig の「圧倒的なパフォーマンス」を体感するための単体デモです
（[zig-demo/zig-perf-demo](zig-demo/zig-perf-demo)）。

「素数を1つずつ試し割りで数える」という同じアルゴリズムを Zig（ネイティブコンパイル）と
Python（インタプリタ）でまったく同じ実装で用意し、ボタンを押すとサーバー上で両方を実際に
実行して所要時間を比較します。Zig サーバーが `python3` をサブプロセスとして起動して計測する
ため、追加のサーバー起動は不要です（`python3` が見つからない環境ではPython側の結果が
「N/A」になります）。

### セットアップ手順

```bash
cd zig-demo/zig-perf-demo

# サーバー起動（パフォーマンス比較のため最適化ビルドで実行する）
zig run -O ReleaseFast src/main.zig
```

ブラウザで http://localhost:5006 を開くと、探索範囲を選んで「ベンチマーク実行」ボタンを
押せます。実行のたびにサーバー上で Zig 版・Python 版それぞれの実行時間を計測し、何倍
高速だったかを表示します。**Zig 0.15系を対象にしています**（zig-demo と同様の理由）。

### 単体テスト

```bash
cd zig-demo/zig-perf-demo
zig test src/main.zig
```

### CI

`main` ブランチへのプルリクエスト作成時に GitHub Actions
（[.github/workflows/ci.yml](.github/workflows/ci.yml)）が自動実行され、
`zig-demo/zig-perf-demo` に対して単体テストを検証します。

## カウンターデモアプリ（Kotlin版）

Ktor（Nettyエンジン）で作られた同じカウンターデモアプリです（[kotlin-demo](kotlin-demo)）。

カウンターに加えて、Kotlinのcoroutine（`delay`によるノンブロッキングな待機）を
体感できる「🚀 コルーチンオートパイロット」機能つきです。ボタンを押すとサーバー側が
一定間隔で自動的にカウントアップし、Server-Sent Eventsでブラウザにリアルタイム配信します。

### セットアップ手順

```bash
cd kotlin-demo

# 依存パッケージの取得とサーバー起動（Gradle Wrapper使用）
./gradlew run
```

ブラウザで http://localhost:5009 を開くと、Kotlin版のカウンターデモが表示されます。

### 単体テスト

```bash
cd kotlin-demo
./gradlew test
```

### CI

`main` ブランチへのプルリクエスト作成時に GitHub Actions
（[.github/workflows/ci.yml](.github/workflows/ci.yml)）が自動実行され、
`kotlin-demo` に対して単体テスト・ビルドを検証します。

## カウンターデモアプリ（PHP版）

PHP組み込みのWebサーバーだけで作られた同じカウンターデモアプリです（[php-demo](php-demo)）。

カウンターの値はPHPセッションに保存されており、ページをリロードしても、
ブラウザを閉じて再度開いても消えません（セッションクッキーの有効期限を30日に
設定しています）。

### セットアップ手順

```bash
cd php-demo

# 依存パッケージ（PHPUnit）をインストール
composer install

# サーバー起動
php -S localhost:5010 index.php
```

ブラウザで http://localhost:5010 を開くと、PHP版のカウンターデモが表示されます。

### 単体テスト

```bash
cd php-demo
composer test
```

### CI

`main` ブランチへのプルリクエスト作成時に GitHub Actions
（[.github/workflows/ci.yml](.github/workflows/ci.yml)）が自動実行され、
`php-demo` に対して単体テストを検証します。

---

各デモアプリは以下のポートで動作する前提です。
ホーム画面も含めてすべて同時に起動しておくと、ホーム画面からリンクを辿って行き来できます。

| デモ | ディレクトリ | ポート |
| --- | --- | --- |
| ホーム画面 | [/](.) | 8080 |
| Vite (React) | [vite-demo](vite-demo) | 5173 |
| Python (Flask) | [python-demo](python-demo) | 5000 |
| Python (Gradio) | [python-demo/gradio-ver](python-demo/gradio-ver) | 5007 |
| Python (NiceGUI) | [python-demo/nicegui-ver](python-demo/nicegui-ver) | 5008 |
| Rust (axum) | [rust-demo](rust-demo) | 5001 |
| Go (net/http) | [go-demo](go-demo) | 5002 |
| C# (ASP.NET Core) | [csharp-demo](csharp-demo) | 5003 |
| TypeScript (Deno) | [typescript-demo](typescript-demo) | 5004 |
| Zig (std.net) | [zig-demo](zig-demo) | 5005 |
| Zig vs Python 速度対決 | [zig-demo/zig-perf-demo](zig-demo/zig-perf-demo) | 5006 |
| Kotlin (Ktor) | [kotlin-demo](kotlin-demo) | 5009 |
| PHP | [php-demo](php-demo) | 5010 |

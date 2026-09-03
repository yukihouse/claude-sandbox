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
/rust-demo        Rust (axum) 版
/go-demo          Go (net/http) 版
/csharp-demo      C# (ASP.NET Core) 版
/typescript-demo  TypeScript (Deno) 版
```

新しい言語のデモを追加する場合は、

1. その言語用の `xxx-demo` フォルダを追加し、ホーム画面への「戻る」リンクだけを持たせる
2. ホーム画面（`index.html`）にそのデモへのリンクカードを1つ追加する

の2箇所を変更するだけで完結します。既存デモやホーム画面のロジックには手を入れません。

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

### CI

`main` ブランチへのプルリクエスト作成時に GitHub Actions
（[.github/workflows/ci.yml](.github/workflows/ci.yml)）が自動実行され、
`vite-demo` に対して静的解析・単体テスト・ビルドの3つを検証します。

## カウンターデモアプリ（Python版）

Flask で作られた同じカウンターデモアプリです（[python-demo](python-demo)）。

### セットアップ手順

```bash
cd python-demo

# 依存パッケージをインストール
pip install -r requirements.txt

# 開発サーバーを起動
python app.py
```

ブラウザで http://localhost:5000 を開くと、Python版のカウンターデモが表示されます。

## カウンターデモアプリ（Rust版）

axum で作られた同じカウンターデモアプリです（[rust-demo](rust-demo)）。

### セットアップ手順

```bash
cd rust-demo

# 依存パッケージの取得とサーバー起動
cargo run
```

ブラウザで http://localhost:5001 を開くと、Rust版のカウンターデモが表示されます。

## カウンターデモアプリ（Go版）

標準ライブラリの `net/http` だけで作られた同じカウンターデモアプリです（[go-demo](go-demo)）。

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

---

各デモアプリは以下のポートで動作する前提です。
ホーム画面も含めてすべて同時に起動しておくと、ホーム画面からリンクを辿って行き来できます。

| デモ | ディレクトリ | ポート |
| --- | --- | --- |
| ホーム画面 | [/](.) | 8080 |
| Vite (React) | [vite-demo](vite-demo) | 5173 |
| Python (Flask) | [python-demo](python-demo) | 5000 |
| Rust (axum) | [rust-demo](rust-demo) | 5001 |
| Go (net/http) | [go-demo](go-demo) | 5002 |
| C# (ASP.NET Core) | [csharp-demo](csharp-demo) | 5003 |
| TypeScript (Deno) | [typescript-demo](typescript-demo) | 5004 |

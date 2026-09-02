# claude-sandbox
claude code向けのsandbox

## カウンターデモアプリ

React + Vite + Tailwind CSS で作られたシンプルなカウンターアプリです。
ボタンを押すとカウントがリアルタイムで増加します。

### セットアップ手順

```bash
# 依存パッケージをインストール
npm install

# 開発サーバーを起動
npm run dev
```

ブラウザで表示されたURL（デフォルトは http://localhost:5173 ）を開くと、
カウンターデモが表示されます。

### ビルド

```bash
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
npm run test
```

### 静的解析（ESLint）

```bash
npm run lint
```

### CI

`main` ブランチへのプルリクエスト作成時に GitHub Actions
（[.github/workflows/ci.yml](.github/workflows/ci.yml)）が自動実行され、
静的解析・単体テスト・ビルドの3つを検証します。

## カウンターデモアプリ（Python版）

Flask で作られた同じカウンターデモアプリです（[python-demo](python-demo)）。
各デモアプリの画面下部から、他の言語版デモアプリへそれぞれ移動できます。

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

---

各デモアプリは以下のポートで動作する前提で、互いにリンクしています。
すべて同時に起動しておくと、画面下部のリンクから行き来できます。

| デモ | ディレクトリ | ポート |
| --- | --- | --- |
| Vite (React) | [/](.) | 5173 |
| Python (Flask) | [python-demo](python-demo) | 5000 |
| Rust (axum) | [rust-demo](rust-demo) | 5001 |
| Go (net/http) | [go-demo](go-demo) | 5002 |


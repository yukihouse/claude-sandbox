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
ホーム画面から Vite 版デモアプリへ、Vite 版デモアプリからも Python 版へ
それぞれ移動できます。

### セットアップ手順

```bash
cd python-demo

# 依存パッケージをインストール
pip install -r requirements.txt

# 開発サーバーを起動
python app.py
```

ブラウザで http://localhost:5000 を開くと、Python版のカウンターデモが表示されます。
（Vite版デモアプリは http://localhost:5173 で起動している前提でリンクしています）


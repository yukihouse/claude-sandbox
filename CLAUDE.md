# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

同じ「カウンター」アプリを9言語・フレームワークで並行実装したデモ集です。各デモの
セットアップ手順・テストコマンド・ポート番号は README.md に一覧があるので、まずそちらを
参照してください。

## 構造上の制約

- デモ同士は直接リンクし合わない（依存方向を一方向にするため）。各デモは「ホームへ戻る」
  リンクのみを持ち、ホーム画面（`index.html` / `style.css`）が全デモへのリンクカードを持つ。
- 新しい言語のデモを追加する場合、変更は次の2箇所だけで完結する設計になっている。既存
  デモやホーム画面のロジックには手を入れない。
  1. `xxx-demo/` フォルダを新規追加し、ホームへの「戻る」リンクだけを持たせる
  2. `index.html` にそのデモへのリンクカードを1つ追加する
  （加えて README・`start-all.sh`・`.github/workflows/ci.yml` にもそのデモの分を追記する）

## その他の注意点

- `.github/workflows/ci.yml` は `dorny/paths-filter` で変更のあったデモディレクトリのみを
  検出し、該当するジョブだけを実行する。
- Zig は 0.15系専用（0.16で `std.net` が撤廃され `std.Io.net` に置き換わっているため非互換）。
- リポジトリ内のコミットメッセージ・コメント・ドキュメントは日本語が基本。

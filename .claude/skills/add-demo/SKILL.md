---
name: add-demo
description: Scaffold a new per-language/framework implementation of this repo's counter demo app, following the repo's strict two-file-change convention. Use when the user asks to add a new language, framework, or runtime version of the counter demo (e.g. "PHPでも作って", "add a Kotlin demo").
---

# 新しい言語デモの追加

このリポジトリは同じ「カウンター」アプリを複数の言語・フレームワークで実装したデモ集です。
新しいデモを追加するときは、以下の設計上の制約を厳守してください。

## 守るべき制約

- デモ同士は**直接リンクし合わない**（依存方向を一方向にするため）。各デモが持つリンクは
  「ホームへ戻る」の1つだけ。
- 既存デモやホーム画面 (`index.html` / `style.css`) のロジックには手を入れない。
- 新しいデモは `xxx-demo/` という名前のフォルダに自己完結させる。
- 挙動は既存デモと同じ「カウンター」仕様にする: 「+1」ボタンでカウントを増やし、
  「リセット」ボタンで0に戻す。他のデモの実装（例えば `go-demo/main.go` や
  `python-demo/app.py`）を参照して同等のUI・挙動にする。
- 使用するポート番号は、README.md 末尾の一覧表にある既存デモと重複しないものを choose する
  (現在 8080, 5173, 5000-5005 が使用済み)。

## 手順

1. `xxx-demo/` フォルダを新規作成し、そこにその言語のサーバー実装・テスト・静的ファイル
   (HTML/CSS/JS) を置く。ホームへの「戻る」リンクのみを持たせる。
2. リポジトリルートの `index.html` に、そのデモへのリンクカードを1つだけ追加する
   (既存のカードの構造を踏襲する)。
3. `README.md` に、他のデモと同じ体裁でセットアップ手順・単体テストの実行方法・CIの説明を
   追記し、末尾のポート一覧表にも1行追加する。
4. `.github/workflows/ci.yml` に、`dorny/paths-filter` の新しいフィルタと、対応する
   lint/test/buildジョブを追加する(既存の他言語ジョブを踏襲する)。
5. `start-all.sh` の `start` 呼び出し一覧に、新デモの起動コマンドを1行追加する
   (`start "<name>" "<dir>" "<cmd>" "<requires-binary>"` の形式)。
6. 必要であれば `.claude/hooks/session-start.sh` に、Claude Code on the web の
   セッションでツールチェインが未インストールの場合のインストール処理を追加する
   (既存の .NET / Zig のインストール処理を参考にする)。
7. `CLAUDE.md` の対応表にも新デモの行を追加する。

## 完了確認

- 新デモのテストがローカルで通ること。
- `./start-all.sh` で他のデモと一緒に起動でき、ホーム画面から新デモへ、新デモから
  ホームへ、それぞれリンクで行き来できること。

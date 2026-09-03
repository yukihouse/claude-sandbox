# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

同じ「カウンター」アプリを7つの言語・フレームワークで並行実装したデモ集です。各デモは
`xxx-demo/` 配下に自己完結しており、リポジトリルートの静的ホーム画面（`index.html` /
`style.css`）からのみリンクされます。**デモ同士は直接リンクし合いません**（依存方向を
一方向にするため）。各デモは「ホームへ戻る」リンクのみを持ち、ホーム画面が全デモへの
リンクカードを持つ、という構造上の制約があります。

新しい言語のデモを追加する場合、変更箇所は以下の2つだけで完結するように設計されています。
既存デモやホーム画面のロジックには手を入れないこと。

1. その言語用の `xxx-demo/` フォルダを追加し、ホーム画面への「戻る」リンクだけを持たせる
2. ホーム画面（`index.html`）にそのデモへのリンクカードを1つ追加する

## Demos: ports, commands, dependencies

| デモ | ディレクトリ | ポート | 起動 | テスト |
| --- | --- | --- | --- | --- |
| ホーム画面 | `/` | 8080 | `python3 -m http.server 8080` | — |
| Vite (React) | `vite-demo` | 5173 | `npm install && npm run dev` | `npm run test` (Vitest) |
| Python (Flask) | `python-demo` | 5000 | `uv sync && uv run python app.py` | `uv run pytest` |
| Rust (axum) | `rust-demo` | 5001 | `cargo run` | `cargo test` |
| Go (net/http) | `go-demo` | 5002 | `go run .` | `go test ./...` |
| C# (ASP.NET Core) | `csharp-demo` | 5003 | `dotnet run` | `cd CsharpDemo.Tests && dotnet test` |
| TypeScript (Deno) | `typescript-demo` | 5004 | `deno task start` | `deno task test` |
| Zig (std.net, 0.15系) | `zig-demo` | 5005 | `zig run src/main.zig` | `zig test src/main.zig` |

各コマンドは対応する `xxx-demo/` ディレクトリ内で実行する。全デモをまとめて起動するには
リポジトリルートで `./start-all.sh` を実行する（未インストールのツールチェインのデモは
自動スキップされる。ログは `logs/<demo>.log`、停止は Ctrl+C）。

Lint / 静的解析（CIで実行されるもの）:
- `vite-demo`: `npm run lint`（ESLint）
- `go-demo`: `go vet ./...`
- `rust-demo`: `cargo clippy --all-targets -- -D warnings`
- `typescript-demo`: `deno check server.ts`

macOS では `python-demo` を `localhost:5000` で開くとAirPlay受信機能とポートが衝突するため、
`127.0.0.1:5000` を使う（README参照）。

## CI

`.github/workflows/ci.yml` は `dorny/paths-filter` で変更のあったデモディレクトリのみを
検出し、該当するジョブだけを実行する（`main` へのPR時）。各デモのジョブ内容は上表の
起動/テスト/lintコマンドと一致している。新しいデモを追加する際はこのワークフローにも
`paths-filter` のフィルタとジョブを追加する必要がある。

`.github/workflows/codeql.yml` が言語ごとのCodeQL解析、
`.github/workflows/cleanup-merged-branches.yml` がマージ済みブランチの自動削除を行う。

## Notes

- Zig は 0.15系専用（0.16で `std.net` が撤廃され `std.Io.net` に置き換わっているため非互換）。
- リポジトリ内のコミットメッセージ・コメント・ドキュメントは日本語が基本。

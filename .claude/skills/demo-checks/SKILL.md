---
name: demo-checks
description: Run the same lint/test/build checks CI runs, scoped to whichever xxx-demo/ directories have changed in this repo. Use before finishing or pushing changes to any demo, or when asked to run tests/lint/CI checks locally.
---

# デモごとのローカルCIチェック

`.github/workflows/ci.yml` は `dorny/paths-filter` で変更のあった `xxx-demo/` ディレクトリ
だけを検出し、該当するジョブのみ実行する。ローカルでも同じ範囲だけをチェックすることで、
無関係な言語のツールチェイン不足で足止めされずに済む。

## 手順

1. 変更範囲を確認する: `git diff --name-only origin/main...HEAD`(または作業中の差分)
   から、どの `xxx-demo/` ディレクトリに変更があるかを特定する。
2. 変更のあったデモについてのみ、下表のコマンドを実行する。ツールチェインが
   インストールされていない場合はその旨を報告し、スキップしてよい
   (`.claude/hooks/session-start.sh` が Claude Code on the web 環境では
   .NET/Zig を自動インストールする)。

| デモ | 静的解析 | 単体テスト | ビルド確認 |
| --- | --- | --- | --- |
| `vite-demo` | `npm run lint` | `npm run test` | `npm run build` |
| `go-demo` | `go vet ./...` | `go test ./...` | `go build ./...` |
| `rust-demo` | `cargo clippy --all-targets -- -D warnings` | `cargo test` | `cargo build` |
| `csharp-demo` | — | `cd CsharpDemo.Tests && dotnet test` | — |
| `typescript-demo` | `deno check server.ts` | `deno task test` | — |
| `python-demo` | — | `uv run pytest` | — |
| `zig-demo` | — | `zig test src/main.zig` | — |

各コマンドは対応する `xxx-demo/` ディレクトリ内で実行する(`cd` してから実行、または
`--prefix`/`--manifest-path` 等の相当オプションを使う)。

3. すべて成功したら結果を簡潔に報告する。失敗があれば原因を調査して修正し、再実行する。

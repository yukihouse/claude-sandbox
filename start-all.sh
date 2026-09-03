#!/usr/bin/env bash
# 全デモ（ホーム画面 + 各言語版カウンターデモ）をまとめて起動するエントリーポイント。
#
# 使い方:
#   ./start-all.sh          # 起動できるものだけ起動
#   ./start-all.sh --help   # ヘルプ表示
#
# 各デモのツールチェインが未インストールの場合はそのデモだけスキップします。
# Ctrl+C で起動した全プロセスをまとめて停止します。
# ログは logs/<demo>.log に出力されます。

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT_DIR/logs"
PIDS=()
STARTED=()
SKIPPED=()

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage: ./start-all.sh

リポジトリ内の全デモ（ホーム画面 + vite/python/rust/go/csharp/typescript/zig の
各カウンターデモ）を、必要なツールチェインが揃っているものだけまとめて起動します。

  ホーム画面           http://localhost:8080
  Vite (React)         http://localhost:5173
  Python (Flask)       http://localhost:5000
  Rust (axum)          http://localhost:5001
  Go (net/http)        http://localhost:5002
  C# (ASP.NET Core)    http://localhost:5003
  TypeScript (Deno)    http://localhost:5004
  Zig (std.net)        http://localhost:5005

停止するには Ctrl+C を押してください。
EOF
  exit 0
fi

mkdir -p "$LOG_DIR"

cleanup() {
  echo
  echo "全プロセスを停止しています..."
  # setsid で各デモを専用のプロセスグループとして起動しているため、
  # グループごと (npm が起動する vite の子プロセスなども含めて) 停止する。
  for pid in "${PIDS[@]}"; do
    kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null
  done
  sleep 1
  for pid in "${PIDS[@]}"; do
    kill -KILL -- "-$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null
  done
  wait 2>/dev/null
  echo "停止しました。"
}
trap cleanup EXIT INT TERM

start() {
  local name="$1" dir="$2" cmd="$3" requires="$4"

  if [[ -n "$requires" ]] && ! command -v "$requires" >/dev/null 2>&1; then
    echo "[skip] $name: '$requires' が見つからないためスキップします"
    SKIPPED+=("$name")
    return
  fi

  setsid bash -c "cd '$ROOT_DIR/$dir' && $cmd" >"$LOG_DIR/$name.log" 2>&1 &

  local pid=$!
  PIDS+=("$pid")
  STARTED+=("$name")
  echo "[ok]   $name を起動しました (pid=$pid, log=logs/$name.log)"
}

echo "デモをまとめて起動しています..."
echo

start "home"       "."               "python3 -m http.server 8080"                                  "python3"
start "vite"       "vite-demo"       "npm install >/dev/null 2>&1; npm run dev -- --host"           "npm"
start "python"     "python-demo"     "uv sync >/dev/null 2>&1; uv run python app.py"                 "uv"
start "rust"       "rust-demo"       "cargo run"                                                     "cargo"
start "go"         "go-demo"         "go run ."                                                      "go"
start "csharp"     "csharp-demo"     "dotnet run"                                                    "dotnet"
start "typescript" "typescript-demo" "deno task start"                                                "deno"
start "zig"        "zig-demo"        "zig run src/main.zig"                                          "zig"

echo
if [[ ${#STARTED[@]} -eq 0 ]]; then
  echo "起動できるデモがありませんでした。"
  exit 1
fi

echo "起動済み: ${STARTED[*]}"
if [[ ${#SKIPPED[@]} -gt 0 ]]; then
  echo "スキップ: ${SKIPPED[*]}"
fi
echo
echo "ホーム画面: http://localhost:8080"
echo "停止するには Ctrl+C を押してください。"
echo

wait

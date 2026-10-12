#!/usr/bin/env bash
# Start the local studio API and the Vite page. Does not train or call a provider.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY="$(command -v python3)"
fi
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export HF_HUB_DISABLE_PROGRESS_BARS=1
"$PY" -m rcgate.studio --host 127.0.0.1 --port 8765 &
PID=$!
trap 'kill "$PID" 2>/dev/null || true' EXIT
cd "$ROOT/frontend"
npm run dev -- --host 127.0.0.1 --port 5173

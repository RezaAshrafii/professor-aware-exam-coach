#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

command -v node >/dev/null || { echo "Node.js 20.9 or newer is required."; exit 1; }

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt
fi

[ -f .env ] || cp .env.example .env
[ -f web/.env.local ] || cp web/.env.local.example web/.env.local

if [ ! -d web/node_modules/next ]; then
  (cd web && npm install --no-audit --no-fund)
fi

.venv/bin/python run.py &
API_PID=$!
trap 'kill "$API_PID" 2>/dev/null || true' EXIT INT TERM

sleep 2
echo "Product UI: http://localhost:3000"
echo "FastAPI:    http://127.0.0.1:8000"
(cd web && npm run dev)

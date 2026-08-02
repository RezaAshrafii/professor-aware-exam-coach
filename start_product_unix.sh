#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

command -v node >/dev/null || { echo "Node.js 20.9 or newer is required."; exit 1; }

if [[ ! -x .venv/bin/python ]]; then
  echo "[1/5] Creating Python environment..."
  python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt
fi

[[ -f .env ]] || cp .env.example .env
[[ -f web/.env.local ]] || cp web/.env.local.example web/.env.local

if [[ ! -d web/node_modules/next ]]; then
  echo "[2/5] Installing frontend dependencies..."
  (cd web && npm install --no-audit --no-fund)
fi

echo "[3/5] Starting FastAPI..."
.venv/bin/python run.py > /tmp/exam-coach-api.log 2>&1 &
API_PID=$!

echo "[4/5] Starting Next.js..."
(
  cd web
  NEXT_PUBLIC_API_URL= BACKEND_INTERNAL_URL=http://127.0.0.1:8000 npm run dev
) > /tmp/exam-coach-web.log 2>&1 &
WEB_PID=$!
trap 'kill $API_PID $WEB_PID 2>/dev/null || true' EXIT INT TERM

echo "[5/5] Waiting for services..."
for _ in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1 && curl -fsS http://localhost:3000/backend/health >/dev/null 2>&1; then
    echo "Exam Coach is ready at http://localhost:3000"
    wait
    exit 0
  fi
  sleep 0.7
done

echo "Startup failed. See /tmp/exam-coach-api.log and /tmp/exam-coach-web.log."
exit 1

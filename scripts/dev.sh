#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -d "${ROOT_DIR}/.venv" ]]; then
  echo "\n[error] Virtuelle Umgebung (.venv) wurde nicht gefunden. Bitte zuerst \"python3 -m venv .venv\" ausführen." >&2
  exit 1
fi

source "${ROOT_DIR}/.venv/bin/activate"

if ! command -v npm >/dev/null 2>&1; then
  echo "\n[error] npm wurde nicht gefunden. Bitte Node.js installieren." >&2
  exit 1
fi

cd "${ROOT_DIR}"

if [[ ! -f backend/requirements.txt ]]; then
  echo "\n[error] backend/requirements.txt fehlt." >&2
  exit 1
fi

if [[ ! -f frontend/package.json ]]; then
  echo "\n[error] frontend/package.json fehlt." >&2
  exit 1
fi

ENV_FILE="${ROOT_DIR}/.env"
if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # Load env vars so spawned processes (uvicorn/worker) know about model settings
  source "${ENV_FILE}"
  set +a
fi

pip install --disable-pip-version-check --no-warn-script-location -r backend/requirements.txt >/dev/null

pushd frontend >/dev/null
if [[ ! -d node_modules ]]; then
  npm install --no-fund --no-audit >/dev/null
fi
npm run dev -- --host &
FRONTEND_PID=$!
popd >/dev/null

uvicorn backend.app.main:app --reload --reload-dir backend/app &
BACKEND_PID=$!

python worker/run_worker.py &
WORKER_PID=$!

declare -a PIDS=("${BACKEND_PID}" "${FRONTEND_PID}" "${WORKER_PID}")

cleanup() {
  echo "\n[info] Stoppe Dev-Umgebung..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" >/dev/null 2>&1 || true
  done
}

trap cleanup INT TERM EXIT

wait ${BACKEND_PID}
wait ${FRONTEND_PID}
wait ${WORKER_PID}

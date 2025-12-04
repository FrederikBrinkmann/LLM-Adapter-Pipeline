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

if [[ ! -f ticket_frontend/package.json ]]; then
  echo "\n[error] ticket_frontend/package.json fehlt." >&2
  exit 1
fi

ENV_FILE="${ROOT_DIR}/.env"
if [[ -f "${ENV_FILE}" ]]; then
  set -a
  source "${ENV_FILE}"
  set +a
fi

pip install --disable-pip-version-check --no-warn-script-location -r backend/requirements.txt >/dev/null

pushd ticket_frontend >/dev/null
if [[ ! -d node_modules ]]; then
  npm install --no-fund --no-audit >/dev/null
fi
npm run dev -- --host --port 5174 &
UI_PID=$!
popd >/dev/null

uvicorn ticket_service.main:app --reload --port 9000 &
API_PID=$!

declare -a PIDS=("${API_PID}" "${UI_PID}")

cleanup() {
  echo "\n[info] Stoppe Ticket-Stack..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" >/dev/null 2>&1 || true
  done
}

trap cleanup INT TERM EXIT

wait ${API_PID}
wait ${UI_PID}

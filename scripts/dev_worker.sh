#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="${ROOT_DIR}/worker_dev.log"

if [[ ! -d "${ROOT_DIR}/.venv" ]]; then
  echo "[error] .venv not found" >&2
  exit 1
fi

source "${ROOT_DIR}/.venv/bin/activate"

python worker/run_worker.py >>"${LOG_FILE}" 2>&1

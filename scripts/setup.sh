#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "[error] Python-Binary '${PYTHON_BIN}' wurde nicht gefunden. Setze die Variable PYTHON_BIN oder installiere Python." >&2
  exit 1
fi

cd "${ROOT_DIR}"

if [[ ! -d .venv ]]; then
  echo "[info] Lege virtuelle Umgebung an (.venv)."
  "${PYTHON_BIN}" -m venv .venv
else
  echo "[info] Virtuelle Umgebung (.venv) existiert bereits."
fi

source .venv/bin/activate

if [[ -f backend/requirements.txt ]]; then
  echo "[info] Installiere Backend-Abhängigkeiten."
  pip install --upgrade pip >/dev/null
  pip install -r backend/requirements.txt
else
  echo "[warn] backend/requirements.txt wurde nicht gefunden. Überspringe Backend-Installation." >&2
fi

if command -v npm >/dev/null 2>&1; then
  if [[ -d frontend ]]; then
    echo "[info] Installiere Frontend-Abhängigkeiten."
    pushd frontend >/dev/null
    npm install
    popd >/dev/null
  else
    echo "[warn] Frontend-Verzeichnis fehlt. Überspringe npm install." >&2
  fi
else
  echo "[warn] npm wurde nicht gefunden. Installiere Node.js, um das Frontend aufzusetzen." >&2
fi

echo "\n[done] Setup abgeschlossen. Starte die Dev-Server mit './scripts/dev.sh'."

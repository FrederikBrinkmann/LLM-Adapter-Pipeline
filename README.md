# LLM-Adapter-Pipeline
Modellagnostische LLM-Pipeline, die unstrukturierte E-Mails in ein JSON überführt und an eine Ticket-API übergibt. Fokus: strukturierte Ausgaben, Validierung, Mapping, reproduzierbare Evaluation.

## Setup einmalig ausführen
```bash
./scripts/setup.sh
```
Das Skript legt eine `.venv`-Umgebung an, installiert Python-Abhängigkeiten und – sofern `npm` verfügbar ist – auch die Frontend-Pakete.

## Backend lokal starten
1. Virtuelle Umgebung aktivieren (falls nicht durch das Skript erledigt): `source .venv/bin/activate`.
2. FastAPI-Server starten: `uvicorn backend.app.main:app --reload --reload-dir backend/app`.
3. API im Browser öffnen: [http://127.0.0.1:8000](http://127.0.0.1:8000) oder interaktive Doku unter [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

Der Health-Check ist unter `GET /health/` erreichbar und liefert `{ "status": "ok" }`. Der Endpunkt `POST /ingest/` nimmt Freitext entgegen, ruft das ausgewählte LLM auf (standardmäßig ein Mock) und liefert das strukturierte Ergebnis zurück.

## Frontend (Vite + React)
1. Wechsel in das Frontend-Verzeichnis: `cd frontend`.
2. Entwicklungserver starten: `npm run dev` (standardmäßig Port 5173).
3. Optional die Backend-URL anpassen, indem eine `.env` auf Basis der Vorlage `.env.example` angelegt wird.

Das Frontend lädt verfügbare Modelle über `GET /models/`, ermöglicht die Auswahl im UI und schickt den Text samt `model_id` an `/ingest/`. Die Antwort wird inklusive Modelldetails angezeigt.

## Dev-Skript (Backend + Frontend gleichzeitig)
Mit `.venv` und Node installiert kannst du beide Server in einem Terminal starten:

```bash
./scripts/dev.sh
```

Das Skript installiert fehlende Dependencies, startet `npm run dev` sowie `uvicorn` und beendet beides bei `CTRL+C`.

## LLM-Konfiguration
Die verfügbaren Modelle werden über die Settings gesteuert. Standardmäßig stehen zwei Mock-Modelle bereit (rein lokal, ohne Netzwerkanfragen). Eigene Modelle kannst du über Umgebungsvariablen hinterlegen:

```bash
export LLM_PIPELINE_LLM_MODELS='[
  {"model_id": "mock-basic", "display_name": "Mock Model", "provider": "mock"},
  {"model_id": "local-phi3", "display_name": "Phi-3 (lokal)", "provider": "mock"}
]'
export LLM_PIPELINE_LLM_DEFAULT_MODEL="mock-basic"
```

Weitere Provider (z. B. OpenAI, Ollama, HF-Inference) können durch zusätzliche Adapter unter `backend/app/llm/` ergänzt und in der Registry registriert werden. Der Endpoint `GET /models/` liefert allen Clients eine Liste mit `model_id`, Anzeigenamen und Default-Markierung.

## CORS-Konfiguration
Standardmäßig erlaubt das Backend Anfragen von `http://localhost`, `http://localhost:3000`, `http://localhost:5173` sowie den entsprechenden `127.0.0.1`-Varianten. Weitere Origins können über die Umgebungsvariable `LLM_PIPELINE_BACKEND_CORS_ORIGINS` (kommagetrennt) gesetzt werden.

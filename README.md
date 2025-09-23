# LLM-Adapter-Pipeline
Modellagnostische LLM-Pipeline, die unstrukturierte E-Mails in ein JSON überführt und an eine Ticket-API übergibt. Fokus: strukturierte Ausgaben, Validierung, Mapping, reproduzierbare Evaluation.

## Setup einmalig ausführen
```bash
./scripts/setup.sh
```
Das Skript legt eine `.venv`-Umgebung an, installiert Python-Abhängigkeiten und – sofern `npm` verfügbar ist – auch die Frontend-Pakete.

## Services starten
- **Backend API**: `source .venv/bin/activate && uvicorn backend.app.main:app --reload --reload-dir backend/app`
- **Worker** (Job-Queue-Verarbeitung): `source .venv/bin/activate && python worker/run_worker.py`
- **Frontend** (Vite + React): `cd frontend && npm run dev`

Für lokales Arbeiten kannst du alle drei Komponenten gleichzeitig mit einem Befehl starten:
```bash
./scripts/dev.sh
```
Das Skript stellt sicher, dass Abhängigkeiten installiert sind, und stoppt Backend, Worker und Frontend gemeinsam mit `CTRL+C`.

## API-Überblick
- `POST /ingest/` – erstellt einen neuen Job (Text + optional ausgewähltes Modell) und liefert `job_id` sowie den initialen Status (`queued`).
- `GET /jobs/{job_id}` – liefert den aktuellen Status, Timestamps, Fehlermeldungen sowie – nach erfolgreicher Verarbeitung – das strukturierte Ergebnis.
- `POST /jobs/{job_id}/submit` – sendet ein abgeschlossenes Ergebnis an das konfigurierte Ticketsystem und speichert Referenz/Antwort in der Datenbank.
- `GET /models/` – listet alle registrierten LLM-Adapter inklusive Default-Markierung.

Die SQLite-Datenbank liegt standardmäßig unter `data/pipeline.db`. Sie enthält die `jobs`-Tabelle (Status, Modell, Ergebnis, Target-Response). Über die Umgebungsvariable `LLM_PIPELINE_DATABASE_URL` kannst du z. B. auf Postgres wechseln; `LLM_PIPELINE_DATABASE_PATH` steuert die lokale SQLite-Datei.

## LLM-Konfiguration
Die verfügbaren Modelle werden über Umgebungsvariablen bzw. `.env`-Datei gesteuert. In `backend/app/llm/model_registry.py` sind alle bekannten Modelle samt Default-Parametern (Temperatur, Token-Limits etc.) hinterlegt. Aktiviere sie per ID-Liste:
```bash
export LLM_PIPELINE_LLM_MODEL_IDS='["llama3", "gpt-4o-mini"]'
export LLM_PIPELINE_LLM_DEFAULT_MODEL="llama3"
```
Feintuning pro Modell erfolgt über Overrides, z. B. um `max_output_tokens` oder `temperature` anzupassen:
```bash
export LLM_PIPELINE_LLM_MODEL_OVERRIDES='{
  "gpt-4o-mini": {
    "parameters": {"max_output_tokens": 700, "temperature": 0.2}
  }
}'
```
Die Registry lässt sich erweitern, indem du in `model_registry.py` weitere Einträge ergänzt und – falls nötig – einen passenden Adapter unter `backend/app/llm/` implementierst.

## Target-Ticketsystem konfigurieren
Setze folgende Variablen, damit `POST /jobs/{job_id}/submit` deine Dummy- oder Echt-API anruft:
```bash
export LLM_PIPELINE_TARGET_API_BASE_URL="http://127.0.0.1:8500"   # Basis-URL deines Ticket-Backends
export LLM_PIPELINE_TARGET_API_TICKETS_PATH="/tickets"           # optionaler Pfad
export LLM_PIPELINE_TARGET_API_TOKEN="<optional-bearer-token>"
export LLM_PIPELINE_TARGET_TIMEOUT_SECONDS=10
```
Der Aufruf erfolgt via HTTPX, Antwort und Referenz werden im Job gespeichert (Felder `target_status`, `target_reference`, `target_response`). Ohne konfigurierte URL antwortet der Endpoint mit HTTP 503.

## Frontend
Das React-Frontend lädt beim Start `GET /models/`, erlaubt die Modellwahl und erstellt anschließend einen Job. Status und Ergebnis werden regelmäßig per Polling über `GET /jobs/{job_id}` aktualisiert. Nach erfolgreicher Verarbeitung lässt sich das Ergebnis per Button an das Ticketsystem übermitteln.

## CORS-Konfiguration
Standardmäßig erlaubt das Backend Anfragen von `http://localhost`, `http://localhost:3000`, `http://localhost:5173` sowie den entsprechenden `127.0.0.1`-Varianten. Weitere Origins können über `LLM_PIPELINE_BACKEND_CORS_ORIGINS` (kommagetrennt) gesetzt werden.

## OpenAI-Kosten (nur zum Vergleich)
Falls du zum Testen ein OpenAI-Modell einbinden möchtest, beachte die tokenbasierte Abrechnung (Stand Juli 2024):

- GPT-4o: ca. 5 USD pro 1 Mio. Eingabe-Tokens und 15 USD pro 1 Mio. Ausgabe-Tokens (≈ 0,02 USD pro 1.000 Tokens insgesamt).
- GPT-4o mini: ca. 0,15 USD pro 1 Mio. Eingabe-Tokens und 0,60 USD pro 1 Mio. Ausgabe-Tokens (≈ 0,004 USD pro 1.000 Tokens).

Für ein paar Testläufe reicht ein kleines Guthaben (z. B. 5–10 USD). Preise können sich ändern – siehe https://openai.com/pricing für aktuelle Infos.

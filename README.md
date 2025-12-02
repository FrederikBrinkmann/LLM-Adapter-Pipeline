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
- **Ticket-Demo-Service** (separater Port 9000): `source .venv/bin/activate && uvicorn ticket_service.main:app --reload --port 9000`
- **Pipeline-Frontend** (LLM-Steuerung): `cd frontend && npm run dev`
- **Ticket-Frontend** (eigene Domäne/Port): `cd ticket_frontend && npm run dev`

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
Setze folgende Variablen, damit `POST /jobs/{job_id}/submit` deine Dummy- oder Echt-API anruft (für den mitgelieferten Ticket-Demo-Service z. B. `http://127.0.0.1:9000`):
```bash
export LLM_PIPELINE_TARGET_API_BASE_URL="http://127.0.0.1:9000"   # Basis-URL deines Ticket-Backends
export LLM_PIPELINE_TARGET_API_TICKETS_PATH="/tickets"           # optionaler Pfad
export LLM_PIPELINE_TARGET_API_TOKEN="<optional-bearer-token>"
export LLM_PIPELINE_TARGET_TIMEOUT_SECONDS=10
```
Der Aufruf erfolgt via HTTPX, Antwort und Referenz werden im Job gespeichert (Felder `target_status`, `target_reference`, `target_response`). Ohne konfigurierte URL antwortet der Endpoint mit HTTP 503.

## Ticket-Demo-Service
Unter `ticket_service/` liegt ein kleines FastAPI-Projekt, das Tickets in `data/tickets_store.json` persistiert und typische Felder (Status, Priorität, Action Items, fehlende Angaben, Referenz zum Pipeline-Job) verwaltet. Der Service stellt folgende Endpunkte bereit:

- `GET /tickets` – Liste aller Tickets (absteigend sortiert)
- `POST /tickets` – neues Ticket anlegen; wird vom Frontend und vom `/jobs/{id}/submit`-Endpoint benutzt
- `GET /tickets/{id}` – Details zu einem Ticket
- `PATCH /tickets/{id}` – Status, Priorität, Beschreibung oder Action Items aktualisieren

Der Service läuft standardmäßig auf Port 9000 und ist komplett vom Haupt-Backend getrennt. Datenspeicherung erfolgt in einer eigenen JSON-Datei, sodass du gefahrlos experimentieren oder die Daten bei Bedarf löschen kannst.

## Frontend
Das React-Frontend unter `frontend/` lädt beim Start `GET /models/`, erlaubt die Modellwahl und erstellt anschließend einen Job. Status und Ergebnis werden regelmäßig per Polling über `GET /jobs/{job_id}` aktualisiert. Nach erfolgreicher Verarbeitung lässt sich das Ergebnis per Button an das Ticketsystem übermitteln. Die Oberfläche zeigt einen Link zum separaten Ticket-Dashboard; passe die Ziel-URL via `VITE_TICKETS_UI_URL` an (Default: `http://127.0.0.1:5174`).

Unter `ticket_frontend/` liegt das dedizierte Ticket-Dashboard (eigene Vite-App, Standardport 5174). Es spricht direkt mit dem Ticket-Service (Basis über `VITE_TICKETS_API_BASE_URL`, Default `http://127.0.0.1:9000`), zeigt alle Tickets inklusive Action Items und fehlender Felder an und erlaubt Status- sowie Formularupdates über die API. Beide Frontends sind somit entkoppelt und lassen sich auf unterschiedlichen Domains/Ports betreiben.

## CORS-Konfiguration
Standardmäßig erlaubt das Backend Anfragen von `http://localhost`, `http://localhost:3000`, `http://localhost:5173` sowie den entsprechenden `127.0.0.1`-Varianten. Weitere Origins können über `LLM_PIPELINE_BACKEND_CORS_ORIGINS` (kommagetrennt) gesetzt werden.

## OpenAI-Kosten (nur zum Vergleich)
Falls du zum Testen ein OpenAI-Modell einbinden möchtest, beachte die tokenbasierte Abrechnung (Stand Juli 2024):

- GPT-4o: ca. 5 USD pro 1 Mio. Eingabe-Tokens und 15 USD pro 1 Mio. Ausgabe-Tokens (≈ 0,02 USD pro 1.000 Tokens insgesamt).
- GPT-4o mini: ca. 0,15 USD pro 1 Mio. Eingabe-Tokens und 0,60 USD pro 1 Mio. Ausgabe-Tokens (≈ 0,004 USD pro 1.000 Tokens).

Für ein paar Testläufe reicht ein kleines Guthaben (z. B. 5–10 USD). Preise können sich ändern – siehe https://openai.com/pricing für aktuelle Infos.

## Evaluation: Synthetic E-Mails
Unter `scripts/generate_synthetic_emails.py` liegt ein Generator für reproduzierbare Testdaten. Der Standardaufruf

```bash
python scripts/generate_synthetic_emails.py
```

legt 200 fiktive Versicherungsmails in `data/emails/synthetic_insurance_emails.jsonl` ab und schreibt Meta-Informationen nach `data/emails/manifest.json`. Mit Zusatzoptionen lassen sich u. a. Anzahl, Seed sowie eine automatische Weiterleitung an die API anpassen:

```bash
python scripts/generate_synthetic_emails.py \
  --count 50 \
  --seed 123 \
  --ingest-api http://localhost:8000/ingest/ \
  --model-id llama3
```

Die Option `--split` erzeugt zusätzlich einzelne `.txt`-Dateien je E-Mail (z. B. für manuelle Reviews). In `ingest_results.json` werden Rückmeldungen der Pipeline gespeichert, sobald `--ingest-api` gesetzt wurde.

## Ticket-Overview & Export
Für einen schnellen Überblick über die verarbeiteten Jobs kannst du

```bash
python scripts/export_pipeline_results.py
```

ausführen. Das Skript liest `data/pipeline.db`, erstellt eine CSV (`evaluation/tickets_overview.csv`) sowie eine Zusammenfassung (`evaluation/tickets_summary.json`). Mit `--submit` werden alle fertigen Jobs ohne fehlende Felder automatisch via `POST /jobs/{id}/submit` an das konfigurierte Ticket-Backend weitergereicht (Standard: `http://localhost:8000`).

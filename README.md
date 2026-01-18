# LLM-Adapter-Pipeline
Modellagnostische LLM-Pipeline, die unstrukturierte Versicherungs-E-Mails in ein JSON überführt und an eine Ticket-API übergibt. Fokus: strukturierte Ausgaben, Validierung, Mapping, reproduzierbare Evaluation.

## Setup (einmalig)
- `./scripts/setup.sh` legt `.venv` an, installiert Python-Dependencies und Node-Pakete (falls npm vorhanden).
- `.env` optional füllen (z. B. API-Keys, Model-Liste, Target-URL).

## Start: Pipeline-Stack (Backend + Worker + Pipeline-Frontend)
- Alles auf einmal: `./scripts/dev.sh` (Ports: API 8000, Frontend 5173). Stoppen mit `CTRL+C`.
- Manuell:
  - `source .venv/bin/activate && uvicorn backend.app.main:app --reload --reload-dir backend/app`
  - `source .venv/bin/activate && python worker/run_worker.py`
  - `cd frontend && npm run dev -- --host --port 5173`

## Start: Ticket-Stack (Ticket-Service + Ticket-Frontend)
- Alles auf einmal: `./scripts/dev_tickets.sh` (Ports: Ticket-Service 9000, Ticket-UI 5174). Stoppen mit `CTRL+C`.
- Manuell:
  - `source .venv/bin/activate && uvicorn ticket_service.main:app --reload --port 9000`
  - `cd ticket_frontend && npm run dev -- --host --port 5174`

## E-Mail-Ingest (optional)
- Script: `python scripts/mail_ingest.py` pollt ein IMAP-Postfach und legt Mails via `POST /ingest/` als Jobs an.
- Env-Variablen (Beispiel in `.env`):
  - `MAIL_IMAP_HOST`, `MAIL_IMAP_USER`, `MAIL_IMAP_PASSWORD` (erforderlich)
  - `MAIL_IMAP_PORT=993`, `MAIL_IMAP_FOLDER=INBOX`, `MAIL_POLL_INTERVAL=30`
  - `MAIL_API_BASE=http://127.0.0.1:8000`, `MAIL_MODEL_ID=<optional>`
-.env-Beispiel:
```bash
MAIL_IMAP_HOST=imap.example.com
MAIL_IMAP_USER=support@example.com
MAIL_IMAP_PASSWORD=...
MAIL_IMAP_FOLDER=INBOX
MAIL_API_BASE=http://127.0.0.1:8000
MAIL_POLL_INTERVAL=30
MAIL_MODEL_ID=gpt-4o-mini
```

## Auto-Submit (optional)
- `LLM_PIPELINE_AUTO_SUBMIT_ENABLED=true` schaltet automatisches Submit fertig verarbeiteter Jobs ein (Worker ruft `/jobs/{id}/submit` auf).
- `LLM_PIPELINE_AUTO_SUBMIT_ALLOW_MISSING_FIELDS` (default false) steuert, ob Jobs mit `missing_fields` trotzdem submitted werden.
- `LLM_PIPELINE_AUTO_SUBMIT_API_BASE` (default `http://127.0.0.1:8000`) legt fest, wohin der Worker den Submit-Call sendet.
- Voraussetzung: Ticket-Target konfiguriert (`LLM_PIPELINE_TARGET_API_BASE_URL`), sonst wird Submit übersprungen.

## Datenablage
- Tickets: `data/tickets_store.json` (leer ausgeliefert, keine Auto-Seeds). Datei löschen, um den Ticket-Bestand zu resetten.
- Pipeline-Jobs: `data/pipeline.db` (SQLite, wird beim Start neu angelegt, falls gelöscht).

## API-Überblick
- `POST /ingest/` – erstellt einen neuen Job (Text + optional ausgewähltes Modell) und liefert `job_id` sowie den initialen Status (`queued`).
- `GET /jobs/{job_id}` – liefert den aktuellen Status, Timestamps, Fehlermeldungen sowie – nach erfolgreicher Verarbeitung – das strukturierte Ergebnis.
- `POST /jobs/{job_id}/submit` – sendet ein abgeschlossenes Ergebnis an das konfigurierte Ticketsystem und speichert Referenz/Antwort in der Datenbank.
- `GET /models/` – listet alle registrierten LLM-Adapter inklusive Default-Markierung.

Die SQLite-Datenbank liegt standardmäßig unter `data/pipeline.db`. Sie enthält die `jobs`-Tabelle (Status, Modell, Ergebnis, Target-Response). Über die Umgebungsvariable `LLM_PIPELINE_DATABASE_URL` kannst du z. B. auf Postgres wechseln; `LLM_PIPELINE_DATABASE_PATH` steuert die lokale SQLite-Datei.

## LLM-Konfiguration
Die verfügbaren Modelle werden über Umgebungsvariablen bzw. `.env`-Datei gesteuert. In `backend/app/llm/model_config.py` sind alle bekannten Modelle hinterlegt, während die providerweiten Default-Parameter (Temperatur, Token-Limits etc.) in `backend/app/llm/model_spec.py` zentral gepflegt werden. Aktiviere sie per ID-Liste:
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
Die Registry lässt sich erweitern, indem du in `model_config.py` weitere Einträge ergänzt und – falls nötig – einen passenden Adapter unter `backend/app/llm/` implementierst.

## Target-Ticketsystem konfigurieren
Setze folgende Variablen, damit `POST /jobs/{job_id}/submit` dein Ticket-Backend (Standard: interner Ticket-Service auf Port 9000) anspricht:
```bash
export LLM_PIPELINE_TARGET_API_BASE_URL="http://127.0.0.1:9000"   # Basis-URL deines Ticket-Backends
export LLM_PIPELINE_TARGET_API_TICKETS_PATH="/tickets"           # optionaler Pfad
export LLM_PIPELINE_TARGET_API_TOKEN="<optional-bearer-token>"
export LLM_PIPELINE_TARGET_TIMEOUT_SECONDS=10
```
Der Aufruf erfolgt via HTTPX, Antwort und Referenz werden im Job gespeichert (Felder `target_status`, `target_reference`, `target_response`). Ohne konfigurierte URL antwortet der Endpoint mit HTTP 503.

## Ticket-Service (Insurance Claims)
Unter `ticket_service/` liegt ein kleines FastAPI-Projekt, das Tickets in `data/tickets_store.json` persistiert und typische Felder für Versicherungsfälle (Status, Priorität, Action Items, fehlende Angaben, Referenz zum Pipeline-Job) verwaltet. Der Service stellt folgende Endpunkte bereit:

- `GET /tickets` – Liste aller Tickets (absteigend sortiert)
- `POST /tickets` – neues Ticket anlegen; wird vom Frontend und vom `/jobs/{id}/submit`-Endpoint benutzt
- `GET /tickets/{id}` – Details zu einem Ticket
- `PATCH /tickets/{id}` – Status, Priorität, Beschreibung oder Action Items aktualisieren

Der Service läuft standardmäßig auf Port 9000 und ist komplett vom Haupt-Backend getrennt. Datenspeicherung erfolgt in einer eigenen JSON-Datei, sodass du gefahrlos experimentieren oder die Daten bei Bedarf löschen kannst.

## Frontends
- Pipeline-Frontend (`frontend/`, Port 5173): Modelle wählen, Jobs anlegen, Status pollend anzeigen, Abschluss an Ticketsystem senden. Link zum Ticket-Dashboard per `VITE_TICKETS_UI_URL` konfigurierbar (Default `http://127.0.0.1:5174`).
- Ticket-Frontend (`ticket_frontend/`, Port 5174): Direkt gegen den Ticket-Service (`VITE_TICKETS_API_BASE_URL`, Default `http://127.0.0.1:9000`), zeigt/ändert Tickets und Action Items.

## CORS-Konfiguration
Standardmäßig erlaubt das Backend Anfragen von `http://localhost`, `http://localhost:3000`, `http://localhost:5173` sowie den entsprechenden `127.0.0.1`-Varianten. Weitere Origins können über `LLM_PIPELINE_BACKEND_CORS_ORIGINS` (kommagetrennt) gesetzt werden.

## LLM-Ausgabe (Insurance Ticket-Schema)
Der LLM-Adapter soll JSON mit folgenden Schlüsseln liefern:
- `ticket_id` (Pflicht, String)
- `summary` (Pflicht), optional `subject`
- `claimant_name`, `claimant_email`, `claimant_phone` (optional)
- `description` (optional)
- `priority`: `low|medium|high|urgent` (Pflicht)
- `policy_number` (optional)
- `claim_type`: `damage|medical|liability|death|other` (Pflicht)
- `claim_date`, `incident_date` (optional, YYYY-MM-DD)
- `incident_location` (optional)
- `claim_amount` (optional, Zahl)
- `missing_fields`: nur echte Lücken (z. B. `policy_number`, `incident_date`)
- `action_items`: konkrete nächste Schritte (Strings oder Objekte)
- `next_steps` (Pflicht, String)
- `created_timestamp` (Pflicht, ISO-8601)

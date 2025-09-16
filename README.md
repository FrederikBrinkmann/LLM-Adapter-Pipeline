# LLM-Adapter-Pipeline
Modellagnostische LLM-Pipeline, die unstrukturierte E-Mails in ein JSON überführt und an eine Ticket-API übergibt. Fokus: strukturierte Ausgaben, Validierung, Mapping, reproduzierbare Evaluation.

## Backend lokal starten
1. Virtuelle Umgebung anlegen und aktivieren (z. B. `python -m venv .venv && source .venv/bin/activate`).
2. Abhängigkeiten installieren: `pip install -r backend/requirements.txt`.
3. FastAPI-Server starten: `uvicorn backend.app.main:app --reload --reload-dir backend/app`.
4. API im Browser öffnen: [http://127.0.0.1:8000](http://127.0.0.1:8000) oder interaktive Doku unter [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

Der Health-Check ist unter `GET /health/` erreichbar und liefert `{ "status": "ok" }`. Der Beispiel-Endpunkt `POST /ingest/` nimmt Freitext entgegen und beantwortet die Anfrage mit einer Echo-Antwort.

## Frontend (Vite + React)
1. Wechsel in das Frontend-Verzeichnis: `cd frontend`.
2. Abhängigkeiten installieren: `npm install`.
3. Entwicklungserver starten: `npm run dev` (standardmäßig Port 5173).
4. Optional die Backend-URL anpassen, indem eine `.env` auf Basis der Vorlage `.env.example` angelegt wird.

Das Frontend ruft das FastAPI-Backend über `/ingest/` auf und zeigt Antwort oder Fehlerzustand an.

## Dev-Skript (Backend + Frontend gleichzeitig)
Mit `.venv` und Node installiert kannst du beide Server in einem Terminal starten:

```bash
./scripts/dev.sh
```

Das Skript installiert fehlende Dependencies, startet `npm run dev` sowie `uvicorn` und beendet beides bei `CTRL+C`.

## CORS-Konfiguration
Standardmäßig erlaubt das Backend Anfragen von `http://localhost`, `http://localhost:3000`, `http://localhost:5173` sowie den entsprechenden `127.0.0.1`-Varianten. Weitere Origins können über die Umgebungsvariable `LLM_PIPELINE_BACKEND_CORS_ORIGINS` (kommagetrennt) gesetzt werden.

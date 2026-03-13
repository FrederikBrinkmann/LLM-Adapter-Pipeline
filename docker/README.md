# Docker Deployment

Dieses Projekt kann vollständig mit Docker ausgeführt werden.

## Voraussetzungen

- Docker & Docker Compose
- OpenAI API Key (für GPT-Modelle)
- Optional: Ollama (lokal oder im Container für lokale Modelle)

## Quick Start

### 1. Environment-Variablen setzen

```bash
cp .env.docker.example .env
# Dann .env editieren und OPENAI_API_KEY eintragen
```

### 2. Produktions-Modus (gebaut)

```bash
# Alle Services starten
docker-compose up -d

# Mit Ollama (für lokale Modelle)
docker-compose --profile with-ollama up -d
```

### 3. Development-Modus (Hot-Reload)

```bash
docker-compose -f docker-compose.dev.yml up
```

## Services

| Service | Port | Beschreibung |
|---------|------|--------------|
| Backend | 8000 | FastAPI Backend API |
| Worker | - | Job-Verarbeitung (kein Port) |
| Ticket Service | 9000 | Ticket-Management API |
| Frontend | 5173 | Pipeline UI (React) |
| Ticket Frontend | 5174 | Ticket Dashboard (React) |
| Ollama | 11434 | Lokale LLMs (optional) |

## URLs nach Start

- **Pipeline UI**: http://localhost:5173
- **Ticket Dashboard**: http://localhost:5174
- **Backend API**: http://localhost:8000
- **Ticket API**: http://localhost:9000
- **API Docs**: http://localhost:8000/docs

## Einzelne Services

```bash
# Nur Backend + Worker
docker-compose up backend worker -d

# Nur Frontends
docker-compose up frontend ticket_frontend -d

# Logs eines Services
docker-compose logs -f backend
```

## Ollama mit lokalen Modellen

```bash
# Mit Ollama-Profil starten
docker-compose --profile with-ollama up -d

# Modell herunterladen (im Container)
docker exec -it llm-pipeline-ollama ollama pull llama3:latest
docker exec -it llm-pipeline-ollama ollama pull qwen3:8b
```

Falls Ollama bereits lokal läuft, nutzt der Worker automatisch `host.docker.internal:11434`.

## Daten & Volumes

- `backend-data`: SQLite DB für Jobs
- `ticket-data`: JSON-Store für Tickets
- `ollama-data`: Ollama Modelle (falls im Container)

### Daten löschen

```bash
docker-compose down -v  # Löscht auch Volumes
```

## Troubleshooting

### Container-Status prüfen

```bash
docker-compose ps
docker-compose logs backend
```

### Rebuild nach Code-Änderungen

```bash
docker-compose build --no-cache
docker-compose up -d
```

### Health Checks

```bash
curl http://localhost:8000/health
curl http://localhost:9000/health
```

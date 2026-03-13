# Worker Service
FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY backend/ ./backend/
COPY worker/ ./worker/

# Data directory
RUN mkdir -p /app/data

ENV PYTHONPATH=/app
ENV LLM_PIPELINE_DATABASE_URL=sqlite:///./data/pipeline.db

CMD ["python", "worker/run_worker.py"]

# Ticket Service (FastAPI)
FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies - ticket_service nutzt gleiche deps wie backend
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY ticket_service/ ./ticket_service/

# Data directory
RUN mkdir -p /app/data

ENV PYTHONPATH=/app

EXPOSE 9000

CMD ["uvicorn", "ticket_service.main:app", "--host", "0.0.0.0", "--port", "9000"]

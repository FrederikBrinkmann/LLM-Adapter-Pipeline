FROM python:3.12-slim

WORKDIR /app

# Install only what's needed for mail_ingest
RUN pip install --no-cache-dir httpx

# Copy the mail ingest script
COPY scripts/mail_ingest.py ./scripts/

CMD ["python", "scripts/mail_ingest.py"]

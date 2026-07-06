FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir psycopg2-binary pymongo

WORKDIR /app
COPY scripts/sync-contingencia.py /app/sync-contingencia.py

CMD ["python", "/app/sync-contingencia.py", "daemon"]

FROM python:3.11-slim
WORKDIR /app
COPY shared/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY shared/coop_shared /app/coop_shared
ENV PYTHONPATH=/app
COPY services/sync/app /app/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]

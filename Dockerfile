# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Keeps Python output unbuffered so logs appear immediately
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (cached layer — only re-runs when requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Persistent data goes in /data — mount a volume here to keep it across restarts
RUN mkdir -p /data
ENV CONFIG_PATH=/data/config.json
ENV DB_PATH=/data/emails.db

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

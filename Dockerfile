FROM mcr.microsoft.com/playwright/python:v1.49.1-noble
WORKDIR /app

# Python deps
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# App code (output/ is created at runtime; mount a volume for persistence)
COPY backend ./backend

ENV PYTHONUNBUFFERED=1
# Railway injects $PORT; default to 8000 locally.
CMD ["sh", "-c", "uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

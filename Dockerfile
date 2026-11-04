# Stage 1: Build Frontend Assets
FROM node:20-alpine AS frontend-builder
WORKDIR /web
COPY web/package.json web/package-lock.json* ./
RUN npm install
COPY web/ ./
RUN npm run build

# Stage 2: Python Backend Runtime
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/backend:/app

WORKDIR /app

# Install system dependencies needed for psycopg2, curl, and image libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --upgrade pip && pip install -r backend/requirements.txt

# Copy backend application code and compiled frontend
COPY backend/ ./backend/
COPY --from=frontend-builder /web/dist ./web/dist
COPY render.yaml ./

WORKDIR /app/backend

# Render dynamically sets $PORT (usually 10000)
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python scripts/seed_medications.py && python scripts/seed_users.py && python scripts/create_user.py && uvicorn prescripto.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]

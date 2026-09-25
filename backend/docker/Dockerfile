FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies needed for psycopg2 and image libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY prescripto/ ./prescripto/
COPY scripts/ ./scripts/
COPY alembic.ini .

# Expose API port
EXPOSE 8000

CMD ["uvicorn", "prescripto.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

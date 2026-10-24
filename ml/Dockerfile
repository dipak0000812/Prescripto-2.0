FROM python:3.12-slim

WORKDIR /service

# System deps for PaddleOCR (libGL etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 libsm6 libxrender1 libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Install runtime dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    # PaddlePaddle CPU build — override for GPU in production deployment
    && pip install --no-cache-dir paddlepaddle>=2.6.1 paddleocr>=2.8.1

# Copy service source
COPY . .

ENV ML_PORT=8001 \
    ML_DEVICE=cpu \
    ML_MODEL_NAME=PP-OCRv6 \
    ML_MODEL_VERSION=6.0.0 \
    LOG_LEVEL=INFO

EXPOSE 8001

CMD ["uvicorn", "ml.app.main:app", "--host", "0.0.0.0", "--port", "8001"]

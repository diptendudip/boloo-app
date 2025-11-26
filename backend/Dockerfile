# Multi-stage Docker build for Boloo Backend MVP - Production Ready
FROM python:3.11-slim as base

# Install system dependencies for PostGIS, audio processing, and ML libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libgdal-dev \
    gdal-bin \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
# This layer will be cached unless requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/uploads /app/data

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    WEB_CONCURRENCY=2 \
    WORKERS=2 \
    WORKER_CLASS=uvicorn.workers.UvicornWorker \
    MAX_REQUESTS=1000 \
    MAX_REQUESTS_JITTER=50 \
    TIMEOUT=120 \
    GRACEFUL_TIMEOUT=30 \
    KEEP_ALIVE=5

# Expose port
EXPOSE 8000

# Health check - optimized for production
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with Gunicorn + Uvicorn workers for production
# 2 workers for 100 users (scalable to 4 workers for B2 tier - 3.5GB RAM)
# --max-requests enables worker recycling to prevent memory leaks
# --preload loads app before forking for better memory efficiency
CMD ["gunicorn", "app.main:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "50", \
     "--preload", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]

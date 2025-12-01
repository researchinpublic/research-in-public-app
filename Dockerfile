FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app

WORKDIR ${APP_HOME}

# Install system dependencies (needed for FAISS and some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code (excluding unnecessary files via .dockerignore)
COPY . .

# Ensure data directory exists (for dummy_struggles.json if needed)
RUN mkdir -p /app/data

# Cloud Run sets PORT env var automatically, use it if available, default to 8080
EXPOSE 8080

# Use PORT environment variable (Cloud Run provides this)
# Use sh -c to properly expand environment variable
CMD sh -c "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}"




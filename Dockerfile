# Root Dockerfile for Railway deployment (build context: project root)
# The services/backend/Dockerfile is used for docker-compose (context: services/backend/).
# Multi-stage build for optimized image size.

# ── Stage 1: Builder ────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/backend/requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install CPU-only torch first so pip doesn't pull the 1.7 GB CUDA wheel
# when it processes torch from requirements.txt (resolved as already satisfied).
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /root/nltk_data /root/nltk_data

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy backend source (root .dockerignore excludes data/, app/notebooks/, tests/, etc.)
COPY services/backend/ .

RUN mkdir -p temp data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/ping || exit 1

# Railway injects $PORT; default to 8000 for local use
CMD uvicorn app.api.app:app --host 0.0.0.0 --port ${PORT:-8000}

# ── Build stage ────────────────────────────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Use CPU-only requirements to avoid pulling 3+ GB of CUDA libraries
COPY requirements.docker.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.docker.txt

# ── Runtime stage ──────────────────────────────────────────────────────────────
FROM python:3.10-slim AS runtime

# Minimal runtime system libs for OpenCV headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libgl1 libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /install /usr/local

COPY backend/   ./backend/
COPY frontend/  ./frontend/
COPY best.pt    ./

RUN mkdir -p backend/outputs

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

ENV HOST=0.0.0.0 \
    PORT=8000 \
    WORKERS=1

CMD ["sh", "-c", "cd backend && python -m uvicorn main:app --host $HOST --port $PORT --workers $WORKERS"]

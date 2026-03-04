# ── Build stage ────────────────────────────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /app

# Install build tools needed by some packages (e.g. numpy, scipy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ──────────────────────────────────────────────────────────────
FROM python:3.10-slim AS runtime

# Runtime system libs needed by OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libgl1 libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY backend/   ./backend/
COPY frontend/  ./frontend/
COPY best.pt    ./

# Output videos are written here at runtime — expose as a volume
RUN mkdir -p backend/outputs

# Non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Uvicorn config via environment (overridable at deploy time)
ENV HOST=0.0.0.0 \
    PORT=8000 \
    WORKERS=1

CMD ["sh", "-c", "cd backend && python -m uvicorn main:app --host $HOST --port $PORT --workers $WORKERS"]

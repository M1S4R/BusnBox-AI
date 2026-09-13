# ============================================================
# BusNBox AI — Standalone Production Dockerfile
# ============================================================
# Independent FastAPI AI module.
# Does NOT require MariaDB or mock company inventory container.
# ============================================================

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/app /app/app

# Default environment variables
ENV HOST=0.0.0.0
ENV PORT=8000
ENV AI_PROVIDER=gemini
ENV INVENTORY_PROVIDER=mock
ENV PYTHONPATH=/app

EXPOSE 8000

# Healthcheck probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Production startup
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

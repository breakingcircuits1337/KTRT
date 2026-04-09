# ── Stage 1: build ───────────────────────────────────────────────────────────
# Compile native extensions (trafilatura, lxml, cryptography) then discard
# build toolchain so the final image stays small and has a reduced attack surface.
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY pyproject.toml .
COPY app/ ./app/

# Non-editable install into an isolated prefix so we can copy it cleanly
RUN pip install --no-cache-dir --prefix=/install .


# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim

# Only the shared libraries needed at runtime (no compilers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local
# Copy application source
COPY --from=builder /build/app ./app/

ENV PYTHONUNBUFFERED=1
ENV LOG_FORMAT=json

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

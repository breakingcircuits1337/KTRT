# ── Stage 1: build ───────────────────────────────────────────────────────────
# lxml, cryptography and trafilatura all ship self-contained manylinux wheels
# for cp311, so no system compiler or -dev headers are needed. Avoiding apt
# entirely also sidesteps slow/unreliable Debian mirror fetches.
FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml .
COPY app/ ./app/

# Prefer prebuilt wheels; install into an isolated prefix we can copy cleanly.
# A BuildKit cache mount persists downloaded wheels across builds, and the long
# timeout/retries tolerate a slow uplink.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefer-binary --timeout 180 --retries 15 --prefix=/install .


# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder stage (wheels bundle libxml2/libxslt).
COPY --from=builder /install /usr/local
# Copy application source
COPY --from=builder /build/app ./app/

ENV PYTHONUNBUFFERED=1
ENV LOG_FORMAT=json

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

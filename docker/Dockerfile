FROM python:3.11-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN addgroup --system nebula && adduser --system --ingroup nebula nebula

COPY --from=builder /install /usr/local

COPY backend/app /app/app
COPY backend/vector /app/vector
COPY backend/static /app/static
COPY docker/entrypoint.sh /app/entrypoint.sh
COPY docker/scheduler-entrypoint.sh /app/scheduler-entrypoint.sh

RUN mkdir -p /app/storage/uploads /app/storage/cache /app/storage/vector \
             /app/storage/indexes /app/storage/exports /app/logs \
    && chmod +x /app/entrypoint.sh /app/scheduler-entrypoint.sh \
    && chown -R nebula:nebula /app

USER nebula

EXPOSE 8000/tcp

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["/app/entrypoint.sh"]

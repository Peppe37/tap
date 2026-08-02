# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# lxml/bs4 need libxml2/libxslt at build time; libpq is required by asyncpg's dependency chain
# at runtime for psycopg-free environments as well as general Postgres tooling.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libxml2-dev \
        libxslt1-dev \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic

RUN pip install --no-cache-dir .

RUN useradd --create-home --shell /bin/bash tap
USER tap

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

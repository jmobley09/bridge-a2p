#!/usr/bin/env bash
set -euo pipefail

alembic upgrade head

exec gunicorn \
  --workers "${WEB_CONCURRENCY:-2}" \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind "0.0.0.0:${PORT:-8000}" \
  app.main:app

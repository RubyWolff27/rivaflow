#!/bin/bash
# Start script for RivaFlow on Render

set -e  # Exit on error

# Activate virtualenv if running on Render
if [ -f /opt/render/project/src/.venv/bin/activate ]; then
    . /opt/render/project/src/.venv/bin/activate
fi

echo "==> Starting RivaFlow deployment..."
echo "==> Python version: $(python --version)"
echo "==> Environment: ${ENV:-development}"

# Validate environment variables
if [ -z "$SECRET_KEY" ]; then
    echo "ERROR: SECRET_KEY environment variable is not set"
    exit 1
fi

if [ -z "$PORT" ]; then
    echo "WARNING: PORT environment variable not set, using default 8000"
    export PORT=8000
fi

echo "==> PORT: $PORT"

# Run migrations (creates schema_migrations table if needed, then applies pending)
echo "==> Running database migrations..."
python rivaflow/db/migrate.py

# Start gunicorn with uvicorn workers
echo "==> Starting gunicorn on 0.0.0.0:${PORT}..."
exec python -m gunicorn rivaflow.api.main:app \
    -w 2 \
    -k uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:${PORT}" \
    --log-level info \
    --timeout 120 \
    --graceful-timeout 30

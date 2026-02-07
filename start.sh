#!/bin/bash
# Start script for RivaFlow on Render

set -e  # Exit on error

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

# Initialize database
echo "==> Initializing database..."
python -c "
from rivaflow.db.database import init_db
init_db()
print('Database initialized successfully')
"

# Run migrations
echo "==> Running database migrations..."
python rivaflow/db/migrate.py

# Start uvicorn server
echo "==> Starting uvicorn server on 0.0.0.0:${PORT}..."
exec uvicorn rivaflow.api.main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --log-level info

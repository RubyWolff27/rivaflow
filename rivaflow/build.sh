#!/bin/bash
# Render build script for RivaFlow

set -e  # Exit on error

echo "==> RivaFlow Build Script v0.2.0-FIXED (no AI deps, non-editable install)"
echo "==> Git commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
if [ -f rivaflow/VERSION ]; then
    echo "==> Package version: $(cat rivaflow/VERSION)"
fi

echo "==> Installing Python dependencies..."
pip install --upgrade pip setuptools wheel

echo "==> Installing RivaFlow package..."
pip install .

echo "==> Initializing database..."
python -c "from rivaflow.db.database import init_db; init_db()"

echo "==> Running PostgreSQL migrations..."
python rivaflow/db/migrate.py || echo "Migration script not needed for initialization"

echo "==> Build complete!"

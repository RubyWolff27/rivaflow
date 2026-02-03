#!/bin/bash
# Render build script for RivaFlow

set -e  # Exit on error

echo "==> Installing Python dependencies..."
pip install --upgrade pip setuptools wheel

echo "==> Installing RivaFlow package..."
pip install -e .

echo "==> Initializing database..."
python -c "from rivaflow.db.database import init_db; init_db()"

echo "==> Running PostgreSQL migrations..."
python rivaflow/db/migrate.py || echo "Migration script not needed for initialization"

echo "==> Build complete!"

#!/bin/bash
set -e

echo "========================================================================"
echo "RivaFlow Build v0.2.0 - NO AI DEPENDENCIES"
echo "Commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
echo "========================================================================"

# Verify we have the VERSION file (proves we're using fresh code)
if [ -f rivaflow/VERSION ]; then
    echo "✓ VERSION file found: $(cat rivaflow/VERSION)"
else
    echo "✗ ERROR: VERSION file not found - using STALE CACHED CODE!"
    echo "This build should FAIL to alert you to the cache problem."
    exit 1
fi

echo "==> Upgrading pip..."
pip install --upgrade pip setuptools wheel

echo "==> Installing RivaFlow (non-editable)..."
pip install .

echo "==> Checking for forbidden AI dependencies..."
python verify_no_ai_deps.py

echo "==> Initializing database..."
python -c "from rivaflow.db.database import init_db; init_db()"

echo "========================================================================"
echo "✓ Build complete - v0.2.0"
echo "========================================================================"

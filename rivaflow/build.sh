#!/usr/bin/env bash
set -euo pipefail

# Ensure we're in the repository root
cd "$(dirname "$0")"

echo "========================================================================"
echo "RivaFlow Build v0.2.0 - NO AI DEPENDENCIES"
echo "Working directory: $(pwd)"
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

echo ""
echo "==> Upgrading pip..."
pip install --upgrade pip setuptools wheel

echo ""
echo "==> Installing RivaFlow (non-editable)..."
pip install .

echo ""
echo "==> Checking for forbidden AI dependencies..."
python verify_no_ai_deps.py

echo ""
echo "==> Building frontend..."
if [ -d "web" ]; then
    cd web
    echo "Installing frontend dependencies..."
    npm install
    echo "Building frontend..."
    npm run build
    echo "✓ Frontend build complete"
    cd ..
else
    echo "⚠ Warning: web directory not found, skipping frontend build"
fi

echo ""
echo "==> Initializing database..."
python -c "from rivaflow.db.database import init_db; init_db()"

echo ""
echo "========================================================================"
echo "✓ BUILD SUCCESSFUL - RivaFlow v0.2.0"
echo "========================================================================"

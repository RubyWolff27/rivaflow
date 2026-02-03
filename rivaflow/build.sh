#!/bin/bash
# Render build script for RivaFlow v0.2.0

set -e  # Exit on error

echo ""
echo "████████████████████████████████████████████████████████████████████████████████"
echo "██                                                                            ██"
echo "██  RivaFlow Build Script v0.2.0-NO-AI-DEPS                                   ██"
echo "██  Git commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'UNKNOWN')                                                     ██"
echo "██  Build time: $(date -u +"%Y-%m-%d %H:%M:%S UTC")                            ██"
echo "██                                                                            ██"
echo "████████████████████████████████████████████████████████████████████████████████"
echo ""

if [ -f rivaflow/VERSION ]; then
    echo "✓ Found VERSION file: $(cat rivaflow/VERSION)"
else
    echo "✗ WARNING: VERSION file not found - using stale code!"
fi

echo ""
echo "==> Installing Python dependencies..."
pip install --upgrade pip setuptools wheel

echo ""
echo "==> Installing RivaFlow package (NON-EDITABLE)..."
pip install .

echo ""
echo "==> Verifying NO AI dependencies installed..."
python verify_no_ai_deps.py

echo ""
echo "==> Initializing database..."
python -c "from rivaflow.db.database import init_db; init_db()"

echo ""
echo "==> Build complete!"
echo "████████████████████████████████████████████████████████████████████████████████"

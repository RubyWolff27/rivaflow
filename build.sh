#!/usr/bin/env bash
# ============================================================
# RivaFlow Root Build Script (Render-compatible)
# ============================================================
# Render's Build Command is configured as `bash build.sh`, but the
# actual build logic lives at `rivaflow/build.sh`. This thin wrapper
# delegates to the inner script so Render finds it at the repo root.
#
# History: the root-level build.sh was lost during a refactor and
# the Render dashboard was still configured to call it. Restored
# 2026-04-05 (Ruby Wolff + Sage) as part of Sprint cleanup session.
#
# The inner script at rivaflow/build.sh handles:
#   - pip install for the Python backend package
#   - npm build for the frontend at rivaflow/web/
#   - database init check
#   - verify_no_ai_deps.py guard
# ============================================================

set -euo pipefail

cd "$(dirname "$0")"

echo "==> RivaFlow root build wrapper — delegating to rivaflow/build.sh"
echo "==> CWD: $(pwd)"
echo "==> Commit: $(git rev-parse --short HEAD 2>/dev/null || echo unknown)"

if [ ! -f rivaflow/build.sh ]; then
    echo "✗ ERROR: rivaflow/build.sh not found — cannot build"
    ls -la rivaflow/ 2>&1 || true
    exit 1
fi

exec bash rivaflow/build.sh

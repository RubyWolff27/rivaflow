#!/bin/bash
# Sync rivaflow/web/ to web/ for Render static site deployment.
#
# Render's rivaflow-web service builds from the root-level web/ directory.
# Source of truth for frontend code is rivaflow/web/.
# Run this script before committing frontend changes to keep web/ in sync.
#
# Usage:
#   ./scripts/sync-web.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

SOURCE="${REPO_ROOT}/rivaflow/web/"
DEST="${REPO_ROOT}/web/"

if [ ! -d "$SOURCE" ]; then
    echo "ERROR: Source directory not found: ${SOURCE}"
    exit 1
fi

rsync -a --delete "$SOURCE" "$DEST"

echo "Synced rivaflow/web/ -> web/"

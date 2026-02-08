#!/bin/bash
# RivaFlow Database Backup Script
#
# Usage:
#   ./scripts/backup_db.sh
#
# Requires:
#   - DATABASE_URL environment variable (Render PostgreSQL connection string)
#   - pg_dump installed locally
#
# The script creates a timestamped SQL dump in ./backups/
#
# Recommended: Run weekly during beta, daily before scaling.
# To automate on macOS, add to crontab:
#   crontab -e
#   0 2 * * * cd /path/to/rivaflow && ./scripts/backup_db.sh
#
# To restore from backup:
#   psql "$DATABASE_URL" < backups/rivaflow_backup_YYYY-MM-DD_HHMMSS.sql

set -euo pipefail

BACKUP_DIR="$(dirname "$0")/../backups"
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/rivaflow_backup_${TIMESTAMP}.sql"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Check DATABASE_URL is set
if [ -z "${DATABASE_URL:-}" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set."
    echo ""
    echo "Get it from Render dashboard:"
    echo "  rivaflow-db-v2 → Info → External Database URL"
    echo ""
    echo "Then run:"
    echo "  DATABASE_URL='postgresql://...' ./scripts/backup_db.sh"
    exit 1
fi

echo "Starting backup..."
echo "  Timestamp: ${TIMESTAMP}"
echo "  Output:    ${BACKUP_FILE}"

# Run pg_dump
pg_dump "$DATABASE_URL" \
    --no-owner \
    --no-privileges \
    --format=plain \
    --file="$BACKUP_FILE"

# Compress the backup
gzip "$BACKUP_FILE"
COMPRESSED="${BACKUP_FILE}.gz"

SIZE=$(du -h "$COMPRESSED" | cut -f1)
echo "Backup complete: ${COMPRESSED} (${SIZE})"

# Keep only last 30 backups
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/rivaflow_backup_*.sql.gz 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt 30 ]; then
    echo "Cleaning old backups (keeping last 30)..."
    ls -1t "$BACKUP_DIR"/rivaflow_backup_*.sql.gz | tail -n +31 | xargs rm -f
fi

echo "Done."

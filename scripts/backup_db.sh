#!/bin/bash
# RivaFlow Database Backup Script
#
# Usage:
#   ./scripts/backup_db.sh [DATABASE_URL]
#
# DATABASE_URL can be passed as the first argument or set as an environment variable.
#
# Requires:
#   - pg_dump installed locally
#
# Optional environment variables:
#   - S3_BUCKET_NAME: If set, uploads the backup to s3://$S3_BUCKET_NAME/backups/
#     (requires AWS CLI configured with appropriate credentials)
#
# The script creates a timestamped gzip SQL dump in ./backups/
#
# Recommended: Run weekly during beta, daily before scaling.
# To automate on macOS, add to crontab:
#   crontab -e
#   0 2 * * * cd /path/to/rivaflow && ./scripts/backup_db.sh
#
# To restore from backup:
#   gunzip -c backups/rivaflow_backup_YYYYMMDD_HHMMSS.sql.gz | psql "$DATABASE_URL"

set -euo pipefail

# Accept DATABASE_URL from first argument or environment variable
DATABASE_URL="${1:-${DATABASE_URL:-}}"

BACKUP_DIR="$(dirname "$0")/../backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/rivaflow_backup_${TIMESTAMP}.sql"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Check DATABASE_URL is set
if [ -z "${DATABASE_URL}" ]; then
    echo "ERROR: DATABASE_URL is not set."
    echo ""
    echo "Pass it as an argument or environment variable:"
    echo "  ./scripts/backup_db.sh 'postgresql://...'"
    echo "  DATABASE_URL='postgresql://...' ./scripts/backup_db.sh"
    echo ""
    echo "Get it from Render dashboard:"
    echo "  rivaflow-db-v2 -> Info -> External Database URL"
    exit 1
fi

echo "Starting backup..."
echo "  Timestamp: ${TIMESTAMP}"
echo "  Output:    ${BACKUP_FILE}.gz"

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

# Optionally upload to S3
if [ -n "${S3_BUCKET_NAME:-}" ]; then
    S3_PATH="s3://${S3_BUCKET_NAME}/backups/rivaflow_backup_${TIMESTAMP}.sql.gz"
    echo "Uploading to ${S3_PATH}..."
    aws s3 cp "$COMPRESSED" "$S3_PATH"
    echo "S3 upload complete."
fi

# Keep only last 30 backups
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/rivaflow_backup_*.sql.gz 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt 30 ]; then
    echo "Cleaning old backups (keeping last 30)..."
    ls -1t "$BACKUP_DIR"/rivaflow_backup_*.sql.gz | tail -n +31 | xargs rm -f
fi

echo "Done. Backup saved to ${COMPRESSED}"

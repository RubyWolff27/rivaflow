#!/bin/bash
# RivaFlow DB backup -> restic on Cloudflare R2 (offsite). Run via cron.
set -euo pipefail
cd /opt/rivaflow
set -a; . ./.env.prod; set +a            # S3_* creds
. ./.backup.env                          # RESTIC_PASSWORD
export AWS_ACCESS_KEY_ID="$S3_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="$S3_SECRET_ACCESS_KEY"
export AWS_DEFAULT_REGION="${S3_REGION:-auto}"
export RESTIC_REPOSITORY="s3:${S3_ENDPOINT_URL}/${S3_BUCKET_NAME}/restic-db"
export RESTIC_PASSWORD

ts=$(date +%Y%m%d-%H%M%S)
mkdir -p /opt/rivaflow/backups
DUMP="/opt/rivaflow/backups/rivaflow-${ts}.sql.gz"

echo "==> pg_dump"
sudo -n docker compose -f docker-compose.prod.yml exec -T db pg_dump -U rivaflow rivaflow | gzip > "$DUMP"
echo "    dump: $(du -h "$DUMP" | cut -f1)"

echo "==> restic init (if needed)"
restic snapshots >/dev/null 2>&1 || restic init

echo "==> restic backup"
restic backup "$DUMP" --tag rivaflow-db --host rivaflow-vps

echo "==> retention (14 daily / 8 weekly)"
restic forget --keep-daily 14 --keep-weekly 8 --prune >/dev/null

# keep only last 3 local dumps (R2 is the real store)
ls -t /opt/rivaflow/backups/*.sql.gz 2>/dev/null | tail -n +4 | xargs -r rm -f

# heartbeat for monitoring
date -u +%Y-%m-%dT%H:%M:%SZ > /opt/rivaflow/backups/.last_success
echo "BACKUP OK ${ts}"

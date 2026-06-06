#!/bin/bash
# Stage 5: read-only pg_dump from Render -> restore into local VPS Postgres.
# Render is untouched (dump is read-only).
set -uo pipefail
cd /opt/rivaflow
REN=$(cat .renderdb.conn)
# Render requires SSL; ensure sslmode if not already present
case "$REN" in *sslmode=*) ;; *) REN="${REN}?sslmode=require";; esac
DBPW=$(grep '^DB_PASSWORD=' .env | cut -d= -f2-)
LOC="postgresql://rivaflow:${DBPW}@db:5432/rivaflow"

sudo -n docker run --rm --network rivaflow_default -e REN="$REN" -e LOC="$LOC" postgres:18 bash -c '
  set -o pipefail
  echo "==> dumping from Render (read-only)..."
  pg_dump "$REN" --no-owner --no-acl -f /tmp/r.sql || { echo "DUMP_FAILED"; exit 2; }
  echo "==> dump size: $(wc -l </tmp/r.sql) lines, $(du -h /tmp/r.sql | cut -f1)"
  echo "==> restoring into local db..."
  psql "$LOC" -v ON_ERROR_STOP=0 -f /tmp/r.sql > /tmp/rest.log 2>&1
  echo "==> restore real errors (excluding benign):"
  grep -iE "error|fatal" /tmp/rest.log | grep -viE "already exists|multiple primary keys|skipping" | head -12 || echo "  none"
'
echo "=== verify: tables in local db ==="
sudo -n docker compose -f docker-compose.prod.yml exec -T db psql -U rivaflow -d rivaflow -c "\dt" 2>/dev/null | tail -30
echo "=== key row counts ==="
sudo -n docker compose -f docker-compose.prod.yml exec -T db psql -U rivaflow -d rivaflow -tc "SELECT 'users='||count(*) FROM users;" 2>/dev/null || echo "(no users table)"
sudo -n docker compose -f docker-compose.prod.yml exec -T db psql -U rivaflow -d rivaflow -tc "SELECT 'sessions='||count(*) FROM sessions;" 2>/dev/null || echo "(no sessions table)"

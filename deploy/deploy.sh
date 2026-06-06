#!/bin/bash
# Pull-based GitOps deploy for RivaFlow on the VPS (pai-relay).
# Runs from cron; only redeploys when origin/main advances. Health-check + auto-rollback.
# Secure by design: VPS pulls (read-only deploy key) — no inbound SSH, no runner on the host.
set -uo pipefail
cd /opt/rivaflow || exit 1
log(){ echo "$(date -u +%FT%TZ) $*"; }

git fetch --quiet origin main 2>/dev/null || { log "git fetch failed"; exit 1; }
LOCAL=$(git rev-parse HEAD); REMOTE=$(git rev-parse origin/main)
[ "$LOCAL" = "$REMOTE" ] && exit 0   # nothing new

log "deploy $LOCAL -> $REMOTE"; PREV=$LOCAL
git reset --hard origin/main 2>/dev/null || { log "reset failed"; exit 1; }

if ! ( sudo -n docker compose -f docker-compose.prod.yml build && \
       sudo -n docker compose -f docker-compose.prod.yml up -d ); then
  log "build/up FAILED -> rollback to $PREV"
  git reset --hard "$PREV"; sudo -n docker compose -f docker-compose.prod.yml up -d --build; exit 1
fi

ok=0
for i in $(seq 1 24); do
  if sudo -n docker compose -f docker-compose.prod.yml exec -T web wget -qO- --timeout=5 http://api:8000/health >/dev/null 2>&1; then ok=1; break; fi
  sleep 5
done
if [ "$ok" != 1 ]; then
  log "health check FAILED -> rollback to $PREV"
  git reset --hard "$PREV"; sudo -n docker compose -f docker-compose.prod.yml up -d --build; exit 1
fi

log "deploy OK -> $REMOTE"
date -u +%FT%TZ > /opt/rivaflow/.last_deploy

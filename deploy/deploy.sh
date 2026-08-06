#!/bin/bash
# Pull-based GitOps deploy for RivaFlow on the VPS (pai-relay).
# Runs from cron; only redeploys when origin/main advances past the last
# SUCCESSFULLY-deployed SHA. Health-check + served-SHA assertion + auto-rollback.
# Secure by design: VPS pulls (read-only deploy key) — no inbound SSH, no runner on the host.
set -uo pipefail
cd /opt/rivaflow || exit 1
log(){ echo "$(date -u +%FT%TZ) $*"; }

COMPOSE="sudo -n docker compose -f docker-compose.prod.yml"
STATE_FILE=/opt/rivaflow/.last_deployed_sha
HANDLED=0     # set to 1 once we reach a terminal state (success OR rollback)
PREV=""       # last-known-good tree SHA; empty until we're about to move HEAD

# Single-flight guard. Without this a slow build overlaps the next 3-minute cron
# tick and the two runs race on `git reset`, leaving the OLD image on the NEW SHA.
# flock -n makes a second concurrent run exit immediately instead of racing.
exec 9>/opt/rivaflow/.deploy.lock
flock -n 9 || { log "another deploy already running — skipping this tick"; exit 0; }

# EXIT trap. flock stops OVERLAP; it does NOT stop a SINGLE run being killed (OOM,
# reboot, cron SIGTERM) AFTER `git reset` advanced HEAD but BEFORE the build+health
# finished. That used to strand an old image on a new HEAD, and — because the old
# skip test compared git HEAD — every later tick then said "nothing new" and the
# stale container went undetected. Two independent guards now prevent that:
#   1. deploy-state is .last_deployed_sha (written ONLY after a verified-healthy,
#      served-SHA-matched deploy), NOT git HEAD — a killed run leaves it stale, so
#      the next tick correctly redeploys.
#   2. this trap resets the working tree back to PREV on any unexpected exit, so a
#      killed run doesn't even leave HEAD ahead of the running image.
cleanup(){
  if [ "$HANDLED" != 1 ] && [ -n "$PREV" ]; then
    log "unexpected exit before a verified deploy — resetting tree to ${PREV:0:8}"
    git reset --hard "$PREV" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT
# A caught signal must EXIT (not resume the interrupted line); the exit then runs
# the single EXIT-trap reset above. Without this, bash resumes after the handler.
trap 'exit 143' TERM
trap 'exit 130' INT

git fetch --quiet origin main 2>/dev/null || { log "git fetch failed"; exit 1; }
REMOTE=$(git rev-parse origin/main)
DEPLOYED=$(cat "$STATE_FILE" 2>/dev/null || echo "none")
[ "$DEPLOYED" = "$REMOTE" ] && exit 0   # nothing new since the last VERIFIED-healthy deploy

PREV=$(git rev-parse HEAD)
log "deploy ${DEPLOYED:0:8} -> ${REMOTE:0:8} (tree at ${PREV:0:8})"
git reset --hard origin/main 2>/dev/null || { log "reset failed"; exit 1; }

# Roll the tree + running containers back to PREV and shout. Used for every caught
# failure below. Sets HANDLED so the EXIT trap doesn't reset a second time.
rollback(){
  log "$1 -> rollback to ${PREV:0:8}"
  git reset --hard "$PREV"
  $COMPOSE build --build-arg GIT_SHA="$PREV" && $COMPOSE up -d
  bash "$(dirname "$0")/notify.sh" "DEPLOY $1 for ${REMOTE:0:8} — rolled back to ${PREV:0:8}"
  HANDLED=1
  exit 1
}

# --build-arg on the CLI (not an env var): the value is a literal argument to the
# sudo'd docker, so sudo's env-reset can't strip it the way it would `export GIT_SHA`.
if ! ( $COMPOSE build --build-arg GIT_SHA="$REMOTE" && $COMPOSE up -d ); then
  rollback "build/up FAILED"
fi

ok=0
for i in $(seq 1 24); do
  if $COMPOSE exec -T web wget -qO- --timeout=5 http://api:8000/health >/dev/null 2>&1; then ok=1; break; fi
  sleep 5
done
[ "$ok" = 1 ] || rollback "health-check FAILED"

# Served-SHA assertion — the check that was missing. Ask the RUNNING api container
# what SHA it was built from; if it isn't the SHA we just built, an old image is
# still serving (the exact silent-stale failure) — roll back and shout.
SERVED=$($COMPOSE exec -T api printenv GIT_SHA 2>/dev/null | tr -d '\r\n')
if [ "$SERVED" != "$REMOTE" ]; then
  rollback "served-SHA mismatch (running=${SERVED:0:8} expected=${REMOTE:0:8})"
fi

log "deploy OK -> ${REMOTE:0:8} (served-SHA verified)"
echo "$REMOTE" > "$STATE_FILE"
date -u +%FT%TZ > /opt/rivaflow/.last_deploy
HANDLED=1

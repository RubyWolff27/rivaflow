#!/bin/bash
# Telegram alert helper for RivaFlow VPS ops (deploy/backup failures).
# Reads creds from /opt/rivaflow/.notify.env (gitignored). No-ops gracefully if
# unconfigured, so it NEVER breaks the caller.
#   Usage: notify.sh "message text"
#   .notify.env needs: TELEGRAM_BOT_TOKEN=...  TELEGRAM_CHAT_ID=...
set -u
msg="${1:-RivaFlow alert}"
ENVF=/opt/rivaflow/.notify.env
[ -f "$ENVF" ] || { echo "notify: no $ENVF — skipping"; exit 0; }
. "$ENVF"
[ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ] || { echo "notify: creds unset — skipping"; exit 0; }
host=$(hostname 2>/dev/null || echo vps)
curl -s -m 10 -o /dev/null \
  -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=⚠️ RivaFlow [${host}]: ${msg}" \
  --data-urlencode "disable_web_page_preview=true" \
  && echo "notify: sent"

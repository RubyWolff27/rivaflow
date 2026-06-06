#!/bin/bash
# RivaFlow VPS ops alerts (deploy/backup failures) -> routed through the EXISTING
# Hermes/Groot Telegram connection via `hermes send` (reuses the gateway's
# Telegram creds — no new bot, no token stored here). No-ops gracefully on any
# failure so it NEVER breaks the caller.
#   Usage: notify.sh "message text"
set -u
host=$(hostname 2>/dev/null || echo vps)
printf '%s' "⚠️ RivaFlow [${host}]: ${1:-alert}" \
  | sudo -n -u pai-hermes env HERMES_HOME=/home/pai-hermes/.hermes \
      hermes send -t telegram -f - --quiet 2>/dev/null \
  && echo "notify: sent via hermes/telegram" \
  || echo "notify: hermes send unavailable (non-fatal)"

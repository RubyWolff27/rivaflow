# RivaFlow — VPS Deployment (migrated off Render 2026-06-06)

RivaFlow now runs self-hosted on the **pai-relay VPS** via Docker Compose, fronted by a
Cloudflare Tunnel. Migrated off Render (~$30/mo saved). Solo-use app.

## Architecture
- `db`  — postgres:18 (volume `pgdata` at `/var/lib/postgresql`)
- `api` — FastAPI/gunicorn (`Dockerfile.api`, nested package `rivaflow/rivaflow/`)
- `web` — Vite SPA built + served by Caddy (`web.Dockerfile` + `Caddyfile`)
- `cloudflared` — connector for tunnel `rivaflow-staging` → `api.rivaflow.app` + `rivaflow.app`
  (+ `staging[-api].rivaflow.app`). All containers memory-limited (Groot's gateway = priority tenant).

## Files
- `docker-compose.prod.yml` — the stack (lives at `/opt/rivaflow/`)
- `Dockerfile.api`, `web.Dockerfile`, `Caddyfile`
- `migrate_db.sh` — one-time Render→VPS data migration (read-only dump)
- `backup.sh` — daily restic→Cloudflare R2 offsite backup (cron 03:00 AEST)
- `deploy.sh` — **pull-based GitOps**: cron checks `origin/main`, rebuilds + health-checks + auto-rollback
- `cf_tunnel_setup.sh` — one-time tunnel + DNS creation

## Secrets (NOT in git — on the VPS only)
- `/opt/rivaflow/.env.prod` — app env (26 vars pulled from Render: S3/R2, WHOOP, SendGrid, etc.)
- `/opt/rivaflow/.env` — `DB_PASSWORD` for compose
- `/opt/rivaflow/.tunnel.env` — cloudflared `TUNNEL_TOKEN`
- `/opt/rivaflow/.backup.env` — restic password (also stored on Sage's Mac for DR)

## CI/CD (GitHub → VPS)
- Push to `main` → `.github/workflows/deploy.yml` runs **tests + security** gates.
- The VPS auto-pulls `main` via `deploy.sh` (cron) using a **read-only deploy key**, rebuilds,
  health-checks, and auto-rolls-back on failure. No inbound SSH / no self-hosted runner.

## Rollback (manual)
`cd /opt/rivaflow && git reset --hard <prev-sha> && sudo docker compose -f docker-compose.prod.yml up -d --build`
DNS rollback to Render (if ever needed): repoint `api.rivaflow.app`→`rivaflow-api-v2.onrender.com`,
`rivaflow.app`→A `216.24.57.1`.

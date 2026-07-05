-- 112_whoop_cockpit_snapshot_pg.sql
-- Pre-computed cockpit HTML snapshot for the WHOOP data platform (PostgreSQL / production).
-- See 112_whoop_cockpit_snapshot.sql for the SQLite (local dev) variant.
--
-- The analyst cockpit runs ~15 multi-day analytics per render (~40s cold), which black-screens the
-- browser on an on-demand fetch. Instead a scheduled job pre-computes the full page every 4h and stores
-- it here, so the serve is a single instant SELECT. One row per user, upserted in place.
-- (Keep these comments free of the semicolon character, which the migration runner treats as a
--  statement separator even inside a comment.)
CREATE TABLE IF NOT EXISTS whoop_cockpit_snapshot (
    user_id     INTEGER     PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    html        TEXT        NOT NULL,
    rendered_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

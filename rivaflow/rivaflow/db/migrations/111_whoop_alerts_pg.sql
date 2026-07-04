-- 111_whoop_alerts_pg.sql
-- Delivery log + cooldown state for the WHOOP prevention digest (PostgreSQL / production).
-- See 111_whoop_alerts.sql for the SQLite (local dev) variant.
--
-- One row per safety alert the once-daily digest actually fired (P2 delivery). It is the cooldown
-- state (last-fired per key) and the delivery record the prevention-log panel reads. Anti-anxiety by
-- design, so this is a daily digest record, never a live-refresh flag.
-- (Keep these comments free of the semicolon character, which the migration runner treats as a
--  statement separator even inside a comment.)
CREATE TABLE IF NOT EXISTS whoop_alerts (
    id          BIGSERIAL   PRIMARY KEY,
    user_id     INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day         DATE        NOT NULL,
    alert_key   TEXT        NOT NULL,
    tier        TEXT        NOT NULL,
    headline    TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, day, alert_key)
);

CREATE INDEX IF NOT EXISTS whoop_alerts_user_day_idx ON whoop_alerts (user_id, day);

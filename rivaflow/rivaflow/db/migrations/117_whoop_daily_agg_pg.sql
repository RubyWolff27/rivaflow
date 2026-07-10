-- 117_whoop_daily_agg_pg.sql
-- Append-only per-day rollup cache for the WHOOP data platform (PostgreSQL / production).
-- See 117_whoop_daily_agg.sql for the SQLite (local dev) variant.
--
-- whoop_summary() re-scanned weeks of raw whoop_hr/whoop_rr rows on EVERY call — each of
-- daily_resting_rmssd, daily_resting_hr, nightly_sleep_history, and daily_cardio_load independently
-- re-derived HRV/resting-HR/sleep/cardio-load over their own N-day window every time. A day's raw rows
-- rarely change once the day is over, so this table lets a historical day be computed ONCE and served
-- from metrics_json thereafter — only today (still accruing) is ever computed live. sample_count is the
-- staleness signal: the phone's offline spool and historical drains can land whoop_hr/whoop_rr rows for a
-- day well after it first looked complete, so a stored day whose CURRENT raw count no longer matches what
-- it was rolled up from gets recomputed. One row per (user_id, day), upserted in place — see
-- rivaflow.core.services.whoop_daily_agg.
-- (Keep these comments free of the semicolon character, which the migration runner treats as a
--  statement separator even inside a comment.)
CREATE TABLE IF NOT EXISTS whoop_daily_agg (
    id              SERIAL      PRIMARY KEY,
    user_id         INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day             TEXT        NOT NULL,
    metrics_json    TEXT        NOT NULL,
    deriver_version TEXT        NOT NULL,
    sample_count    INTEGER     NOT NULL,
    complete        BOOLEAN     NOT NULL DEFAULT TRUE,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, day)
);

CREATE INDEX IF NOT EXISTS whoop_daily_agg_user_day_idx
    ON whoop_daily_agg (user_id, day);

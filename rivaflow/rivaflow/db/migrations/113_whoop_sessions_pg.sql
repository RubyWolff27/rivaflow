-- 113_whoop_sessions_pg.sql
-- Timestamped workout-session store for the WHOOP data platform (PostgreSQL / production).
-- See 113_whoop_sessions.sql for the SQLite (local dev) variant.
--
-- The class `sessions` table only carries a date, so per-second WHOOP HR cannot attach to a workout.
-- This is a dedicated store with a real start/end window (logged from the app, closed when the session
-- ends), so the cockpit's Workouts list + last-workout card can attach in-window HR and compute the
-- deep-dive (curve, zones, load, hardness). One row per logged workout.
-- (Keep these comments free of the semicolon character, which the migration runner treats as a
--  statement separator even inside a comment.)
CREATE TABLE IF NOT EXISTS whoop_sessions (
    id          SERIAL      PRIMARY KEY,
    user_id     INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity    TEXT        NOT NULL,
    started_at  TIMESTAMPTZ NOT NULL,
    ended_at    TIMESTAMPTZ,
    source      TEXT        NOT NULL DEFAULT 'app',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS whoop_sessions_user_started_idx
    ON whoop_sessions (user_id, started_at DESC);

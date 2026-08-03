-- 119_strava_session_biometrics_pg.sql
-- Per-session Strava biometrics (PostgreSQL / production).
-- See 119_strava_session_biometrics.sql for the SQLite (local dev) variant.
--
-- These ride on the session object exactly like the garmin_* columns do, and are written via the
-- session update path rather than session create. Deliberately NOT reusing garmin_* or whoop_*:
-- labelling Strava-sourced heart rate as Garmin data would misattribute it in the UI, and both of
-- those devices are out of service for this user.
-- (Keep these comments free of the semicolon character, which the migration runner splits on.)
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS strava_activity_id TEXT;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS strava_activity_name TEXT;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS strava_activity_type TEXT;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS strava_avg_hr INTEGER;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS strava_max_hr INTEGER;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS strava_calories INTEGER;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS strava_duration_min REAL;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS strava_suffer_score REAL;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS strava_distance_m REAL;

-- One session per Strava activity — makes the auto-import idempotent at the database level,
-- so a re-run of the July backfill cannot produce duplicate sessions even if the cache is rebuilt.
CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_strava_activity
    ON sessions (user_id, strava_activity_id)
    WHERE strava_activity_id IS NOT NULL;

-- 119_strava_session_biometrics.sql
-- Per-session Strava biometrics (SQLite local-dev variant of 119_strava_session_biometrics_pg.sql).
--
-- These ride on the session object exactly like the garmin_* columns do, and are written via the
-- session update path rather than session create. Deliberately NOT reusing garmin_* or whoop_*:
-- labelling Strava-sourced heart rate as Garmin data would misattribute it in the UI, and both of
-- those devices are out of service for this user.
-- (Keep these comments free of the semicolon character, which the migration runner splits on.)
ALTER TABLE sessions ADD COLUMN strava_activity_id TEXT;
ALTER TABLE sessions ADD COLUMN strava_activity_name TEXT;
ALTER TABLE sessions ADD COLUMN strava_activity_type TEXT;
ALTER TABLE sessions ADD COLUMN strava_avg_hr INTEGER;
ALTER TABLE sessions ADD COLUMN strava_max_hr INTEGER;
ALTER TABLE sessions ADD COLUMN strava_calories INTEGER;
ALTER TABLE sessions ADD COLUMN strava_duration_min REAL;
ALTER TABLE sessions ADD COLUMN strava_suffer_score REAL;
ALTER TABLE sessions ADD COLUMN strava_distance_m REAL;

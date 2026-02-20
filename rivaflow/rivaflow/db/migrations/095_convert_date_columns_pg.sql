-- Convert session_date from TEXT to DATE on PostgreSQL
-- Must DROP DEFAULT before TYPE change, then SET DEFAULT after

-- sessions.session_date: TEXT → DATE
ALTER TABLE sessions ALTER COLUMN session_date DROP DEFAULT;
ALTER TABLE sessions ALTER COLUMN session_date TYPE DATE USING session_date::date;

-- readiness.check_date: TEXT → DATE
ALTER TABLE readiness ALTER COLUMN check_date DROP DEFAULT;
ALTER TABLE readiness ALTER COLUMN check_date TYPE DATE USING check_date::date;

-- daily_checkins.check_date: TEXT → DATE
ALTER TABLE daily_checkins ALTER COLUMN check_date DROP DEFAULT;
ALTER TABLE daily_checkins ALTER COLUMN check_date TYPE DATE USING check_date::date;

-- activity_photos.activity_date: TEXT → DATE
ALTER TABLE activity_photos ALTER COLUMN activity_date DROP DEFAULT;
ALTER TABLE activity_photos ALTER COLUMN activity_date TYPE DATE USING activity_date::date;

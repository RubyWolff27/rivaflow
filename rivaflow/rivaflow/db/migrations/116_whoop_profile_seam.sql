-- 116_whoop_profile_seam.sql
-- Per-user profile fields the WhoopProfile seam reads (SQLite/test): sleep-need
-- hours, which weekday is the rest day, an optional manual max-HR override, and
-- the device-reported IANA tz (distinct from profile.timezone, which is user-set;
-- device_tz is what the WHOOP strap/phone last reported at ingest).
ALTER TABLE profile ADD COLUMN sleep_need_h REAL DEFAULT 8.0;
ALTER TABLE profile ADD COLUMN rest_weekday INTEGER DEFAULT 6;
ALTER TABLE profile ADD COLUMN max_hr_override INTEGER;
ALTER TABLE profile ADD COLUMN device_tz TEXT;

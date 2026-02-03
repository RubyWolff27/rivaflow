-- Add Whoop fitness tracker stats to sessions
-- Migration: 011_add_whoop_stats

ALTER TABLE sessions ADD COLUMN whoop_strain REAL;
ALTER TABLE sessions ADD COLUMN whoop_calories INTEGER;
ALTER TABLE sessions ADD COLUMN whoop_avg_hr INTEGER;
ALTER TABLE sessions ADD COLUMN whoop_max_hr INTEGER;

-- Add index for querying sessions with Whoop data
CREATE INDEX IF NOT EXISTS idx_sessions_whoop_strain ON sessions(whoop_strain) WHERE whoop_strain IS NOT NULL;

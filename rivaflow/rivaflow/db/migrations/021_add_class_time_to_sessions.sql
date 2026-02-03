-- Migration 021: Add class_time to sessions table
-- Add optional class time field (HH:MM format)

ALTER TABLE sessions ADD COLUMN class_time TEXT;

-- Add index for querying by class time
CREATE INDEX IF NOT EXISTS idx_sessions_class_time ON sessions(class_time);

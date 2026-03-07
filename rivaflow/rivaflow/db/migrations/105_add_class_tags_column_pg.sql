ALTER TABLE sessions ADD COLUMN IF NOT EXISTS class_tags TEXT;

-- Update CHECK constraint to include 'drilling'
ALTER TABLE sessions DROP CONSTRAINT IF EXISTS chk_sessions_class_type;
ALTER TABLE sessions ADD CONSTRAINT chk_sessions_class_type CHECK (class_type IN ('gi', 'no-gi', 'open-mat', 'competition', 's&c', 'cardio', 'mobility', 'wrestling', 'judo', 'yoga', 'rehab', 'physio', 'drilling'));

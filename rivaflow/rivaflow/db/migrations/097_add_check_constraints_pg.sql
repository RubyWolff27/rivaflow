-- Add CHECK constraint for sessions.class_type
ALTER TABLE sessions ADD CONSTRAINT chk_sessions_class_type CHECK (class_type IN ('gi', 'no-gi', 'open-mat', 'competition', 's&c', 'cardio', 'mobility', 'wrestling', 'judo', 'yoga', 'rehab', 'physio'));

-- Add CHECK constraint for sessions.visibility_level
ALTER TABLE sessions ADD CONSTRAINT chk_sessions_visibility_level CHECK (visibility_level IN ('private', 'attendance', 'summary', 'full'));

-- Add CHECK constraint for sessions.intensity (may already exist from CREATE TABLE)
ALTER TABLE sessions ADD CONSTRAINT chk_sessions_intensity_range CHECK (intensity BETWEEN 1 AND 5);

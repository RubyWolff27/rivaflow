-- Add instructor field to sessions table
ALTER TABLE sessions ADD COLUMN instructor_id INTEGER REFERENCES contacts(id) ON DELETE SET NULL;
ALTER TABLE sessions ADD COLUMN instructor_name TEXT;  -- Fallback if no contact record

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_sessions_instructor ON sessions(instructor_id);

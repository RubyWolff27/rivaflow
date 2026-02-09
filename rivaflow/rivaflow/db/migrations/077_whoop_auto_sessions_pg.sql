-- Add source tracking and review flag to sessions
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'manual';
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS needs_review BOOLEAN DEFAULT FALSE;

-- Add auto-create preference to whoop_connections
ALTER TABLE whoop_connections ADD COLUMN IF NOT EXISTS auto_create_sessions BOOLEAN DEFAULT FALSE;

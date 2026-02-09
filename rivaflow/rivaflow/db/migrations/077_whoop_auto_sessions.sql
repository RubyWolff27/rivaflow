-- Add source tracking and review flag to sessions
ALTER TABLE sessions ADD COLUMN source TEXT DEFAULT 'manual';
ALTER TABLE sessions ADD COLUMN needs_review INTEGER DEFAULT 0;

-- Add auto-create preference to whoop_connections
ALTER TABLE whoop_connections ADD COLUMN auto_create_sessions INTEGER DEFAULT 0;

-- Add auto_fill_readiness toggle to whoop_connections (PostgreSQL)
ALTER TABLE whoop_connections ADD COLUMN IF NOT EXISTS auto_fill_readiness BOOLEAN DEFAULT FALSE;

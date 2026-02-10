-- Add auto_fill_readiness toggle to whoop_connections
ALTER TABLE whoop_connections ADD COLUMN auto_fill_readiness INTEGER DEFAULT 0;

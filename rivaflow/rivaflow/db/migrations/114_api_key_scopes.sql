-- 114_api_key_scopes.sql
-- Add a scope to api_keys so a read-only dashboard key can exist (SQLite/test).
-- Existing keys default to 'full' so nothing is locked out. Read-only keys
-- carry 'read' and are rejected on write and admin routes.
ALTER TABLE api_keys ADD COLUMN scopes TEXT NOT NULL DEFAULT 'full';

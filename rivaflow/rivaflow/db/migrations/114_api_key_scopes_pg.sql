-- 114_api_key_scopes_pg.sql
-- Add a scope to api_keys so a read-only dashboard key can exist (PG).
-- Existing keys default to 'full' (user-equivalent) so nothing is locked out.
-- Read-only keys carry 'read' and are rejected on every write and admin route,
-- letting the bookmarkable cockpit URL carry a non-write credential.
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS scopes TEXT NOT NULL DEFAULT 'full';

-- 107_create_api_keys_pg.sql
-- Add api_keys table for user-owned API key authentication (PG).
--
-- A user can mint named API keys with the same authorization scope as their
-- own user account ("simple, user-equivalent keys" — Sage MCP integration spec).
-- Keys are stored as SHA-256 hashes. Raw values are revealed exactly once at
-- creation and never persisted in plaintext.
-- (Keep these comments free of the semicolon character, which the migration
--  runner treats as a statement separator even inside a comment.)
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    key_prefix TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS api_keys_user_id_idx ON api_keys (user_id);
CREATE INDEX IF NOT EXISTS api_keys_key_hash_idx ON api_keys (key_hash);
CREATE INDEX IF NOT EXISTS api_keys_user_active_idx
    ON api_keys (user_id)
    WHERE revoked_at IS NULL;

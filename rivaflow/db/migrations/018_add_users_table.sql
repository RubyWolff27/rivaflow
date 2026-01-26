-- ============================================================
-- MIGRATION 018: Add Users and Refresh Tokens Tables
-- Multi-user authentication with JWT tokens
-- ============================================================

-- USERS: User accounts with email/password authentication
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- REFRESH_TOKENS: Long-lived tokens for token refresh
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- INDEXES for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);

-- DATA MIGRATION: Create first user from existing profile (if exists)
-- This assumes a profile exists with id=1. If profile data exists, create a user for it.
-- The email defaults to user@localhost (profile table doesn't have email column yet).
-- Password is set to a placeholder - user will need to register a new account or reset password.
INSERT INTO users (id, email, hashed_password, first_name, last_name, is_active, created_at, updated_at)
SELECT
    1 as id,
    'user@localhost' as email,
    '$2b$12$placeholder.hash.that.wont.match.any.real.password' as hashed_password,
    COALESCE((SELECT first_name FROM profile WHERE id = 1), 'User') as first_name,
    COALESCE((SELECT last_name FROM profile WHERE id = 1), 'One') as last_name,
    1 as is_active,
    datetime('now') as created_at,
    datetime('now') as updated_at
WHERE EXISTS (SELECT 1 FROM profile WHERE id = 1)
  AND NOT EXISTS (SELECT 1 FROM users WHERE id = 1);

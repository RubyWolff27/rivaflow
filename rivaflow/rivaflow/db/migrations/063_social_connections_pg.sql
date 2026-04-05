-- PostgreSQL version (auto-generated from sibling .sql file)
-- Translations applied: AUTOINCREMENT→BIGSERIAL, *_id INTEGER→BIGINT,
-- datetime('now')→CURRENT_TIMESTAMP, BOOLEAN 0/1→FALSE/TRUE,
-- PRAGMA/BEGIN/COMMIT removed, CREATE INDEX→IF NOT EXISTS.
-- Regenerate: bun /tmp/translate_sqlite_to_pg.py (see note in header)

-- ============================================================================
-- MIGRATION 063: Social Connections, Friend Suggestions, and User Profile Columns
-- Created: 2026-02-07
-- Purpose: Add friend connections, blocking, friend suggestions, and
--          social profile columns needed by social features
-- ============================================================================

-- Add social profile columns to users table
ALTER TABLE users ADD COLUMN username TEXT;
ALTER TABLE users ADD COLUMN display_name TEXT;
ALTER TABLE users ADD COLUMN profile_photo_url TEXT;
ALTER TABLE users ADD COLUMN location_city TEXT;
ALTER TABLE users ADD COLUMN location_state TEXT;
ALTER TABLE users ADD COLUMN location_country TEXT DEFAULT 'AU';
ALTER TABLE users ADD COLUMN belt_rank TEXT DEFAULT 'white';
ALTER TABLE users ADD COLUMN belt_stripes INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN searchable BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN profile_visibility TEXT DEFAULT 'friends';
ALTER TABLE users ADD COLUMN activity_visibility TEXT DEFAULT 'friends';
ALTER TABLE users ADD COLUMN bio TEXT;
ALTER TABLE users ADD COLUMN preferred_style TEXT DEFAULT 'both';

-- Friend Connections (request/accept flow)
CREATE TABLE IF NOT EXISTS friend_connections (
    id BIGSERIAL PRIMARY KEY,
    requester_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending',
    connection_source TEXT,
    request_message TEXT,
    requested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    responded_at TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(requester_id, recipient_id)
);

CREATE INDEX IF NOT EXISTS idx_friend_connections_requester ON friend_connections(requester_id);
CREATE INDEX IF NOT EXISTS idx_friend_connections_recipient ON friend_connections(recipient_id);
CREATE INDEX IF NOT EXISTS idx_friend_connections_status ON friend_connections(status);

-- Blocked Users
CREATE TABLE IF NOT EXISTS blocked_users (
    id BIGSERIAL PRIMARY KEY,
    blocker_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    blocked_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason TEXT,
    blocked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(blocker_id, blocked_id)
);

CREATE INDEX IF NOT EXISTS idx_blocked_users_blocker ON blocked_users(blocker_id);
CREATE INDEX IF NOT EXISTS idx_blocked_users_blocked ON blocked_users(blocked_id);

-- Friend Suggestions
CREATE TABLE IF NOT EXISTS friend_suggestions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    suggested_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score REAL DEFAULT 0,
    reasons TEXT DEFAULT '[]',
    mutual_friends_count INTEGER DEFAULT 0,
    dismissed BOOLEAN DEFAULT FALSE,
    dismissed_at TEXT,
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT,
    UNIQUE(user_id, suggested_user_id)
);

CREATE INDEX IF NOT EXISTS idx_friend_suggestions_user ON friend_suggestions(user_id);
CREATE INDEX IF NOT EXISTS idx_friend_suggestions_score ON friend_suggestions(user_id, score);

-- Unique index for username (can't use UNIQUE on ALTER TABLE ADD COLUMN in SQLite)
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_unique ON users(username) WHERE username IS NOT NULL;

-- Sync display_name from first/last name for existing users
UPDATE users
SET display_name = TRIM(COALESCE(first_name, '') || ' ' || COALESCE(last_name, ''))
WHERE display_name IS NULL AND (first_name IS NOT NULL OR last_name IS NOT NULL);

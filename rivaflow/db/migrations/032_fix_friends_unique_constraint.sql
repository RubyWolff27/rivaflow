-- ============================================================
-- MIGRATION 032: Fix friends table unique constraint
-- Change from UNIQUE(name) to UNIQUE(user_id, name)
-- This allows multiple users to have friends with the same name
-- ============================================================

-- For SQLite: Need to recreate the table since it doesn't support DROP CONSTRAINT

-- Create new friends table with correct constraint
CREATE TABLE IF NOT EXISTS friends_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    friend_type TEXT NOT NULL DEFAULT 'training-partner' CHECK(friend_type IN ('training-partner', 'instructor', 'other')),
    belt_rank TEXT,
    gym TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),

    UNIQUE(user_id, name)  -- Each user can have their own friend named "John"
);

-- Copy existing data (explicitly list columns to handle different column order and schema)
-- Note: Old friends table has more columns (belt_stripes, instructor_certification, phone, email)
-- New schema simplified to: id, user_id, name, friend_type, belt_rank, gym, notes
-- Convert old 'both' friend_type to 'other'
INSERT INTO friends_new (
    id, user_id, name, friend_type, belt_rank, gym, notes, created_at, updated_at
)
SELECT
    id, user_id, name,
    CASE WHEN friend_type = 'both' THEN 'other' ELSE friend_type END as friend_type,
    belt_rank,
    NULL as gym,  -- gym column doesn't exist in old schema
    notes, created_at, updated_at
FROM friends;

-- Drop old table
DROP TABLE IF EXISTS friends;

-- Rename new table
ALTER TABLE friends_new RENAME TO friends;

-- Recreate indices
CREATE INDEX IF NOT EXISTS idx_friends_user_id ON friends(user_id);
CREATE INDEX IF NOT EXISTS idx_friends_name ON friends(name);

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

-- Copy existing data
INSERT INTO friends_new
SELECT * FROM friends;

-- Drop old table
DROP TABLE friends;

-- Rename new table
ALTER TABLE friends_new RENAME TO friends;

-- Recreate indices
CREATE INDEX IF NOT EXISTS idx_friends_user_id ON friends(user_id);
CREATE INDEX IF NOT EXISTS idx_friends_name ON friends(name);

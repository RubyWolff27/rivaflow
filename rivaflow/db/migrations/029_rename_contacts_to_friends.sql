-- Migration 029: Rename contacts table to friends
-- Rename all references from "contact" to "friend" for better social UX

-- Step 1: Create backup of contacts table
CREATE TABLE IF NOT EXISTS contacts_backup AS SELECT * FROM contacts;

-- Step 2: Drop old indexes
DROP INDEX IF EXISTS idx_contacts_name;
DROP INDEX IF EXISTS idx_contacts_type;
DROP INDEX IF EXISTS idx_contacts_belt;
DROP INDEX IF EXISTS idx_contacts_user_id;

-- Step 3: Drop the old contacts table (CASCADE for PostgreSQL foreign key constraints)
DROP TABLE IF EXISTS contacts CASCADE;

-- Step 4: Create new friends table with updated column name (contact_type -> friend_type)
CREATE TABLE friends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    friend_type TEXT NOT NULL DEFAULT 'training-partner' CHECK(friend_type IN ('instructor', 'training-partner', 'both')),
    belt_rank TEXT CHECK(belt_rank IN ('white', 'blue', 'purple', 'brown', 'black') OR belt_rank IS NULL),
    belt_stripes INTEGER DEFAULT 0 CHECK(belt_stripes BETWEEN 0 AND 4),
    instructor_certification TEXT,
    phone TEXT,
    email TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    user_id INTEGER NOT NULL DEFAULT 1 REFERENCES users(id) ON DELETE CASCADE
);

-- Step 5: Copy data from backup, renaming contact_type column to friend_type
INSERT INTO friends (id, user_id, name, friend_type, belt_rank, belt_stripes, instructor_certification, phone, email, notes, created_at, updated_at)
SELECT id, user_id, name, contact_type, belt_rank, belt_stripes, instructor_certification, phone, email, notes, created_at, updated_at
FROM contacts_backup;

-- Step 6: Drop the backup table
DROP TABLE contacts_backup;

-- Step 7: Create new indexes with updated names
CREATE INDEX IF NOT EXISTS idx_friends_name ON friends(name);
CREATE INDEX IF NOT EXISTS idx_friends_type ON friends(friend_type);
CREATE INDEX IF NOT EXISTS idx_friends_belt ON friends(belt_rank);
CREATE INDEX IF NOT EXISTS idx_friends_user_id ON friends(user_id);

-- Note: Foreign key constraints from sessions and session_rolls were dropped with CASCADE
-- TODO: Add separate migration to recreate these constraints pointing to friends table
-- For now, referential integrity is not enforced on partner_id and instructor_id

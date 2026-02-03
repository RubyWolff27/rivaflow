-- Migration 054: Fix streaks UNIQUE constraint properly
-- Created: 2026-02-04
-- Purpose: Remove incorrect UNIQUE constraint on streak_type column alone
--
-- SQLite doesn't support DROP CONSTRAINT, so we need to recreate the table

-- Step 1: Rename old table
ALTER TABLE streaks RENAME TO streaks_old;

-- Step 2: Create new table with correct schema (no UNIQUE on streak_type alone)
CREATE TABLE streaks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    streak_type TEXT NOT NULL,  -- Removed UNIQUE here
    current_streak INTEGER NOT NULL DEFAULT 0,
    longest_streak INTEGER NOT NULL DEFAULT 0,
    last_checkin_date TEXT,
    streak_started_date TEXT,
    grace_days_used INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
);

-- Step 3: Copy data from old table
INSERT INTO streaks (id, streak_type, current_streak, longest_streak, last_checkin_date,
                     streak_started_date, grace_days_used, updated_at, user_id)
SELECT id, streak_type, current_streak, longest_streak, last_checkin_date,
       streak_started_date, grace_days_used, updated_at, user_id
FROM streaks_old;

-- Step 4: Drop old table
DROP TABLE streaks_old;

-- Step 5: Recreate indexes
CREATE INDEX IF NOT EXISTS idx_streaks_user_id ON streaks(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_streaks_user_streak_type ON streaks(user_id, streak_type);
CREATE INDEX IF NOT EXISTS idx_streaks_user_type ON streaks(user_id, streak_type);

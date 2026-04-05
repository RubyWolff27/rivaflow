-- PostgreSQL version (auto-generated from sibling .sql file)
-- Translations applied: AUTOINCREMENT→BIGSERIAL, *_id INTEGER→BIGINT,
-- datetime('now')→CURRENT_TIMESTAMP, BOOLEAN 0/1→FALSE/TRUE,
-- PRAGMA/BEGIN/COMMIT removed, CREATE INDEX→IF NOT EXISTS.
-- Regenerate: bun /tmp/translate_sqlite_to_pg.py (see note in header)

-- Migration 054: Fix streaks UNIQUE constraint properly
-- Created: 2026-02-04
-- Purpose: Remove incorrect UNIQUE constraint on streak_type column alone
--
-- SQLite doesn't support DROP CONSTRAINT, so we need to recreate the table

-- Step 1: Rename old table
ALTER TABLE streaks RENAME TO streaks_old;

-- Step 2: Create new table with correct schema (no UNIQUE on streak_type alone)
CREATE TABLE streaks (
    id BIGSERIAL PRIMARY KEY,
    streak_type TEXT NOT NULL,  -- Removed UNIQUE here
    current_streak INTEGER NOT NULL DEFAULT 0,
    longest_streak INTEGER NOT NULL DEFAULT 0,
    last_checkin_date TEXT,
    streak_started_date TEXT,
    grace_days_used INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE
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

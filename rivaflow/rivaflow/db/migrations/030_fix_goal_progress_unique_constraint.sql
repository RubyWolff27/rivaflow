-- ============================================================
-- MIGRATION 030: Fix goal_progress unique constraint
-- Change from UNIQUE(week_start_date) to UNIQUE(user_id, week_start_date)
-- This allows multiple users to have goal progress for the same week
-- ============================================================

-- For PostgreSQL: Drop old constraint and add new one
-- For SQLite: Need to recreate the table since it doesn't support DROP CONSTRAINT

-- SQLite approach (recreate table):
CREATE TABLE IF NOT EXISTS goal_progress_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    week_start_date TEXT NOT NULL,
    week_end_date TEXT NOT NULL,
    target_sessions INTEGER NOT NULL,
    actual_sessions INTEGER NOT NULL DEFAULT 0,
    target_hours REAL NOT NULL,
    actual_hours REAL NOT NULL DEFAULT 0.0,
    target_rolls INTEGER NOT NULL,
    actual_rolls INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),

    UNIQUE(user_id, week_start_date)  -- One record per user per week
);

-- Copy existing data (explicitly list columns to handle different column order)
INSERT INTO goal_progress_new (
    id, user_id, week_start_date, week_end_date,
    target_sessions, actual_sessions, target_hours, actual_hours,
    target_rolls, actual_rolls, completed_at, created_at, updated_at
)
SELECT
    id, user_id, week_start_date, week_end_date,
    target_sessions, actual_sessions, target_hours, actual_hours,
    target_rolls, actual_rolls, completed_at, created_at, updated_at
FROM goal_progress;

-- Drop old table
DROP TABLE IF EXISTS goal_progress CASCADE;

-- Rename new table
ALTER TABLE goal_progress_new RENAME TO goal_progress;

-- Recreate indices
CREATE INDEX IF NOT EXISTS idx_goal_progress_user_id ON goal_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_goal_progress_week ON goal_progress(week_start_date);

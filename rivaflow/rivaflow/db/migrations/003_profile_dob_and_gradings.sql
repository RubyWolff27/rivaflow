-- Migration 003: Replace age with date_of_birth and add gradings table

-- Step 1: Add date_of_birth column to profile
ALTER TABLE profile ADD COLUMN date_of_birth TEXT;

-- Step 2: Create gradings table for tracking belt progression
CREATE TABLE IF NOT EXISTS gradings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grade TEXT NOT NULL,
    date_graded TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Create index on date_graded for efficient querying
CREATE INDEX IF NOT EXISTS idx_gradings_date ON gradings(date_graded DESC);

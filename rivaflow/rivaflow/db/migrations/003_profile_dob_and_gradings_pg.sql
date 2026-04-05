-- PostgreSQL version (auto-generated from sibling .sql file)
-- Translations applied: AUTOINCREMENT→BIGSERIAL, *_id INTEGER→BIGINT,
-- datetime('now')→CURRENT_TIMESTAMP, BOOLEAN 0/1→FALSE/TRUE,
-- PRAGMA/BEGIN/COMMIT removed, CREATE INDEX→IF NOT EXISTS.
-- Regenerate: bun /tmp/translate_sqlite_to_pg.py (see note in header)

-- Migration 003: Replace age with date_of_birth and add gradings table

-- Step 1: Add date_of_birth column to profile
ALTER TABLE profile ADD COLUMN date_of_birth TEXT;

-- Step 2: Create gradings table for tracking belt progression
CREATE TABLE IF NOT EXISTS gradings (
    id BIGSERIAL PRIMARY KEY,
    grade TEXT NOT NULL,
    date_graded TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CREATE INDEX IF NOT EXISTS on date_graded for efficient querying
CREATE INDEX IF NOT EXISTS idx_gradings_date ON gradings(date_graded DESC);

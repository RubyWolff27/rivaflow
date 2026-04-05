-- PostgreSQL version (auto-generated from sibling .sql file)
-- Translations applied: AUTOINCREMENT→BIGSERIAL, *_id INTEGER→BIGINT,
-- datetime('now')→CURRENT_TIMESTAMP, BOOLEAN 0/1→FALSE/TRUE,
-- PRAGMA/BEGIN/COMMIT removed, CREATE INDEX→IF NOT EXISTS.
-- Regenerate: bun /tmp/translate_sqlite_to_pg.py (see note in header)

-- ============================================================
-- MIGRATION 031: Fix readiness table unique constraint
-- Change from UNIQUE(check_date) to UNIQUE(user_id, check_date)
-- This allows multiple users to check in on the same date
-- ============================================================

-- For SQLite: Need to recreate the table since it doesn't support DROP CONSTRAINT

-- Create new readiness table with correct constraint
CREATE TABLE IF NOT EXISTS readiness_new (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    check_date TEXT NOT NULL,
    sleep INTEGER NOT NULL CHECK(sleep >= 1 AND sleep <= 5),
    stress INTEGER NOT NULL CHECK(stress >= 1 AND stress <= 5),
    soreness INTEGER NOT NULL CHECK(soreness >= 1 AND soreness <= 5),
    energy INTEGER NOT NULL CHECK(energy >= 1 AND energy <= 5),
    hotspot_note TEXT,
    weight_kg REAL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, check_date)  -- One check-in per user per date
);

-- Copy existing data (explicitly list columns to handle different column order)
INSERT INTO readiness_new (
    id, user_id, check_date, sleep, stress, soreness, energy,
    hotspot_note, weight_kg, created_at, updated_at
)
SELECT
    id, user_id, check_date, sleep, stress, soreness, energy,
    hotspot_note, weight_kg, created_at, updated_at
FROM readiness;

-- Drop old table
DROP TABLE IF EXISTS readiness;

-- Rename new table
ALTER TABLE readiness_new RENAME TO readiness;

-- Recreate indices
CREATE INDEX IF NOT EXISTS idx_readiness_user_id ON readiness(user_id);
CREATE INDEX IF NOT EXISTS idx_readiness_check_date ON readiness(check_date);

-- ============================================================
-- MIGRATION 031: Fix readiness table unique constraint
-- Change from UNIQUE(check_date) to UNIQUE(user_id, check_date)
-- This allows multiple users to check in on the same date
-- ============================================================

-- For SQLite: Need to recreate the table since it doesn't support DROP CONSTRAINT

-- Create new readiness table with correct constraint
CREATE TABLE IF NOT EXISTS readiness_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    check_date TEXT NOT NULL,
    sleep INTEGER NOT NULL CHECK(sleep >= 1 AND sleep <= 5),
    stress INTEGER NOT NULL CHECK(stress >= 1 AND stress <= 5),
    soreness INTEGER NOT NULL CHECK(soreness >= 1 AND stress <= 5),
    energy INTEGER NOT NULL CHECK(energy >= 1 AND energy <= 5),
    hotspot_note TEXT,
    weight_kg REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),

    UNIQUE(user_id, check_date)  -- One check-in per user per date
);

-- Copy existing data
INSERT INTO readiness_new
SELECT * FROM readiness;

-- Drop old table
DROP TABLE readiness;

-- Rename new table
ALTER TABLE readiness_new RENAME TO readiness;

-- Recreate indices
CREATE INDEX IF NOT EXISTS idx_readiness_user_id ON readiness(user_id);
CREATE INDEX IF NOT EXISTS idx_readiness_check_date ON readiness(check_date);

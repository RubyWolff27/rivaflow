-- ============================================================
-- MIGRATION 034: Fix movements_glossary custom movements
-- Change custom movements to be per-user
-- Seeded movements remain global, custom movements are user-scoped
-- Like Strava: system activities are global, custom activities per-user
-- ============================================================

-- For SQLite: Need to recreate the table since it doesn't support DROP CONSTRAINT

-- Add user_id column for custom movements (NULL for seeded movements)
-- Create new movements_glossary table with all original columns plus user_id
CREATE TABLE IF NOT EXISTS movements_glossary_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN (
        'position', 'submission', 'sweep', 'pass', 'takedown',
        'escape', 'movement', 'concept', 'defense'
    )),
    subcategory TEXT,
    points INTEGER DEFAULT 0,
    description TEXT,
    aliases TEXT,
    gi_applicable INTEGER DEFAULT 1,
    nogi_applicable INTEGER DEFAULT 1,
    ibjjf_legal_white INTEGER DEFAULT 1,
    ibjjf_legal_blue INTEGER DEFAULT 1,
    ibjjf_legal_purple INTEGER DEFAULT 1,
    ibjjf_legal_brown INTEGER DEFAULT 1,
    ibjjf_legal_black INTEGER DEFAULT 1,
    custom INTEGER DEFAULT 0,
    gi_video_url TEXT,
    nogi_video_url TEXT,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,  -- NEW: NULL for seeded, user_id for custom
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- Seeded movements: globally unique by name
    -- Custom movements: unique per user by name
    UNIQUE(name, custom, user_id)
);

-- Copy existing data (all columns from old table, NULL for new user_id column)
INSERT INTO movements_glossary_new (
    id, name, category, subcategory, points, description, aliases,
    gi_applicable, nogi_applicable,
    ibjjf_legal_white, ibjjf_legal_blue, ibjjf_legal_purple,
    ibjjf_legal_brown, ibjjf_legal_black,
    custom, gi_video_url, nogi_video_url,
    user_id, created_at
)
SELECT
    id, name, category, subcategory, points, description, aliases,
    gi_applicable, nogi_applicable,
    ibjjf_legal_white, ibjjf_legal_blue, ibjjf_legal_purple,
    ibjjf_legal_brown, ibjjf_legal_black,
    custom, gi_video_url, nogi_video_url,
    NULL as user_id,  -- NEW column: NULL for all existing (seeded) movements
    created_at
FROM movements_glossary;

-- Drop old table
DROP TABLE IF EXISTS movements_glossary;

-- Rename new table
ALTER TABLE movements_glossary_new RENAME TO movements_glossary;

-- Recreate indices
CREATE INDEX IF NOT EXISTS idx_movements_glossary_category ON movements_glossary(category);
CREATE INDEX IF NOT EXISTS idx_movements_glossary_name ON movements_glossary(name);
CREATE INDEX IF NOT EXISTS idx_movements_glossary_custom ON movements_glossary(custom);
CREATE INDEX IF NOT EXISTS idx_movements_glossary_user_id ON movements_glossary(user_id);

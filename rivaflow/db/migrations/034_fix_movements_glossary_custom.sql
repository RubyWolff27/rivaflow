-- ============================================================
-- MIGRATION 034: Fix movements_glossary custom movements
-- Change custom movements to be per-user
-- Seeded movements remain global, custom movements are user-scoped
-- Like Strava: system activities are global, custom activities per-user
-- ============================================================

-- For SQLite: Need to recreate the table since it doesn't support DROP CONSTRAINT

-- Add user_id column for custom movements (NULL for seeded movements)
-- Create new movements_glossary table with conditional unique constraint
CREATE TABLE IF NOT EXISTS movements_glossary_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    gi_video_url TEXT,
    nogi_video_url TEXT,
    custom INTEGER DEFAULT 0,  -- 0 = seeded/system, 1 = user-custom
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,  -- NULL for seeded, user_id for custom
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- Seeded movements: globally unique by name
    -- Custom movements: unique per user by name
    -- We enforce this at application level since SQLite doesn't support conditional constraints
    UNIQUE(name, custom, user_id)
);

-- Copy existing data (explicitly list columns, adding NULL for new user_id column)
INSERT INTO movements_glossary_new (
    id, name, category, description, gi_video_url, nogi_video_url,
    custom, user_id, created_at, updated_at
)
SELECT
    id, name, category, description, gi_video_url, nogi_video_url,
    custom,
    NULL as user_id,  -- New column: NULL for all existing (seeded) movements
    created_at, updated_at
FROM movements_glossary;

-- Drop old table (CASCADE for PostgreSQL foreign key constraints)
DROP TABLE IF EXISTS movements_glossary CASCADE;

-- Rename new table
ALTER TABLE movements_glossary_new RENAME TO movements_glossary;

-- Recreate indices
CREATE INDEX IF NOT EXISTS idx_movements_glossary_category ON movements_glossary(category);
CREATE INDEX IF NOT EXISTS idx_movements_glossary_custom ON movements_glossary(custom);
CREATE INDEX IF NOT EXISTS idx_movements_glossary_user_id ON movements_glossary(user_id);

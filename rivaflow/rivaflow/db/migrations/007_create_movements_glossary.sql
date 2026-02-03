-- Migration 007: Create movements glossary table

CREATE TABLE IF NOT EXISTS movements_glossary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL CHECK(category IN (
        'position', 'submission', 'sweep', 'pass', 'takedown',
        'escape', 'movement', 'concept', 'defense'
    )),
    subcategory TEXT,
    points INTEGER DEFAULT 0,
    description TEXT,
    aliases TEXT, -- JSON array of alternative names
    gi_applicable INTEGER DEFAULT 1, -- Boolean: 1 = yes, 0 = no
    nogi_applicable INTEGER DEFAULT 1, -- Boolean: 1 = yes, 0 = no
    ibjjf_legal_white INTEGER DEFAULT 1,
    ibjjf_legal_blue INTEGER DEFAULT 1,
    ibjjf_legal_purple INTEGER DEFAULT 1,
    ibjjf_legal_brown INTEGER DEFAULT 1,
    ibjjf_legal_black INTEGER DEFAULT 1,
    custom INTEGER DEFAULT 0, -- 0 = seeded, 1 = user-added
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Create indexes for efficient querying
CREATE INDEX idx_movements_category ON movements_glossary(category);
CREATE INDEX idx_movements_name ON movements_glossary(name);
CREATE INDEX idx_movements_custom ON movements_glossary(custom);

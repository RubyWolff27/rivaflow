-- PostgreSQL version (auto-generated from sibling .sql file)
-- Translations applied: AUTOINCREMENT→BIGSERIAL, *_id INTEGER→BIGINT,
-- datetime('now')→CURRENT_TIMESTAMP, BOOLEAN 0/1→FALSE/TRUE,
-- PRAGMA/BEGIN/COMMIT removed, CREATE INDEX→IF NOT EXISTS.
-- Regenerate: bun /tmp/translate_sqlite_to_pg.py (see note in header)

-- Session rolls table for detailed roll-by-roll tracking
CREATE TABLE IF NOT EXISTS session_rolls (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL,

    -- Partner information (either ID or fallback name)
    partner_id BIGINT,
    partner_name TEXT,  -- Fallback if no contact record

    -- Roll details
    roll_number INTEGER NOT NULL DEFAULT 1,
    duration_mins INTEGER,

    -- Submissions (stored as JSON arrays of movement IDs from glossary)
    submissions_for TEXT,  -- JSON: [movement_id1, movement_id2, ...]
    submissions_against TEXT,  -- JSON: [movement_id1, movement_id2, ...]

    -- Additional notes
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (partner_id) REFERENCES contacts(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_session_rolls_session ON session_rolls(session_id);
CREATE INDEX IF NOT EXISTS idx_session_rolls_partner ON session_rolls(partner_id);
CREATE INDEX IF NOT EXISTS idx_session_rolls_date ON session_rolls(created_at DESC);

-- Migration: Create session_techniques table
-- Purpose: Track multiple techniques per session with detailed notes and media URLs
-- Date: 2026-01-25

CREATE TABLE IF NOT EXISTS session_techniques (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    movement_id INTEGER NOT NULL,
    technique_number INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    media_urls TEXT,  -- JSON array: [{"type": "video"|"image", "url": "...", "title": "..."}]
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (movement_id) REFERENCES movements_glossary(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_session_techniques_session ON session_techniques(session_id);
CREATE INDEX IF NOT EXISTS idx_session_techniques_movement ON session_techniques(movement_id);

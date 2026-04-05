-- PostgreSQL version (auto-generated from sibling .sql file)
-- Translations applied: AUTOINCREMENT→BIGSERIAL, *_id INTEGER→BIGINT,
-- datetime('now')→CURRENT_TIMESTAMP, BOOLEAN 0/1→FALSE/TRUE,
-- PRAGMA/BEGIN/COMMIT removed, CREATE INDEX→IF NOT EXISTS.
-- Regenerate: bun /tmp/translate_sqlite_to_pg.py (see note in header)

-- Migration: Create movement_videos table for custom video links
-- Purpose: Allow users to add their own preferred instructional video links per movement
-- Date: 2026-01-25

CREATE TABLE IF NOT EXISTS movement_videos (
    id BIGSERIAL PRIMARY KEY,
    movement_id BIGINT NOT NULL,
    title TEXT,
    url TEXT NOT NULL,
    video_type TEXT CHECK(video_type IN ('gi', 'nogi', 'general')) DEFAULT 'general',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (movement_id) REFERENCES movements_glossary(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_movement_videos_movement ON movement_videos(movement_id);

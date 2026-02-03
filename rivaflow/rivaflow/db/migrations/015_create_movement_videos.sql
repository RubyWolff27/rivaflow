-- Migration: Create movement_videos table for custom video links
-- Purpose: Allow users to add their own preferred instructional video links per movement
-- Date: 2026-01-25

CREATE TABLE IF NOT EXISTS movement_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movement_id INTEGER NOT NULL,
    title TEXT,
    url TEXT NOT NULL,
    video_type TEXT CHECK(video_type IN ('gi', 'nogi', 'general')) DEFAULT 'general',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (movement_id) REFERENCES movements_glossary(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_movement_videos_movement ON movement_videos(movement_id);

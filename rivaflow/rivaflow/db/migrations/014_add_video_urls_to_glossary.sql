-- Migration: Add video URL columns to movements_glossary
-- Purpose: Store reference YouTube URLs for gi and no-gi instructional videos
-- Date: 2026-01-25

ALTER TABLE movements_glossary ADD COLUMN gi_video_url TEXT;
ALTER TABLE movements_glossary ADD COLUMN nogi_video_url TEXT;

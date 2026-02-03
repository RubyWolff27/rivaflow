-- Migration 053: Add instructor_id and photo_url to gradings table
-- Created: 2026-02-03
-- Purpose: Support instructor tracking and photo uploads for belt gradings

-- Add instructor_id column
ALTER TABLE gradings ADD COLUMN instructor_id INTEGER REFERENCES friends(id) ON DELETE SET NULL;

-- Add photo_url column
ALTER TABLE gradings ADD COLUMN photo_url TEXT;

-- Create index on instructor_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_gradings_instructor ON gradings(instructor_id);

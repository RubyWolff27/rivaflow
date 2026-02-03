-- Migration 023: Add missing current_professor column to profile table
-- This column was lost during migration 019's table recreation

ALTER TABLE profile ADD COLUMN current_professor TEXT;

-- Migration 004: Add professor tracking to profile and gradings

-- Add current_professor to profile
ALTER TABLE profile ADD COLUMN current_professor TEXT;

-- Add professor to gradings table
ALTER TABLE gradings ADD COLUMN professor TEXT;

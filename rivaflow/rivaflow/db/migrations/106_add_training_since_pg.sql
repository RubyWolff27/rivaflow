-- Add training_since column to profile table (PG only)
ALTER TABLE profile ADD COLUMN IF NOT EXISTS training_since TEXT;

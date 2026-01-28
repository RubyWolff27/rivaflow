-- Migration 025: Add instructor_id to profile for coach tracking
-- Links profile coach to contacts table for better reporting

ALTER TABLE profile ADD COLUMN current_instructor_id INTEGER;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_profile_instructor_id ON profile(current_instructor_id);

-- Foreign key constraint (note: SQLite doesn't enforce FK without PRAGMA, but good for documentation)
-- FOREIGN KEY (current_instructor_id) REFERENCES contacts(id) ON DELETE SET NULL

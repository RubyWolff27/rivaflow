-- ============================================================
-- MIGRATION 047: Add primary_training_type to profile table (PostgreSQL)
-- Allows users to set their default class type for logging
-- ============================================================

-- Add primary_training_type column
ALTER TABLE profile ADD COLUMN IF NOT EXISTS primary_training_type TEXT DEFAULT 'gi';

-- Add comment
COMMENT ON COLUMN profile.primary_training_type IS 'Default class type when logging sessions (gi, no-gi, s&c, etc.)';

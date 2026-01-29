-- ============================================================
-- MIGRATION 027: Fix streaks unique constraint for multi-user
-- Change UNIQUE(streak_type) to UNIQUE(user_id, streak_type)
-- ============================================================

-- Drop the old unique constraint on streak_type
-- PostgreSQL: Drop constraint by name
-- SQLite: Requires table recreation (handled by conversion logic)

-- For PostgreSQL
ALTER TABLE streaks DROP CONSTRAINT IF EXISTS streaks_streak_type_key;

-- Add new unique constraint on (user_id, streak_type)
-- This allows each user to have their own set of streak types
CREATE UNIQUE INDEX IF NOT EXISTS idx_streaks_user_streak_type ON streaks(user_id, streak_type);

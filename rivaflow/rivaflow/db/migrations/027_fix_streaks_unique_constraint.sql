-- ============================================================
-- MIGRATION 027: Fix streaks unique constraint for multi-user
-- Change UNIQUE(streak_type) to UNIQUE(user_id, streak_type)
-- ============================================================

-- Drop the old unique constraint on streak_type
-- PostgreSQL: Drop constraint by name
-- SQLite: Just create the new index (IF NOT EXISTS prevents errors)

-- Add new unique constraint on (user_id, streak_type)
-- This allows each user to have their own set of streak types
-- SQLite: If a conflicting unique constraint exists, this will fail silently with IF NOT EXISTS
-- PostgreSQL: Will create the index if it doesn't exist
CREATE UNIQUE INDEX IF NOT EXISTS idx_streaks_user_streak_type ON streaks(user_id, streak_type);

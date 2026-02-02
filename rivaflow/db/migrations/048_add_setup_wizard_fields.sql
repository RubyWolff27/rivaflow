-- ============================================================
-- MIGRATION 048: Add setup wizard fields to profile table
-- Supports onboarding wizard and weekly goal tracking
-- ============================================================

-- Add setup completion tracking
ALTER TABLE profile ADD COLUMN IF NOT EXISTS setup_completed BOOLEAN DEFAULT 0;

-- Add weekly goal fields (separate from generic targets)
ALTER TABLE profile ADD COLUMN IF NOT EXISTS weekly_bjj_goal INTEGER DEFAULT 3;
ALTER TABLE profile ADD COLUMN IF NOT EXISTS weekly_sc_goal INTEGER DEFAULT 2;
ALTER TABLE profile ADD COLUMN IF NOT EXISTS weekly_mobility_goal INTEGER DEFAULT 60;

-- Add belt tracking fields (if not already present)
ALTER TABLE profile ADD COLUMN IF NOT EXISTS belt_rank TEXT DEFAULT 'white';
ALTER TABLE profile ADD COLUMN IF NOT EXISTS belt_stripes INTEGER DEFAULT 0;

-- Add gym name field (if not already present from default_gym)
ALTER TABLE profile ADD COLUMN IF NOT EXISTS gym_name TEXT;

-- Migrate default_gym to gym_name if gym_name is null
UPDATE profile
SET gym_name = default_gym
WHERE gym_name IS NULL AND default_gym IS NOT NULL;

-- ============================================================
-- MIGRATION 048: Add setup wizard fields to profile table (PostgreSQL)
-- Supports onboarding wizard and weekly goal tracking
-- ============================================================

-- Add setup completion tracking
ALTER TABLE profile ADD COLUMN IF NOT EXISTS setup_completed BOOLEAN DEFAULT FALSE;

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

-- Add comments
COMMENT ON COLUMN profile.setup_completed IS 'Whether user has completed onboarding wizard';
COMMENT ON COLUMN profile.weekly_bjj_goal IS 'Target BJJ/Grappling sessions per week';
COMMENT ON COLUMN profile.weekly_sc_goal IS 'Target S&C sessions per week';
COMMENT ON COLUMN profile.weekly_mobility_goal IS 'Target mobility minutes per week';
COMMENT ON COLUMN profile.belt_rank IS 'Current belt rank (white, blue, purple, brown, black)';
COMMENT ON COLUMN profile.belt_stripes IS 'Number of stripes on current belt (0-4)';
COMMENT ON COLUMN profile.gym_name IS 'Primary gym/academy name';

-- Migration 052: Add Activity-Specific Weekly Goals
-- Created: 2026-02-03
-- Purpose: Allow users to set specific goals for BJJ, S&C, and Mobility sessions

-- Add activity-specific goal columns to profile table
ALTER TABLE profile ADD COLUMN weekly_bjj_sessions_target INTEGER DEFAULT 3;
ALTER TABLE profile ADD COLUMN weekly_sc_sessions_target INTEGER DEFAULT 1;
ALTER TABLE profile ADD COLUMN weekly_mobility_sessions_target INTEGER DEFAULT 0;

-- Update existing records to have sensible defaults based on weekly_sessions_target
-- If they had a goal of 5 sessions, split as: 3 BJJ, 2 S&C, 0 Mobility
UPDATE profile
SET
    weekly_bjj_sessions_target = CASE
        WHEN weekly_sessions_target >= 3 THEN 3
        ELSE weekly_sessions_target
    END,
    weekly_sc_sessions_target = CASE
        WHEN weekly_sessions_target >= 5 THEN 2
        WHEN weekly_sessions_target >= 4 THEN 1
        ELSE 0
    END,
    weekly_mobility_sessions_target = 0
WHERE weekly_sessions_target IS NOT NULL;

-- Add comments
COMMENT ON COLUMN profile.weekly_bjj_sessions_target IS 'Target number of BJJ sessions per week (Gi, No-Gi, Open Mat, Competition)';
COMMENT ON COLUMN profile.weekly_sc_sessions_target IS 'Target number of Strength & Conditioning sessions per week';
COMMENT ON COLUMN profile.weekly_mobility_sessions_target IS 'Target number of Mobility/Recovery sessions per week';

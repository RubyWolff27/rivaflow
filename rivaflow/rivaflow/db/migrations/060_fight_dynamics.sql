-- Migration 060: Add fight dynamics columns to sessions table
-- Tracks attack and defence metrics for the Attack vs Defence Heatmap feature

ALTER TABLE sessions ADD COLUMN attacks_attempted INTEGER DEFAULT 0;
ALTER TABLE sessions ADD COLUMN attacks_successful INTEGER DEFAULT 0;
ALTER TABLE sessions ADD COLUMN defenses_attempted INTEGER DEFAULT 0;
ALTER TABLE sessions ADD COLUMN defenses_successful INTEGER DEFAULT 0;

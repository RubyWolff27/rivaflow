-- Add target weight date to profile (PostgreSQL)
ALTER TABLE profile ADD COLUMN IF NOT EXISTS target_weight_date TEXT;

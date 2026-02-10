-- Add gi/no-gi preference columns to coach_preferences (PostgreSQL)
ALTER TABLE coach_preferences ADD COLUMN IF NOT EXISTS gi_nogi_preference TEXT DEFAULT 'both';
ALTER TABLE coach_preferences ADD COLUMN IF NOT EXISTS gi_bias_pct INTEGER DEFAULT 50;

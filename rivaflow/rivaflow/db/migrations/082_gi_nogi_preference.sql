-- Add gi/no-gi preference columns to coach_preferences
ALTER TABLE coach_preferences ADD COLUMN gi_nogi_preference TEXT DEFAULT 'both';
ALTER TABLE coach_preferences ADD COLUMN gi_bias_pct INTEGER DEFAULT 50;

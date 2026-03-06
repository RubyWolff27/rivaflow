-- Add partner_user_id to session_rolls to link roll partners to actual user accounts
ALTER TABLE session_rolls ADD COLUMN IF NOT EXISTS partner_user_id INTEGER;
CREATE INDEX IF NOT EXISTS idx_session_rolls_partner_user ON session_rolls(partner_user_id);

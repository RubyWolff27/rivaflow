-- Add partner_user_id to session_rolls to link roll partners to actual user accounts
-- partner_id stays as friends.id (local friend record); partner_user_id is users.id (app user)
ALTER TABLE session_rolls ADD COLUMN partner_user_id INTEGER;
CREATE INDEX IF NOT EXISTS idx_session_rolls_partner_user ON session_rolls(partner_user_id);

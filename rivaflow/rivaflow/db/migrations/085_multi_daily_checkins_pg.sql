-- ============================================================
-- MIGRATION 085 (PostgreSQL): Multi-daily check-ins
-- Adds checkin_slot column + new fields for midday and evening slots.
-- ============================================================

-- Add new columns
ALTER TABLE daily_checkins ADD COLUMN IF NOT EXISTS checkin_slot TEXT NOT NULL DEFAULT 'morning';
ALTER TABLE daily_checkins ADD COLUMN IF NOT EXISTS energy_level INTEGER;
ALTER TABLE daily_checkins ADD COLUMN IF NOT EXISTS midday_note TEXT;
ALTER TABLE daily_checkins ADD COLUMN IF NOT EXISTS training_quality INTEGER;
ALTER TABLE daily_checkins ADD COLUMN IF NOT EXISTS recovery_note TEXT;

-- Drop old unique constraint and add new one with slot
ALTER TABLE daily_checkins DROP CONSTRAINT IF EXISTS daily_checkins_user_id_check_date_key;
ALTER TABLE daily_checkins ADD CONSTRAINT daily_checkins_user_id_check_date_slot_key UNIQUE (user_id, check_date, checkin_slot);

-- Add composite index for fast lookups
CREATE INDEX IF NOT EXISTS idx_daily_checkins_user_date ON daily_checkins(user_id, check_date);

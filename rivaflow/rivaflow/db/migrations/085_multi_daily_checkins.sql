-- ============================================================
-- MIGRATION 085: Multi-daily check-ins (morning / midday / evening)
-- Adds checkin_slot column + new fields for midday and evening slots.
-- Changes UNIQUE(user_id, check_date) → UNIQUE(user_id, check_date, checkin_slot)
-- Uses CREATE-RENAME pattern (same as migration 020) since SQLite
-- can't DROP CONSTRAINT.
-- ============================================================

-- Create new table with slot column and new fields
CREATE TABLE IF NOT EXISTS daily_checkins_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    check_date TEXT NOT NULL,
    checkin_type TEXT NOT NULL,
    checkin_slot TEXT NOT NULL DEFAULT 'morning',
    rest_type TEXT,
    rest_note TEXT,
    session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    readiness_id INTEGER REFERENCES readiness(id) ON DELETE SET NULL,
    tomorrow_intention TEXT,
    insight_shown TEXT,
    energy_level INTEGER,
    midday_note TEXT,
    training_quality INTEGER,
    recovery_note TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, check_date, checkin_slot)
);

-- Copy existing rows as morning slot
INSERT INTO daily_checkins_new (
    id, user_id, check_date, checkin_type, checkin_slot,
    rest_type, rest_note, session_id, readiness_id,
    tomorrow_intention, insight_shown, created_at
)
SELECT
    id, user_id, check_date, checkin_type, 'morning',
    rest_type, rest_note, session_id, readiness_id,
    tomorrow_intention, insight_shown, created_at
FROM daily_checkins;

-- Drop old table
DROP TABLE daily_checkins;

-- Rename new table
ALTER TABLE daily_checkins_new RENAME TO daily_checkins;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_daily_checkins_date ON daily_checkins(check_date);
CREATE INDEX IF NOT EXISTS idx_daily_checkins_user_id ON daily_checkins(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_checkins_user_date ON daily_checkins(user_id, check_date);

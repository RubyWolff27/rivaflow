-- PostgreSQL version (auto-generated from sibling .sql file)
-- Translations applied: AUTOINCREMENT→BIGSERIAL, *_id INTEGER→BIGINT,
-- datetime('now')→CURRENT_TIMESTAMP, BOOLEAN 0/1→FALSE/TRUE,
-- PRAGMA/BEGIN/COMMIT removed, CREATE INDEX→IF NOT EXISTS.
-- Regenerate: bun /tmp/translate_sqlite_to_pg.py (see note in header)

-- ============================================================
-- MIGRATION 020: Fix daily_checkins unique constraint
-- Change from UNIQUE(check_date) to UNIQUE(user_id, check_date)
-- ============================================================

-- SQLite doesn't support dropping constraints, so we need to recreate the table

-- Create new table with correct constraint
CREATE TABLE IF NOT EXISTS daily_checkins_new (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    check_date TEXT NOT NULL,                -- ISO 8601: YYYY-MM-DD
    checkin_type TEXT NOT NULL,              -- 'session', 'rest', 'readiness'
    rest_type TEXT,                          -- 'recovery', 'life', 'injury', 'travel' (if rest)
    rest_note TEXT,                          -- Optional note for rest days
    session_id BIGINT REFERENCES sessions(id) ON DELETE SET NULL,
    readiness_id BIGINT REFERENCES readiness(id) ON DELETE SET NULL,
    tomorrow_intention TEXT,                 -- 'train_gi', 'train_nogi', 'rest', 'unsure', etc.
    insight_shown TEXT,                      -- JSON: insight that was displayed
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, check_date)              -- One check-in per user per date
);

-- Copy data from old table
INSERT INTO daily_checkins_new (id, user_id, check_date, checkin_type, rest_type, rest_note, session_id, readiness_id, tomorrow_intention, insight_shown, created_at)
SELECT id, user_id, check_date, checkin_type, rest_type, rest_note, session_id, readiness_id, tomorrow_intention, insight_shown, created_at
FROM daily_checkins;

-- Drop old table
DROP TABLE daily_checkins;

-- Rename new table
ALTER TABLE daily_checkins_new RENAME TO daily_checkins;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_daily_checkins_date ON daily_checkins(check_date);
CREATE INDEX IF NOT EXISTS idx_daily_checkins_user_id ON daily_checkins(user_id);

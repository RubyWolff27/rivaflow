-- PostgreSQL version (auto-generated from sibling .sql file)
-- Translations applied: AUTOINCREMENT→BIGSERIAL, *_id INTEGER→BIGINT,
-- datetime('now')→CURRENT_TIMESTAMP, BOOLEAN 0/1→FALSE/TRUE,
-- PRAGMA/BEGIN/COMMIT removed, CREATE INDEX→IF NOT EXISTS.
-- Regenerate: bun /tmp/translate_sqlite_to_pg.py (see note in header)

-- ============================================================
-- MIGRATION 017: Engagement Features
-- Daily check-ins, streaks, and milestones for habit formation
-- ============================================================

-- DAILY_CHECKINS: Unified daily engagement tracking
CREATE TABLE IF NOT EXISTS daily_checkins (
    id BIGSERIAL PRIMARY KEY,
    check_date TEXT NOT NULL UNIQUE,         -- ISO 8601: YYYY-MM-DD
    checkin_type TEXT NOT NULL,              -- 'session', 'rest', 'readiness_only'
    rest_type TEXT,                          -- 'recovery', 'life', 'injury', 'travel' (if rest)
    rest_note TEXT,                          -- Optional note for rest days
    session_id BIGINT REFERENCES sessions(id) ON DELETE SET NULL,
    readiness_id BIGINT REFERENCES readiness(id) ON DELETE SET NULL,
    tomorrow_intention TEXT,                 -- 'train_gi', 'train_nogi', 'rest', 'unsure', etc.
    insight_shown TEXT,                      -- JSON: insight that was displayed
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- STREAKS: Streak tracking
CREATE TABLE IF NOT EXISTS streaks (
    id BIGSERIAL PRIMARY KEY,
    streak_type TEXT NOT NULL UNIQUE,        -- 'checkin', 'training', 'readiness'
    current_streak INTEGER NOT NULL DEFAULT 0,
    longest_streak INTEGER NOT NULL DEFAULT 0,
    last_checkin_date TEXT,                  -- ISO 8601: YYYY-MM-DD
    streak_started_date TEXT,                -- ISO 8601: YYYY-MM-DD
    grace_days_used INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- MILESTONES: Achievement tracking
CREATE TABLE IF NOT EXISTS milestones (
    id BIGSERIAL PRIMARY KEY,
    milestone_type TEXT NOT NULL,            -- 'hours', 'sessions', 'streak', 'rolls', 'partners', 'techniques'
    milestone_value INTEGER NOT NULL,        -- 10, 50, 100, etc.
    milestone_label TEXT,                    -- "100 Hours on the Mat"
    achieved_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    celebrated INTEGER NOT NULL DEFAULT 0,   -- 0 = not shown yet, 1 = shown
    UNIQUE(milestone_type, milestone_value)
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_daily_checkins_date ON daily_checkins(check_date);
CREATE INDEX IF NOT EXISTS idx_milestones_type ON milestones(milestone_type);
CREATE INDEX IF NOT EXISTS idx_milestones_celebrated ON milestones(celebrated);

-- SEED: Initialize streak types
INSERT OR IGNORE INTO streaks (streak_type, current_streak, longest_streak) VALUES ('checkin', 0, 0);
INSERT OR IGNORE INTO streaks (streak_type, current_streak, longest_streak) VALUES ('training', 0, 0);
INSERT OR IGNORE INTO streaks (streak_type, current_streak, longest_streak) VALUES ('readiness', 0, 0);

-- Add weekly goal targets to profile table
-- Migration 013: Weekly Goals & Streak Tracking

ALTER TABLE profile ADD COLUMN weekly_sessions_target INTEGER DEFAULT 3;
ALTER TABLE profile ADD COLUMN weekly_hours_target REAL DEFAULT 4.5;
ALTER TABLE profile ADD COLUMN weekly_rolls_target INTEGER DEFAULT 15;
ALTER TABLE profile ADD COLUMN show_streak_on_dashboard BOOLEAN DEFAULT 1;
ALTER TABLE profile ADD COLUMN show_weekly_goals BOOLEAN DEFAULT 1;

-- Add goal progress tracking table
CREATE TABLE IF NOT EXISTS goal_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start_date TEXT NOT NULL,  -- Monday of the week (YYYY-MM-DD)
    week_end_date TEXT NOT NULL,    -- Sunday of the week (YYYY-MM-DD)
    target_sessions INTEGER NOT NULL,
    actual_sessions INTEGER NOT NULL DEFAULT 0,
    target_hours REAL NOT NULL,
    actual_hours REAL NOT NULL DEFAULT 0.0,
    target_rolls INTEGER NOT NULL,
    actual_rolls INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,  -- When all goals were met (YYYY-MM-DD HH:MM:SS)
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),

    UNIQUE(week_start_date)  -- One record per week
);

CREATE INDEX IF NOT EXISTS idx_goal_progress_week ON goal_progress(week_start_date);

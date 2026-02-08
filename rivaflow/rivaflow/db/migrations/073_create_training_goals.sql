-- Migration 073: Create training_goals table for monthly goals tracking
-- Supports frequency-based goals (sessions, hours, rolls, submissions)
-- and technique-focused goals (practice a specific movement N times)

CREATE TABLE IF NOT EXISTS training_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_type TEXT NOT NULL CHECK (goal_type IN ('frequency', 'technique')),
    metric TEXT NOT NULL CHECK (metric IN ('sessions', 'hours', 'rolls', 'submissions', 'technique_count')),
    target_value INTEGER NOT NULL CHECK (target_value > 0),
    month TEXT NOT NULL,  -- Format: 'YYYY-MM'
    movement_id INTEGER REFERENCES movements_glossary(id) ON DELETE CASCADE,
    class_type_filter TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Prevent duplicate goals for the same user/month/metric/movement/class_type combo
CREATE UNIQUE INDEX IF NOT EXISTS idx_training_goals_unique
    ON training_goals(user_id, month, metric, COALESCE(movement_id, 0), COALESCE(class_type_filter, ''));

-- Fast lookup for listing goals by month
CREATE INDEX IF NOT EXISTS idx_training_goals_user_month
    ON training_goals(user_id, month);

-- Fast lookup for active goals
CREATE INDEX IF NOT EXISTS idx_training_goals_user_active
    ON training_goals(user_id, is_active);

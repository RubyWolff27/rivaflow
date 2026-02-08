-- Migration 073: Create training_goals table for monthly goals tracking (PostgreSQL)

CREATE TABLE IF NOT EXISTS training_goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_type TEXT NOT NULL CHECK (goal_type IN ('frequency', 'technique')),
    metric TEXT NOT NULL CHECK (metric IN ('sessions', 'hours', 'rolls', 'submissions', 'technique_count')),
    target_value INTEGER NOT NULL CHECK (target_value > 0),
    month TEXT NOT NULL,
    movement_id INTEGER REFERENCES movements_glossary(id) ON DELETE CASCADE,
    class_type_filter TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_training_goals_unique
    ON training_goals(user_id, month, metric, COALESCE(movement_id, 0), COALESCE(class_type_filter, ''));

CREATE INDEX IF NOT EXISTS idx_training_goals_user_month
    ON training_goals(user_id, month);

CREATE INDEX IF NOT EXISTS idx_training_goals_user_active
    ON training_goals(user_id, is_active);

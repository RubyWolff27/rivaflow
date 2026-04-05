-- PostgreSQL version (auto-generated from sibling .sql file)
-- Translations applied: AUTOINCREMENT→BIGSERIAL, *_id INTEGER→BIGINT,
-- datetime('now')→CURRENT_TIMESTAMP, BOOLEAN 0/1→FALSE/TRUE,
-- PRAGMA/BEGIN/COMMIT removed, CREATE INDEX→IF NOT EXISTS.
-- Regenerate: bun /tmp/translate_sqlite_to_pg.py (see note in header)

-- Coach Preferences: personalization for Grapple AI coaching

CREATE TABLE IF NOT EXISTS coach_preferences (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,

    -- Training Mode: competition_prep | lifestyle | skill_development | recovery
    training_mode TEXT NOT NULL DEFAULT 'lifestyle',

    -- Competition context (only when training_mode = 'competition_prep')
    comp_date TEXT,
    comp_name TEXT,
    comp_division TEXT,
    comp_weight_class TEXT,

    -- Coaching style: balanced | motivational | analytical | tough_love | technical
    coaching_style TEXT NOT NULL DEFAULT 'balanced',

    -- Game focus
    primary_position TEXT DEFAULT 'both',
    focus_areas TEXT,
    weaknesses TEXT,

    -- Persistent injuries (JSON array)
    injuries TEXT,

    -- Training context
    years_training REAL,
    competition_experience TEXT DEFAULT 'none',
    available_days_per_week INTEGER DEFAULT 4,

    -- Why they train (JSON array)
    motivations TEXT,

    -- Freeform
    additional_context TEXT,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_coach_preferences_user_id
    ON coach_preferences(user_id);

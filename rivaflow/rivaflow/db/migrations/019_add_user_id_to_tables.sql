-- ============================================================
-- MIGRATION 019: Add user_id to All Tables
-- Convert from single-user to multi-user data model
-- ============================================================

-- Add user_id to sessions
ALTER TABLE sessions ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1 REFERENCES users(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

-- Add user_id to readiness
ALTER TABLE readiness ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1 REFERENCES users(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_readiness_user_id ON readiness(user_id);

-- Add user_id to contacts
ALTER TABLE contacts ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1 REFERENCES users(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_contacts_user_id ON contacts(user_id);

-- Add user_id to gradings
ALTER TABLE gradings ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1 REFERENCES users(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_gradings_user_id ON gradings(user_id);

-- Add user_id to daily_checkins
ALTER TABLE daily_checkins ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1 REFERENCES users(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_daily_checkins_user_id ON daily_checkins(user_id);

-- Add user_id to streaks
ALTER TABLE streaks ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1 REFERENCES users(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_streaks_user_id ON streaks(user_id);

-- Add user_id to milestones
ALTER TABLE milestones ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1 REFERENCES users(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_milestones_user_id ON milestones(user_id);

-- Add user_id to goal_progress
ALTER TABLE goal_progress ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1 REFERENCES users(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_goal_progress_user_id ON goal_progress(user_id);

-- Profile table needs special handling due to CHECK constraint
-- SQLite doesn't support DROP CONSTRAINT, so we need to recreate the table

-- Step 1: Create new profile table with user_id
CREATE TABLE IF NOT EXISTS profile_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,  -- One profile per user
    date_of_birth TEXT,
    sex TEXT CHECK(sex IN ('male', 'female', 'other', 'prefer_not_to_say')),
    default_gym TEXT,
    current_grade TEXT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    location TEXT,
    state TEXT,
    weekly_sessions_target INTEGER DEFAULT 3,
    weekly_hours_target REAL DEFAULT 4.5,
    weekly_rolls_target INTEGER DEFAULT 15,
    show_streak_on_dashboard BOOLEAN DEFAULT 1,
    show_weekly_goals BOOLEAN DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Step 2: Copy data from old profile table to new one (map id=1 to user_id=1)
INSERT INTO profile_new (
    id, user_id, date_of_birth, sex, default_gym, current_grade,
    first_name, last_name, email, location, state,
    weekly_sessions_target, weekly_hours_target, weekly_rolls_target,
    show_streak_on_dashboard, show_weekly_goals, created_at, updated_at
)
SELECT
    id, 1 as user_id, date_of_birth, sex, default_gym, current_grade,
    first_name, last_name, NULL as email, city as location, state,
    weekly_sessions_target, weekly_hours_target, weekly_rolls_target,
    show_streak_on_dashboard, show_weekly_goals, created_at, updated_at
FROM profile
WHERE id = 1;

-- Step 3: Drop old profile table
DROP TABLE profile;

-- Step 4: Rename new table to profile
ALTER TABLE profile_new RENAME TO profile;

-- Step 5: Create index for user_id lookups
CREATE INDEX IF NOT EXISTS idx_profile_user_id ON profile(user_id);

-- Update unique constraints for multi-user support
-- Contacts: name must be unique per user (not globally)
-- Note: SQLite doesn't support modifying constraints, so this is documented for future reference
-- Current implementation keeps global uniqueness for simplicity

-- Update streaks table: streak_type should be unique per user
-- Note: This requires recreating the table in a future migration if needed
-- For now, we'll handle uniqueness at the application level

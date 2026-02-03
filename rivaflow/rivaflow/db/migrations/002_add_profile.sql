-- Add user profile table

CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- Single row table
    age INTEGER,
    sex TEXT CHECK(sex IN ('male', 'female', 'other', 'prefer_not_to_say')),
    default_gym TEXT,
    current_grade TEXT,  -- Belt/grade: white, blue, purple, brown, black, etc.
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Insert default profile
INSERT OR IGNORE INTO profile (id) VALUES (1);

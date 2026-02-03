-- Migration 024: Add activity photos table
-- Support uploading 1-3 photos for any activity (session, readiness, rest)

CREATE TABLE IF NOT EXISTS activity_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    activity_type TEXT NOT NULL CHECK(activity_type IN ('session', 'readiness', 'rest')),
    activity_id INTEGER NOT NULL,
    activity_date TEXT NOT NULL,  -- For easier querying
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    caption TEXT,
    display_order INTEGER DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_activity_photos_user_id ON activity_photos(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_photos_activity ON activity_photos(activity_type, activity_id);
CREATE INDEX IF NOT EXISTS idx_activity_photos_date ON activity_photos(activity_date);

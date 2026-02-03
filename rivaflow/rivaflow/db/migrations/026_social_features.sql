-- Social features: user relationships, activity likes, and activity comments

-- User relationships table (social graph for following)
CREATE TABLE IF NOT EXISTS user_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    follower_user_id INTEGER NOT NULL,      -- User who follows
    following_user_id INTEGER NOT NULL,     -- User being followed
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'blocked')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (follower_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (following_user_id) REFERENCES users(id) ON DELETE CASCADE,

    CHECK (follower_user_id != following_user_id),
    UNIQUE(follower_user_id, following_user_id)
);

-- Activity likes table (polymorphic likes for any activity type)
CREATE TABLE IF NOT EXISTS activity_likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    activity_type TEXT NOT NULL CHECK(activity_type IN ('session', 'readiness', 'rest')),
    activity_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, activity_type, activity_id)
);

-- Activity comments table (polymorphic comments for any activity type)
CREATE TABLE IF NOT EXISTS activity_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    activity_type TEXT NOT NULL CHECK(activity_type IN ('session', 'readiness', 'rest')),
    activity_id INTEGER NOT NULL,
    comment_text TEXT NOT NULL CHECK(length(comment_text) > 0 AND length(comment_text) <= 1000),
    parent_comment_id INTEGER,              -- For nested replies (future)
    edited_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_comment_id) REFERENCES activity_comments(id) ON DELETE CASCADE
);

-- Indexes for performance on user_relationships
CREATE INDEX IF NOT EXISTS idx_user_relationships_follower ON user_relationships(follower_user_id);
CREATE INDEX IF NOT EXISTS idx_user_relationships_following ON user_relationships(following_user_id);
CREATE INDEX IF NOT EXISTS idx_user_relationships_status ON user_relationships(status);

-- Indexes for performance on activity_likes
CREATE INDEX IF NOT EXISTS idx_activity_likes_user ON activity_likes(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_likes_activity ON activity_likes(activity_type, activity_id);
CREATE INDEX IF NOT EXISTS idx_activity_likes_created ON activity_likes(created_at);

-- Indexes for performance on activity_comments
CREATE INDEX IF NOT EXISTS idx_activity_comments_user ON activity_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_comments_activity ON activity_comments(activity_type, activity_id);
CREATE INDEX IF NOT EXISTS idx_activity_comments_parent ON activity_comments(parent_comment_id);
CREATE INDEX IF NOT EXISTS idx_activity_comments_created ON activity_comments(created_at);

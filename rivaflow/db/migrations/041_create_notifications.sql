-- Migration: Create notifications table
-- Description: Track user notifications for social interactions (likes, comments, follows)
-- Author: RivaFlow Team
-- Date: 2026-02-01

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    actor_id INTEGER NOT NULL,
    notification_type TEXT NOT NULL CHECK(notification_type IN ('like', 'comment', 'follow', 'reply', 'mention')),
    activity_type TEXT CHECK(activity_type IN ('session', 'readiness', 'rest') OR activity_type IS NULL),
    activity_id INTEGER,
    comment_id INTEGER,
    message TEXT,
    is_read BOOLEAN DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    read_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read, created_at DESC);
CREATE INDEX idx_notifications_actor ON notifications(actor_id);
CREATE INDEX idx_notifications_type ON notifications(notification_type);
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);

-- Composite index for efficient querying of unread notifications
CREATE INDEX idx_notifications_user_unread_created ON notifications(user_id, is_read, created_at DESC);

-- Add last_seen_feed to users table for tracking when user last viewed feed
ALTER TABLE users ADD COLUMN last_seen_feed TIMESTAMP;

-- Note: Use convert_query() in application code for PostgreSQL compatibility
-- PostgreSQL equivalent uses: BIGSERIAL PRIMARY KEY, BOOLEAN, TIMESTAMP WITH TIME ZONE

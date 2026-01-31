-- Migration: Create notifications table (PostgreSQL version)
-- Description: Track user notifications for social interactions (likes, comments, follows)
-- Author: RivaFlow Team
-- Date: 2026-02-01

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    actor_id BIGINT NOT NULL,
    notification_type TEXT NOT NULL CHECK(notification_type IN ('like', 'comment', 'follow', 'reply', 'mention')),
    activity_type TEXT CHECK(activity_type IN ('session', 'readiness', 'rest') OR activity_type IS NULL),
    activity_id BIGINT,
    comment_id BIGINT,
    message TEXT,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    read_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, is_read, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_actor ON notifications(actor_id);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at DESC);

-- Composite index for efficient querying of unread notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread_created ON notifications(user_id, is_read, created_at DESC);

-- Add last_seen_feed to users table for tracking when user last viewed feed
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen_feed TIMESTAMP WITH TIME ZONE;

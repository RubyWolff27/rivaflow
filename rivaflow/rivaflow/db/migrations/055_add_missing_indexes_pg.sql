-- Migration 055: Add Missing Performance Indexes (PostgreSQL)
-- Created: 2026-02-04
-- Description: Add indexes identified in production readiness review

-- Index on techniques.name for faster technique searches
CREATE INDEX IF NOT EXISTS idx_techniques_name ON techniques(name);

-- Composite index on gradings for user-scoped queries
CREATE INDEX IF NOT EXISTS idx_gradings_user_date ON gradings(user_id, date_graded DESC);

-- Composite index on notifications for unread queries
CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read, created_at DESC);

-- Index on movement_videos.user_id if user-specific videos exist
CREATE INDEX IF NOT EXISTS idx_movement_videos_user ON movement_videos(user_id);

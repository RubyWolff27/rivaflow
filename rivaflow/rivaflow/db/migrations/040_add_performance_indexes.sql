-- ============================================================
-- MIGRATION 040: Add Performance Indexes
-- Optimize N+1 queries and add missing composite indexes
-- ============================================================

-- Sessions table: Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_sessions_user_date ON sessions(user_id, session_date DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_user_created ON sessions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_visibility ON sessions(visibility_level);

-- Activity comments: Composite index for activity lookups with user join
CREATE INDEX IF NOT EXISTS idx_activity_comments_activity_user ON activity_comments(activity_type, activity_id, user_id);

-- Activity likes: Composite index for activity lookups with user join
CREATE INDEX IF NOT EXISTS idx_activity_likes_activity_user ON activity_likes(activity_type, activity_id, user_id);

-- Readiness table: Composite index for user date range queries
CREATE INDEX IF NOT EXISTS idx_readiness_user_date ON readiness(user_id, check_date DESC);

-- Daily checkins: Composite index for user date range queries
CREATE INDEX IF NOT EXISTS idx_daily_checkins_user_date ON daily_checkins(user_id, check_date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_checkins_user_type ON daily_checkins(user_id, checkin_type);

-- Session techniques: Add user_id index (if user_id column exists)
-- CREATE INDEX IF NOT EXISTS idx_session_techniques_user ON session_techniques(user_id);

-- Session rolls: Add user_id index (if user_id column exists)
-- CREATE INDEX IF NOT EXISTS idx_session_rolls_user ON session_rolls(user_id);

-- User relationships: Composite indexes for feed queries
CREATE INDEX IF NOT EXISTS idx_user_relationships_follower_status ON user_relationships(follower_user_id, status);
CREATE INDEX IF NOT EXISTS idx_user_relationships_following_status ON user_relationships(following_user_id, status);

-- Friends table: Additional indexes for lookups
CREATE INDEX IF NOT EXISTS idx_friends_user_type ON friends(user_id, friend_type);

-- Activity photos: Optimize activity lookups
CREATE INDEX IF NOT EXISTS idx_activity_photos_activity_user ON activity_photos(activity_type, activity_id, user_id);

-- Milestones: Composite index for user queries
CREATE INDEX IF NOT EXISTS idx_milestones_user_celebrated ON milestones(user_id, celebrated);
CREATE INDEX IF NOT EXISTS idx_milestones_user_type ON milestones(user_id, milestone_type);

-- Goal progress: Composite index for user week queries
CREATE INDEX IF NOT EXISTS idx_goal_progress_user_week ON goal_progress(user_id, week_start_date DESC);

-- Streaks: Composite index for user lookups
CREATE INDEX IF NOT EXISTS idx_streaks_user_type ON streaks(user_id, streak_type);

-- Techniques: Index for last_trained queries
CREATE INDEX IF NOT EXISTS idx_techniques_last_trained ON techniques(last_trained_date DESC) WHERE last_trained_date IS NOT NULL;

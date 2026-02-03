-- Migration 050: Tier System Enhancements
-- Created: 2026-02-03
-- Purpose: Add tier expiration tracking and feature usage limits

-- Add tier expiration and beta tracking columns
-- SQLite doesn't support IF NOT EXISTS with ALTER TABLE ADD COLUMN
ALTER TABLE users ADD COLUMN tier_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN beta_joined_at TIMESTAMP;

-- Create feature usage tracking table
CREATE TABLE IF NOT EXISTS feature_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature VARCHAR(50) NOT NULL,
    count INTEGER DEFAULT 0,
    period_start DATE NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, feature, period_start)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_feature_usage_user ON feature_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_feature_usage_feature ON feature_usage(feature);
CREATE INDEX IF NOT EXISTS idx_feature_usage_period ON feature_usage(period_start);
CREATE INDEX IF NOT EXISTS idx_users_tier_expires ON users(tier_expires_at);
CREATE INDEX IF NOT EXISTS idx_users_beta ON users(beta_joined_at);

-- Comments (SQLite doesn't support -- COMMENT: - these are for documentation only)
-- TABLE feature_usage: Tracks feature usage for enforcing tier limits (e.g., max friends, max photos)
-- COLUMN users.tier_expires_at: When premium tier expires. NULL = never expires (lifetime_premium, free tier)
-- COLUMN users.beta_joined_at: When user joined beta program. Used for lifetime premium eligibility

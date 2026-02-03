-- Migration 044: Grapple Foundation (SQLite)
-- Created: 2026-02-04
-- Purpose: Add subscription tier and beta user tracking

-- Add subscription tier column (SQLite doesn't support IF NOT EXISTS with ALTER TABLE)
-- Check if column exists before adding
ALTER TABLE users ADD COLUMN subscription_tier TEXT DEFAULT 'free';

-- Add beta user column
ALTER TABLE users ADD COLUMN is_beta_user BOOLEAN DEFAULT FALSE;

-- Update existing users to beta tier (migration period)
UPDATE users
SET subscription_tier = 'beta', is_beta_user = TRUE
WHERE subscription_tier = 'free';

-- Create index on subscription tier for efficient queries
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users(subscription_tier);

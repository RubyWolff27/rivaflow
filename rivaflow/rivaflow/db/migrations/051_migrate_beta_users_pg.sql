-- Migration 051: Migrate Beta Users to Lifetime Premium (PostgreSQL)
-- Created: 2026-02-03
-- Purpose: Mark all existing users as lifetime premium beta users
-- IMPORTANT: Run this ONCE before launching paid tiers

-- Update all existing users to lifetime premium beta status
UPDATE users
SET
    subscription_tier = 'lifetime_premium',
    is_beta_user = TRUE,
    beta_joined_at = COALESCE(created_at::TIMESTAMP WITH TIME ZONE, NOW()),
    tier_expires_at = NULL  -- NULL = never expires
WHERE
    (subscription_tier IS NULL OR subscription_tier = 'free');

-- Verify migration (should output count of migrated users)
SELECT
    COUNT(*) as total_users,
    COUNT(*) FILTER (WHERE subscription_tier = 'lifetime_premium') as lifetime_premium_count,
    COUNT(*) FILTER (WHERE is_beta_user = TRUE) as beta_user_count,
    COUNT(*) FILTER (WHERE beta_joined_at IS NOT NULL) as users_with_beta_date
FROM users;

-- Add comment
COMMENT ON COLUMN users.subscription_tier IS 'User tier: free, premium, lifetime_premium, admin';

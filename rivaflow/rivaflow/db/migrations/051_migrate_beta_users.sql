-- Migration 051: Migrate Beta Users to Lifetime Premium
-- Created: 2026-02-03
-- Purpose: Mark all existing users as lifetime premium beta users
-- IMPORTANT: Run this ONCE before launching paid tiers

-- Update all existing users to lifetime premium beta status
UPDATE users
SET
    subscription_tier = 'lifetime_premium',
    is_beta_user = TRUE,
    beta_joined_at = COALESCE(created_at, CURRENT_TIMESTAMP),
    tier_expires_at = NULL
WHERE
    (subscription_tier IS NULL OR subscription_tier = 'free');

-- Verify migration (should output count of migrated users)
SELECT
    COUNT(*) as total_users,
    SUM(CASE WHEN subscription_tier = 'lifetime_premium' THEN 1 ELSE 0 END) as lifetime_premium_count,
    SUM(CASE WHEN is_beta_user THEN 1 ELSE 0 END) as beta_user_count,
    SUM(CASE WHEN beta_joined_at IS NOT NULL THEN 1 ELSE 0 END) as users_with_beta_date
FROM users;

-- Add comment
-- COMMENT: users.subscription_tier - User tier: free, premium, lifetime_premium, admin

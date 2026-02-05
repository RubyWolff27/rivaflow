-- Migration 058: Set platform owner as admin
-- Sets rubywolff@gmail.com as admin, premium, and beta user
-- This migration is idempotent - safe to run multiple times

UPDATE users
SET is_admin = true,
    subscription_tier = 'premium',
    is_beta_user = true,
    updated_at = CURRENT_TIMESTAMP
WHERE email = 'rubywolff@gmail.com'
  AND is_admin = false;  -- Only update if not already admin

-- Insert a record if the user doesn't exist yet (will fail gracefully if they do)
-- This is commented out - user must register first via the app
-- INSERT INTO users (email, is_admin, subscription_tier, is_beta_user)
-- VALUES ('rubywolff@gmail.com', true, 'premium', true)
-- ON CONFLICT (email) DO NOTHING;

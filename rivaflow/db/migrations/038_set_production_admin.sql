-- Migration 038: Set production admin user
-- Created: 2026-01-31
-- Purpose: Automatically grant admin to production user account

-- Grant admin to the production user
-- This is a one-time migration to set up the initial admin
UPDATE users SET is_admin = TRUE WHERE email = 'rubywolff@gmail.com';

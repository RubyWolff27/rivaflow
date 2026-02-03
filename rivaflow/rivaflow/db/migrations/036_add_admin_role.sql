-- Migration 036: Add admin role to users table
-- Created: 2026-01-31
-- Purpose: Add is_admin column for proper role-based access control

-- Add is_admin column to users table
-- Use FALSE instead of 0 for PostgreSQL compatibility
ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;

-- Make user_id 1 an admin by default (first user)
-- Use TRUE instead of 1 for PostgreSQL compatibility
UPDATE users SET is_admin = TRUE WHERE id = 1;

-- Create index for faster admin checks
CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);

-- Migration 036: Add admin role to users table
-- Created: 2026-01-31
-- Purpose: Add is_admin column for proper role-based access control

-- Add is_admin column to users table
ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0;

-- Make user_id 1 an admin by default (first user)
UPDATE users SET is_admin = 1 WHERE id = 1;

-- Create index for faster admin checks
CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);

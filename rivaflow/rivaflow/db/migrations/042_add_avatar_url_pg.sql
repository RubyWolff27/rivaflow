-- Migration: Add avatar URL to users table (PostgreSQL version)
-- Description: Store profile photo URLs for users
-- Author: RivaFlow Team
-- Date: 2026-02-01

-- Add avatar_url column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT;

-- Note: Avatar URLs will be stored as file paths or external URLs
-- Format: /uploads/avatars/user_{user_id}_{timestamp}.jpg
-- Or external: https://...

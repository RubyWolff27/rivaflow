-- Add timezone column to profile table (PostgreSQL version)
-- Stores IANA timezone name (e.g. 'Australia/Sydney', 'America/New_York')
-- Defaults to UTC for existing users
ALTER TABLE profile ADD COLUMN IF NOT EXISTS timezone TEXT DEFAULT 'UTC';

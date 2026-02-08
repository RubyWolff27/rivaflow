-- Add timezone column to profile table
-- Stores IANA timezone name (e.g. 'Australia/Sydney', 'America/New_York')
-- Defaults to UTC for existing users
ALTER TABLE profile ADD COLUMN timezone TEXT DEFAULT 'UTC';

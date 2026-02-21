-- Add last_login timestamp to users table for admin visibility
ALTER TABLE users ADD COLUMN last_login TIMESTAMP;

-- Migration 086: Ensure profile.timezone column exists (PostgreSQL, idempotent)
-- Fixes issue where migration 074 was recorded but column never created on PG
ALTER TABLE profile ADD COLUMN IF NOT EXISTS timezone TEXT DEFAULT 'UTC';

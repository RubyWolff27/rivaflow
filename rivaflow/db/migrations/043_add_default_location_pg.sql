-- Migration 043: Add default_location to profile table (PostgreSQL)
-- Created: 2026-02-01
-- Purpose: Store user's default location for auto-populating session forms

-- Add default_location column to profile table
ALTER TABLE profile ADD COLUMN IF NOT EXISTS default_location TEXT;

-- Note: Users can set this in their profile settings (e.g., "Sydney, NSW")
-- It will auto-populate in the Log Session form like default_gym does

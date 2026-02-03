-- Migration 045: Add Google Maps URL and head coach belt to gyms (PostgreSQL)
-- Created: 2026-02-01

ALTER TABLE gyms ADD COLUMN IF NOT EXISTS google_maps_url TEXT;
ALTER TABLE gyms ADD COLUMN IF NOT EXISTS head_coach_belt TEXT;

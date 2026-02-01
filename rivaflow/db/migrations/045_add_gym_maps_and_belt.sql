-- Migration 045: Add Google Maps URL and head coach belt to gyms
-- Created: 2026-02-01

ALTER TABLE gyms ADD COLUMN google_maps_url TEXT;
ALTER TABLE gyms ADD COLUMN head_coach_belt TEXT;

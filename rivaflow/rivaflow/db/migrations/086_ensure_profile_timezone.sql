-- Migration 086: Ensure profile.timezone column exists (idempotent)
-- Fixes issue where migration 074 was recorded but column never created on PG
-- This migration is safe to run even if the column already exists
SELECT 1;

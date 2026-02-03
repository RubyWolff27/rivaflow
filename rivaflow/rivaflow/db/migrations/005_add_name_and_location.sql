-- Migration 005: Add name and location fields to profile

ALTER TABLE profile ADD COLUMN first_name TEXT;
ALTER TABLE profile ADD COLUMN last_name TEXT;
ALTER TABLE profile ADD COLUMN city TEXT;
ALTER TABLE profile ADD COLUMN suburb TEXT;

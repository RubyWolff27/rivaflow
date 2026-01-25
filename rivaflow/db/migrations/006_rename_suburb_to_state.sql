-- Migration 006: Rename suburb column to state in profile

ALTER TABLE profile RENAME COLUMN suburb TO state;

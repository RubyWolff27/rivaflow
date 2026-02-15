-- Fix needs_review column type v2
-- Previous migration 089 used DO $$ block which was broken by semicolon splitting
-- Simple ALTER statements that work when split on semicolons
ALTER TABLE sessions ALTER COLUMN needs_review TYPE BOOLEAN USING needs_review::boolean;
ALTER TABLE sessions ALTER COLUMN needs_review SET DEFAULT FALSE

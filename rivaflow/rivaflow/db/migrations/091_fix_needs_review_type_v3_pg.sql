-- Fix needs_review column type v3
-- Previous attempts used ::boolean cast which may fail on some PG configs
-- Use explicit CASE expression which always works
ALTER TABLE sessions ALTER COLUMN needs_review TYPE BOOLEAN USING CASE WHEN needs_review = 0 THEN FALSE WHEN needs_review IS NULL THEN NULL ELSE TRUE END

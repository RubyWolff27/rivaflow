-- Fix needs_review column type: should be BOOLEAN not INTEGER
-- Original migration 077 applied SQLite version before _pg.sql variant existed
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'sessions' AND column_name = 'needs_review'
    AND data_type != 'boolean'
  ) THEN
    ALTER TABLE sessions ALTER COLUMN needs_review TYPE BOOLEAN USING needs_review::boolean;
    ALTER TABLE sessions ALTER COLUMN needs_review SET DEFAULT FALSE;
  END IF;
END $$;

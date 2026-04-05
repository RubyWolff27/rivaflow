-- ============================================================
-- MIGRATION 034: Fix movements_glossary custom movements (PostgreSQL)
-- ============================================================
-- SQLite version uses table-recreation (CREATE _new → INSERT SELECT → DROP → RENAME)
-- because SQLite can't DROP CONSTRAINT. Postgres can, so we use native
-- ALTER TABLE ADD COLUMN which is much simpler and more reliable.
--
-- 2026-04-05 Sage: replaced auto-translated table-recreation (which was
-- failing silently under SAVEPOINT isolation, leaving user_id absent) with
-- this native ALTER TABLE approach. Root cause of admin_list_techniques
-- 500 errors: column "user_id" does not exist.
-- ============================================================

-- Add user_id column for custom movements (NULL for seeded movements)
ALTER TABLE movements_glossary
    ADD COLUMN IF NOT EXISTS user_id BIGINT REFERENCES users(id) ON DELETE CASCADE;

-- Drop the old name-only uniqueness (migration 007 created UNIQUE on name).
-- Try both common auto-generated constraint names — Postgres uses
-- <table>_<column>_key by default.
ALTER TABLE movements_glossary DROP CONSTRAINT IF EXISTS movements_glossary_name_key;
DROP INDEX IF EXISTS idx_movements_glossary_name_unique;

-- New uniqueness: (name, custom, user_id). COALESCE(user_id, 0) ensures NULLs
-- don't create infinite "unique" rows. Seeded movements (user_id=NULL→0) stay
-- globally unique by name; custom movements (user_id=N) unique per user.
CREATE UNIQUE INDEX IF NOT EXISTS idx_movements_glossary_name_custom_user
    ON movements_glossary (name, custom, COALESCE(user_id, 0));

-- Index for user-scoped lookups
CREATE INDEX IF NOT EXISTS idx_movements_glossary_user_id ON movements_glossary(user_id);

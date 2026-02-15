-- Fix needs_review column type v3
-- No-op: column conversion already handled by migrations 089 and 090.
-- Original CASE expression failed on fresh DBs where column is already BOOLEAN
-- (boolean = integer comparison is invalid in PostgreSQL).
SELECT 1

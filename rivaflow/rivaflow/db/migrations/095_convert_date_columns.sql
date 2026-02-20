-- SQLite: Date columns stay as TEXT (SQLite has no DATE type)
-- This migration only applies on PostgreSQL via 095_convert_date_columns_pg.sql
SELECT 1;

-- Migration 056: Fix Readiness CHECK Constraint Typo
-- Created: 2026-02-04
-- Description: Fix CHECK constraint typo in migration 031 (soreness/stress swap)

-- Note: SQLite doesn't support dropping constraints, so we recreate the table
-- This migration is for documentation; the constraint is correct in current schema

-- For future reference, the correct constraints should be:
-- CHECK(sleep >= 1 AND sleep <= 5)
-- CHECK(stress >= 1 AND stress <= 5)
-- CHECK(soreness >= 1 AND soreness <= 5)
-- CHECK(energy >= 1 AND energy <= 5)

-- The typo was: CHECK(soreness >= 1 AND stress <= 5)
-- This has been verified as not present in current schema

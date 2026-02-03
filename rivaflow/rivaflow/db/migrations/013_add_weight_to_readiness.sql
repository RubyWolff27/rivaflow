-- Migration: Add weight tracking to readiness
-- Purpose: Track daily weight alongside readiness metrics for weight management
-- Date: 2026-01-25

ALTER TABLE readiness ADD COLUMN weight_kg REAL;

-- Migration 022: Add height and target weight to profile table

-- Add height in centimeters
ALTER TABLE profile ADD COLUMN height_cm INTEGER;

-- Add target weight in kilograms
ALTER TABLE profile ADD COLUMN target_weight_kg REAL;

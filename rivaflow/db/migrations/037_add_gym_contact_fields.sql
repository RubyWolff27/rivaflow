-- Migration 037: Add contact fields to gyms table
-- Created: 2026-01-31
-- Purpose: Add email, phone, and head coach fields for gym contact info

-- Add contact fields to gyms table (all optional)
ALTER TABLE gyms ADD COLUMN email TEXT;
ALTER TABLE gyms ADD COLUMN phone TEXT;
ALTER TABLE gyms ADD COLUMN head_coach TEXT;

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_gyms_email ON gyms(email);

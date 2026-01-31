-- Migration 035: Create gyms table for standardized gym management
-- Created: 2026-01-31
-- Purpose: Centralized gym database to improve data quality and friend recommendations

-- Create gyms table
CREATE TABLE IF NOT EXISTS gyms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT,
    country TEXT DEFAULT 'USA',
    website TEXT,
    verified BOOLEAN DEFAULT 0,  -- 0 = user-added, 1 = admin-verified
    added_by_user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (added_by_user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create index on name for faster searching
CREATE INDEX IF NOT EXISTS idx_gyms_name ON gyms(name);

-- Create index on city/state for location-based queries
CREATE INDEX IF NOT EXISTS idx_gyms_location ON gyms(city, state);

-- Create index on verified status for filtering
CREATE INDEX IF NOT EXISTS idx_gyms_verified ON gyms(verified);

-- Add primary_gym_id to users table
ALTER TABLE users ADD COLUMN primary_gym_id INTEGER REFERENCES gyms(id) ON DELETE SET NULL;

-- Create index on users.primary_gym_id for faster friend recommendations
CREATE INDEX IF NOT EXISTS idx_users_primary_gym ON users(primary_gym_id);

-- Seed some initial gyms (major BJJ academies in USA)
-- Use TRUE instead of 1 for PostgreSQL compatibility
INSERT INTO gyms (name, city, state, verified, added_by_user_id) VALUES
    ('Gracie Barra', 'Irvine', 'CA', TRUE, NULL),
    ('Alliance BJJ', 'San Diego', 'CA', TRUE, NULL),
    ('Atos Jiu-Jitsu', 'San Diego', 'CA', TRUE, NULL),
    ('10th Planet Jiu Jitsu', 'Los Angeles', 'CA', TRUE, NULL),
    ('Marcelo Garcia Academy', 'New York', 'NY', TRUE, NULL),
    ('Renzo Gracie Academy', 'New York', 'NY', TRUE, NULL),
    ('Team Lloyd Irvin', 'Camp Springs', 'MD', TRUE, NULL),
    ('Gracie Humaita', 'Rio de Janeiro', 'Brazil', TRUE, NULL),
    ('Roger Gracie Academy', 'London', 'UK', TRUE, NULL),
    ('Checkmat', 'Long Beach', 'CA', TRUE, NULL);

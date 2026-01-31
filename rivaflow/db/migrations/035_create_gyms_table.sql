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
INSERT INTO gyms (name, city, state, verified, added_by_user_id) VALUES
    ('Gracie Barra', 'Irvine', 'CA', 1, NULL),
    ('Alliance BJJ', 'San Diego', 'CA', 1, NULL),
    ('Atos Jiu-Jitsu', 'San Diego', 'CA', 1, NULL),
    ('10th Planet Jiu Jitsu', 'Los Angeles', 'CA', 1, NULL),
    ('Marcelo Garcia Academy', 'New York', 'NY', 1, NULL),
    ('Renzo Gracie Academy', 'New York', 'NY', 1, NULL),
    ('Team Lloyd Irvin', 'Camp Springs', 'MD', 1, NULL),
    ('Gracie Humaita', 'Rio de Janeiro', 'Brazil', 1, NULL),
    ('Roger Gracie Academy', 'London', 'UK', 1, NULL),
    ('Checkmat', 'Long Beach', 'CA', 1, NULL);

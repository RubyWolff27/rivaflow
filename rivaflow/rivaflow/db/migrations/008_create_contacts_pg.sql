-- PostgreSQL version (auto-generated from sibling .sql file)
-- Translations applied: AUTOINCREMENT→BIGSERIAL, *_id INTEGER→BIGINT,
-- datetime('now')→CURRENT_TIMESTAMP, BOOLEAN 0/1→FALSE/TRUE,
-- PRAGMA/BEGIN/COMMIT removed, CREATE INDEX→IF NOT EXISTS.
-- Regenerate: bun /tmp/translate_sqlite_to_pg.py (see note in header)

-- Contacts table for training partners and instructors
CREATE TABLE IF NOT EXISTS contacts (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    contact_type TEXT NOT NULL DEFAULT 'training-partner' CHECK(contact_type IN ('instructor', 'training-partner', 'both')),

    -- Belt rank for students/training partners
    belt_rank TEXT CHECK(belt_rank IN ('white', 'blue', 'purple', 'brown', 'black', NULL)),
    belt_stripes INTEGER DEFAULT 0 CHECK(belt_stripes BETWEEN 0 AND 4),

    -- Instructor certification (e.g., "1st degree black belt", "Certified Instructor")
    instructor_certification TEXT,

    -- Contact information (optional)
    phone TEXT,
    email TEXT,
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(name);
CREATE INDEX IF NOT EXISTS idx_contacts_type ON contacts(contact_type);
CREATE INDEX IF NOT EXISTS idx_contacts_belt ON contacts(belt_rank);

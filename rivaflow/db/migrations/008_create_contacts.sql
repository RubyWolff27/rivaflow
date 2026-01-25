-- Contacts table for training partners and instructors
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(name);
CREATE INDEX IF NOT EXISTS idx_contacts_type ON contacts(contact_type);
CREATE INDEX IF NOT EXISTS idx_contacts_belt ON contacts(belt_rank);

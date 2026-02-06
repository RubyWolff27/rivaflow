CREATE TABLE IF NOT EXISTS waitlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    first_name TEXT,
    gym_name TEXT,
    belt_rank TEXT,
    referral_source TEXT,
    position INTEGER,
    status TEXT NOT NULL DEFAULT 'waiting',
    invited_at TEXT,
    registered_at TEXT,
    assigned_tier TEXT DEFAULT 'free',
    invite_token TEXT UNIQUE,
    invite_token_expires_at TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_waitlist_email ON waitlist(email);
CREATE INDEX IF NOT EXISTS idx_waitlist_status ON waitlist(status);
CREATE INDEX IF NOT EXISTS idx_waitlist_position ON waitlist(position);
CREATE INDEX IF NOT EXISTS idx_waitlist_invite_token ON waitlist(invite_token);

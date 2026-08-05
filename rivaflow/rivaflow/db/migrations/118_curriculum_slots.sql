-- 118_curriculum_slots.sql
-- Belt-curriculum tracker: declared sequence slots, derived evidence, immutable
-- coach sign-offs, and the hard-gate meta row (SQLite / local dev).
-- See 118_curriculum_slots_pg.sql for the PostgreSQL (production) variant.
--
-- Integrity core: a slot's status is NEVER stored. It is derived on read from
-- curriculum_slot_evidence (rungs 0-3) and curriculum_slot_signoff (rung 4).
-- There is deliberately no status column for an API path to write to.

CREATE TABLE IF NOT EXISTS curriculum_slot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    belt TEXT NOT NULL DEFAULT 'purple',
    block TEXT NOT NULL,
    requirement_key TEXT NOT NULL,
    requirement_label TEXT,
    slot_index INTEGER NOT NULL,
    of_choice INTEGER NOT NULL DEFAULT 1,
    seq_entry TEXT,
    seq_position TEXT,
    seq_finish TEXT,
    game_tag TEXT,
    movement_ids TEXT,
    is_draft INTEGER NOT NULL DEFAULT 0,
    tension_note TEXT,
    blocker_note TEXT,
    declared_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, belt, requirement_key, slot_index)
);

CREATE INDEX IF NOT EXISTS curriculum_slot_user_block_idx
    ON curriculum_slot (user_id, belt, block);

CREATE TABLE IF NOT EXISTS curriculum_slot_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id INTEGER NOT NULL REFERENCES curriculum_slot(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    kind TEXT NOT NULL,
    partner_ref TEXT,
    partner_rank_band TEXT,
    partner_size TEXT,
    note TEXT,
    logged_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS curriculum_evidence_slot_idx
    ON curriculum_slot_evidence (slot_id, logged_at);
CREATE INDEX IF NOT EXISTS curriculum_evidence_user_idx
    ON curriculum_slot_evidence (user_id, logged_at);

-- Immutable by convention: created only, never updated or deleted via the API.
CREATE TABLE IF NOT EXISTS curriculum_slot_signoff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id INTEGER NOT NULL REFERENCES curriculum_slot(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    verdict TEXT NOT NULL,
    coach_name TEXT NOT NULL,
    coach_rank TEXT,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS curriculum_signoff_slot_idx
    ON curriculum_slot_signoff (slot_id, created_at);

-- Hard gates live here, one row per user per belt. classes_logged is labelled in
-- the UI as "my log, not the Academy's record" and is never authoritative.
-- NOTE: keep every comment in this file free of statement terminators. The
-- migration runner splits the file on the terminator character BEFORE it strips
-- comment lines, so one inside a comment silently severs the next statement.
CREATE TABLE IF NOT EXISTS curriculum_meta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    belt TEXT NOT NULL DEFAULT 'purple',
    competition_date TEXT,
    competition_note TEXT,
    classes_logged INTEGER,
    stripes INTEGER,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, belt)
);

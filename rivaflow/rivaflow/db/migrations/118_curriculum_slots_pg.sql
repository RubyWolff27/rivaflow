-- 118_curriculum_slots_pg.sql
-- Belt-curriculum tracker: declared sequence slots, derived evidence, immutable
-- coach sign-offs, and the hard-gate meta row (PostgreSQL).
--
-- The atom is a declared SEQUENCE (entry/grip -> position/action -> terminal
-- finish), not a technique, because the AJJ syllabus itself is written that way
-- ("10 sweeps -> submission"). ~88 of the ~90 purple slots are "of choice", so
-- the slate doubles as the game-system tracker via game_tag.
--
-- Integrity core: a slot's status is NEVER stored. It is derived on read from
-- curriculum_slot_evidence (rungs 0-3) and curriculum_slot_signoff (rung 4).
-- There is deliberately no status column for an API path to write to.

CREATE TABLE IF NOT EXISTS curriculum_slot (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    belt TEXT NOT NULL DEFAULT 'purple',
    block TEXT NOT NULL,
    requirement_key TEXT NOT NULL,
    requirement_label TEXT,
    slot_index INTEGER NOT NULL,
    of_choice BOOLEAN NOT NULL DEFAULT TRUE,
    seq_entry TEXT,
    seq_position TEXT,
    seq_finish TEXT,
    game_tag TEXT,
    movement_ids TEXT,
    is_draft BOOLEAN NOT NULL DEFAULT FALSE,
    tension_note TEXT,
    blocker_note TEXT,
    declared_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, belt, requirement_key, slot_index)
);

CREATE INDEX IF NOT EXISTS curriculum_slot_user_block_idx
    ON curriculum_slot (user_id, belt, block);

CREATE TABLE IF NOT EXISTS curriculum_slot_evidence (
    id SERIAL PRIMARY KEY,
    slot_id INTEGER NOT NULL REFERENCES curriculum_slot(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    kind TEXT NOT NULL,
    partner_ref TEXT,
    partner_rank_band TEXT,
    partner_size TEXT,
    note TEXT,
    logged_at DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS curriculum_evidence_slot_idx
    ON curriculum_slot_evidence (slot_id, logged_at);
CREATE INDEX IF NOT EXISTS curriculum_evidence_user_idx
    ON curriculum_slot_evidence (user_id, logged_at);

-- Immutable by convention: created only, never updated or deleted via the API.
CREATE TABLE IF NOT EXISTS curriculum_slot_signoff (
    id SERIAL PRIMARY KEY,
    slot_id INTEGER NOT NULL REFERENCES curriculum_slot(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    verdict TEXT NOT NULL,
    coach_name TEXT NOT NULL,
    coach_rank TEXT,
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS curriculum_signoff_slot_idx
    ON curriculum_slot_signoff (slot_id, created_at);

-- Hard gates live here, one row per user per belt. classes_logged is labelled in
-- the UI as "my log, not the Academy's record" and is never authoritative.
-- NOTE: keep every comment in this file free of statement terminators. The
-- migration runner splits the file on the terminator character BEFORE it strips
-- comment lines, so one inside a comment silently severs the next statement.
CREATE TABLE IF NOT EXISTS curriculum_meta (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    belt TEXT NOT NULL DEFAULT 'purple',
    competition_date DATE,
    competition_note TEXT,
    classes_logged INTEGER,
    stripes INTEGER,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, belt)
);

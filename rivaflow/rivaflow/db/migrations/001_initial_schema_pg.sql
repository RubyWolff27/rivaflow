-- PostgreSQL version (auto-generated from sibling .sql file)
-- Translations applied: AUTOINCREMENT→BIGSERIAL, *_id INTEGER→BIGINT,
-- datetime('now')→CURRENT_TIMESTAMP, BOOLEAN 0/1→FALSE/TRUE,
-- PRAGMA/BEGIN/COMMIT removed, CREATE INDEX→IF NOT EXISTS.
-- Regenerate: bun /tmp/translate_sqlite_to_pg.py (see note in header)

-- Use ISO 8601 strings for all dates (timezone-portable)
-- Integer IDs (easily migrated to UUID later)

CREATE TABLE IF NOT EXISTS sessions (
    id BIGSERIAL PRIMARY KEY,
    session_date TEXT NOT NULL,  -- ISO 8601: YYYY-MM-DD
    class_type TEXT NOT NULL,    -- gi, no-gi, wrestling, judo, s&c, mobility, yoga, rehab, physio, open-mat
    gym_name TEXT NOT NULL,
    location TEXT,               -- Human readable: suburb, city, state, country
    duration_mins INTEGER NOT NULL DEFAULT 60,
    intensity INTEGER NOT NULL DEFAULT 4 CHECK(intensity BETWEEN 1 AND 5),
    rolls INTEGER NOT NULL DEFAULT 0,
    submissions_for INTEGER NOT NULL DEFAULT 0,
    submissions_against INTEGER NOT NULL DEFAULT 0,
    partners TEXT,               -- JSON array: ["name1", "name2"]
    techniques TEXT,             -- JSON array: ["armbar", "triangle"]
    notes TEXT,
    visibility_level TEXT NOT NULL DEFAULT 'private',  -- private/attendance/summary/full
    audience_scope TEXT,         -- Future: friends/team/public
    share_fields TEXT,           -- JSON: fields to include when sharing
    published_at TEXT,           -- ISO 8601 datetime if published
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS readiness (
    id BIGSERIAL PRIMARY KEY,
    check_date TEXT NOT NULL UNIQUE,  -- ISO 8601: YYYY-MM-DD
    sleep INTEGER NOT NULL CHECK(sleep BETWEEN 1 AND 5),
    stress INTEGER NOT NULL CHECK(stress BETWEEN 1 AND 5),
    soreness INTEGER NOT NULL CHECK(soreness BETWEEN 1 AND 5),
    energy INTEGER NOT NULL CHECK(energy BETWEEN 1 AND 5),
    hotspot_note TEXT,           -- Injury/soreness location
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS techniques (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT,               -- guard, pass, submission, sweep, takedown, escape, position
    last_trained_date TEXT,      -- ISO 8601: YYYY-MM-DD
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS videos (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT,
    timestamps TEXT,             -- JSON: [{"time": "2:30", "label": "entry"}, {"time": "5:15", "label": "finish"}]
    technique_id BIGINT REFERENCES techniques(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_sessions_class_type ON sessions(class_type);
CREATE INDEX IF NOT EXISTS idx_sessions_gym ON sessions(gym_name);
CREATE INDEX IF NOT EXISTS idx_readiness_date ON readiness(check_date);
CREATE INDEX IF NOT EXISTS idx_techniques_name ON techniques(name);

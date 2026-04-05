-- PostgreSQL version (auto-generated from sibling .sql file)
-- Translations applied: AUTOINCREMENT→BIGSERIAL, *_id INTEGER→BIGINT,
-- datetime('now')→CURRENT_TIMESTAMP, BOOLEAN 0/1→FALSE/TRUE,
-- PRAGMA/BEGIN/COMMIT removed, CREATE INDEX→IF NOT EXISTS.
-- Regenerate: bun /tmp/translate_sqlite_to_pg.py (see note in header)

-- Migration 061: Events & Competition Prep tables

CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    name TEXT NOT NULL,
    event_type TEXT NOT NULL DEFAULT 'competition',
    event_date TEXT NOT NULL,
    location TEXT,
    weight_class TEXT,
    target_weight REAL,
    division TEXT,
    notes TEXT,
    status TEXT DEFAULT 'upcoming',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS weight_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    weight REAL NOT NULL,
    logged_date TEXT NOT NULL DEFAULT CURRENT_DATE,
    time_of_day TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

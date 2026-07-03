-- 109_whoop_ingest.sql
-- Subscription-free WHOOP data platform — Phase 1a ingest tables (SQLite / local dev).
-- See 109_whoop_ingest_pg.sql for the PostgreSQL (production) variant + design notes.
-- RAW-FIRST: whoop_raw_frames is the immutable source of truth; decoded tables are rebuildable.
-- All tables user-scoped; ingest idempotent (dedup on frame hash / ts).

CREATE TABLE IF NOT EXISTS whoop_raw_frames (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ts            TEXT    NOT NULL,              -- ISO-8601
    frame_sha256  TEXT    NOT NULL,              -- hex sha256, dedup key
    session_id    TEXT,
    char_uuid     TEXT    NOT NULL,
    packet_type   INTEGER,
    seq           INTEGER,
    frame_hex     TEXT    NOT NULL,
    decoded       INTEGER NOT NULL DEFAULT 0,
    ingested_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, ts, frame_sha256)
);
CREATE INDEX IF NOT EXISTS idx_whoop_raw_user_ts ON whoop_raw_frames (user_id, ts);

CREATE TABLE IF NOT EXISTS whoop_hr (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ts TEXT NOT NULL, bpm INTEGER NOT NULL, session_id TEXT,
    PRIMARY KEY (user_id, ts)
);
CREATE TABLE IF NOT EXISTS whoop_rr (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ts TEXT NOT NULL, rr_ms INTEGER NOT NULL, session_id TEXT,
    PRIMARY KEY (user_id, ts, rr_ms)
);
CREATE TABLE IF NOT EXISTS whoop_hrv (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ts TEXT NOT NULL, rmssd REAL, rr_count INTEGER, window_s INTEGER, at_rest INTEGER,
    PRIMARY KEY (user_id, ts)
);
CREATE TABLE IF NOT EXISTS whoop_battery (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ts TEXT NOT NULL, soc INTEGER, charging INTEGER,
    PRIMARY KEY (user_id, ts)
);

CREATE TABLE IF NOT EXISTS whoop_ingest_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ingested_at TEXT NOT NULL DEFAULT (datetime('now')),
    device TEXT, kind TEXT,
    raw_frames INTEGER, hr INTEGER, rr INTEGER, hrv INTEGER, battery INTEGER,
    deduped INTEGER, span_start TEXT, span_end TEXT
);
CREATE INDEX IF NOT EXISTS idx_whoop_ingest_log_user ON whoop_ingest_log (user_id, ingested_at DESC);

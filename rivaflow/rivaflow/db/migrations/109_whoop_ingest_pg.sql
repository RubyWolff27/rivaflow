-- 109_whoop_ingest_pg.sql
-- Subscription-free WHOOP data platform — Phase 1a ingest tables (PostgreSQL / production).
-- See 109_whoop_ingest.sql for the SQLite (local dev) variant.
--
-- RAW-FIRST: whoop_raw_frames is the immutable, append-only source of truth (every strap frame,
-- even undecoded). Decoded stream tables are derived and rebuildable from it. All tables are
-- user-scoped and the ingest is idempotent (dedup on frame hash / ts).
--
-- Tables are prefixed whoop_* in the public schema (matches garmin_daily + the existing whoop_*
-- session columns, and preserves SQLite/PG dialect parity) rather than a PG-only CREATE SCHEMA.
-- Prod hardening TODO (issue): daily-partition + compress whoop_raw_frames, archive cold to R2.

-- Immutable raw frame log — source of truth
CREATE TABLE IF NOT EXISTS whoop_raw_frames (
    id            BIGSERIAL PRIMARY KEY,
    user_id       INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ts            TIMESTAMPTZ NOT NULL,
    frame_sha256  TEXT        NOT NULL,          -- hex sha256, dedup key
    session_id    TEXT,
    char_uuid     TEXT        NOT NULL,          -- e.g. 'fd4b0004' / '2a37'
    packet_type   INTEGER,                       -- decoded type if known, else NULL
    seq           INTEGER,
    frame_hex     TEXT        NOT NULL,
    decoded       BOOLEAN     NOT NULL DEFAULT FALSE,
    ingested_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, ts, frame_sha256)
);
CREATE INDEX IF NOT EXISTS idx_whoop_raw_user_ts ON whoop_raw_frames (user_id, ts);

-- Decoded streams (rebuildable from raw_frames)
CREATE TABLE IF NOT EXISTS whoop_hr (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ts TIMESTAMPTZ NOT NULL, bpm SMALLINT NOT NULL, session_id TEXT,
    PRIMARY KEY (user_id, ts)
);
CREATE TABLE IF NOT EXISTS whoop_rr (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ts TIMESTAMPTZ NOT NULL, rr_ms INTEGER NOT NULL, session_id TEXT,
    PRIMARY KEY (user_id, ts, rr_ms)             -- multiple RR can share a ts
);
CREATE TABLE IF NOT EXISTS whoop_hrv (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ts TIMESTAMPTZ NOT NULL, rmssd REAL, rr_count SMALLINT, window_s INTEGER,
    at_rest BOOLEAN,                             -- HRV only trustworthy at rest (motion-artifact guard)
    PRIMARY KEY (user_id, ts)
);
CREATE TABLE IF NOT EXISTS whoop_battery (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ts TIMESTAMPTZ NOT NULL, soc SMALLINT, charging BOOLEAN,
    PRIMARY KEY (user_id, ts)
);

-- Capture-health heartbeat — drives gap detection (single biometric source now)
CREATE TABLE IF NOT EXISTS whoop_ingest_log (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    device TEXT, kind TEXT,                      -- 'realtime' | 'historical_drain'
    raw_frames INTEGER, hr INTEGER, rr INTEGER, hrv INTEGER, battery INTEGER,
    deduped INTEGER, span_start TIMESTAMPTZ, span_end TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_whoop_ingest_log_user ON whoop_ingest_log (user_id, ingested_at DESC);

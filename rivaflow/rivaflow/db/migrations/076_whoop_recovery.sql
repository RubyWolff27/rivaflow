-- WHOOP Recovery & Sleep data (SQLite)

-- Add WHOOP recovery fields to readiness table
ALTER TABLE readiness ADD COLUMN hrv_ms REAL;
ALTER TABLE readiness ADD COLUMN resting_hr INTEGER;
ALTER TABLE readiness ADD COLUMN spo2 REAL;
ALTER TABLE readiness ADD COLUMN whoop_recovery_score REAL;
ALTER TABLE readiness ADD COLUMN whoop_sleep_score REAL;
ALTER TABLE readiness ADD COLUMN data_source TEXT DEFAULT 'manual';

-- Cached WHOOP recovery/sleep cycle data
CREATE TABLE IF NOT EXISTS whoop_recovery_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    whoop_cycle_id TEXT NOT NULL,
    recovery_score REAL,
    resting_hr REAL,
    hrv_ms REAL,
    spo2 REAL,
    skin_temp REAL,
    sleep_performance REAL,
    sleep_duration_ms INTEGER,
    sleep_need_ms INTEGER,
    sleep_debt_ms INTEGER,
    light_sleep_ms INTEGER,
    slow_wave_ms INTEGER,
    rem_sleep_ms INTEGER,
    awake_ms INTEGER,
    cycle_start TEXT NOT NULL,
    cycle_end TEXT,
    raw_data TEXT,
    synced_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, whoop_cycle_id)
);

CREATE INDEX IF NOT EXISTS idx_whoop_recovery_user_cycle
    ON whoop_recovery_cache(user_id, cycle_start);

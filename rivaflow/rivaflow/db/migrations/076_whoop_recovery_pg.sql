-- WHOOP Recovery & Sleep data (PostgreSQL)

-- Add WHOOP recovery fields to readiness table
ALTER TABLE readiness ADD COLUMN IF NOT EXISTS hrv_ms REAL;
ALTER TABLE readiness ADD COLUMN IF NOT EXISTS resting_hr INTEGER;
ALTER TABLE readiness ADD COLUMN IF NOT EXISTS spo2 REAL;
ALTER TABLE readiness ADD COLUMN IF NOT EXISTS whoop_recovery_score REAL;
ALTER TABLE readiness ADD COLUMN IF NOT EXISTS whoop_sleep_score REAL;
ALTER TABLE readiness ADD COLUMN IF NOT EXISTS data_source VARCHAR(20) DEFAULT 'manual';

-- Cached WHOOP recovery/sleep cycle data
CREATE TABLE IF NOT EXISTS whoop_recovery_cache (
    id SERIAL PRIMARY KEY,
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
    cycle_start TIMESTAMP NOT NULL,
    cycle_end TIMESTAMP,
    raw_data JSONB,
    synced_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, whoop_cycle_id)
);

CREATE INDEX IF NOT EXISTS idx_whoop_recovery_user_cycle
    ON whoop_recovery_cache(user_id, cycle_start);

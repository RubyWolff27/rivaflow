-- 108_garmin_metrics.sql
-- Garmin per-session biometrics + daily key metrics (SQLite / local dev).
-- See 108_garmin_metrics_pg.sql for the PostgreSQL (production) variant.

ALTER TABLE sessions ADD COLUMN garmin_activity_type TEXT;
ALTER TABLE sessions ADD COLUMN garmin_activity_name TEXT;
ALTER TABLE sessions ADD COLUMN garmin_avg_hr INTEGER;
ALTER TABLE sessions ADD COLUMN garmin_max_hr INTEGER;
ALTER TABLE sessions ADD COLUMN garmin_calories INTEGER;
ALTER TABLE sessions ADD COLUMN garmin_duration_min REAL;
ALTER TABLE sessions ADD COLUMN garmin_aerobic_te REAL;
ALTER TABLE sessions ADD COLUMN garmin_anaerobic_te REAL;
ALTER TABLE sessions ADD COLUMN garmin_te_label TEXT;
ALTER TABLE sessions ADD COLUMN garmin_training_load REAL;
ALTER TABLE sessions ADD COLUMN garmin_hr_z1_sec REAL;
ALTER TABLE sessions ADD COLUMN garmin_hr_z2_sec REAL;
ALTER TABLE sessions ADD COLUMN garmin_hr_z3_sec REAL;
ALTER TABLE sessions ADD COLUMN garmin_hr_z4_sec REAL;
ALTER TABLE sessions ADD COLUMN garmin_hr_z5_sec REAL;

CREATE TABLE IF NOT EXISTS garmin_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    metric_date TEXT NOT NULL,
    rhr REAL,
    hrv_ms REAL,
    hrv_status TEXT,
    body_battery_high INTEGER,
    body_battery_low INTEGER,
    stress_avg INTEGER,
    max_stress INTEGER,
    sleep_hours REAL,
    sleep_score REAL,
    sleep_deep_hours REAL,
    sleep_rem_hours REAL,
    sleep_light_hours REAL,
    sleep_awake_hours REAL,
    steps INTEGER,
    respiration_rate REAL,
    spo2_pct REAL,
    training_readiness_score INTEGER,
    training_readiness_level TEXT,
    training_status TEXT,
    vo2max REAL,
    active_calories REAL,
    intensity_min_moderate INTEGER,
    intensity_min_vigorous INTEGER,
    synced_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, metric_date)
);

CREATE INDEX IF NOT EXISTS garmin_daily_user_date_idx ON garmin_daily (user_id, metric_date);

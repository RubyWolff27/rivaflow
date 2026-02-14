-- Migration 088: Gym class timetable (PostgreSQL)
CREATE TABLE IF NOT EXISTS gym_classes (
    id SERIAL PRIMARY KEY,
    gym_id INTEGER NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
    day_of_week INTEGER NOT NULL,  -- 0=Monday, 6=Sunday
    start_time TEXT NOT NULL,       -- "10:00" (24h format)
    end_time TEXT NOT NULL,         -- "11:00"
    class_name TEXT NOT NULL,       -- "Beginner/Intermediate Gi"
    class_type TEXT,                -- "gi", "no-gi", "open-mat", "kids", "competition"
    level TEXT,                     -- "beginner", "intermediate", "advanced", "all", "kids"
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_gym_classes_gym_day ON gym_classes(gym_id, day_of_week);

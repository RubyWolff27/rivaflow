-- WHOOP Integration tables (SQLite)

-- OAuth token storage (one per user)
CREATE TABLE IF NOT EXISTS whoop_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    whoop_user_id TEXT,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    token_expires_at TEXT NOT NULL,
    scopes TEXT,
    connected_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_synced_at TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Cached WHOOP workout data
CREATE TABLE IF NOT EXISTS whoop_workout_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    whoop_workout_id TEXT NOT NULL,
    sport_id INTEGER,
    sport_name TEXT,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    timezone_offset TEXT,
    strain REAL,
    avg_heart_rate INTEGER,
    max_heart_rate INTEGER,
    kilojoules REAL,
    calories INTEGER,
    score_state TEXT,
    zone_durations TEXT,
    raw_data TEXT,
    session_id INTEGER,
    synced_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, whoop_workout_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_whoop_workout_cache_user_time
    ON whoop_workout_cache(user_id, start_time, end_time);

-- Short-lived CSRF tokens for OAuth flow
CREATE TABLE IF NOT EXISTS whoop_oauth_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_token TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_whoop_oauth_states_token
    ON whoop_oauth_states(state_token);

-- WHOOP Integration tables (PostgreSQL)

-- OAuth token storage (one per user)
CREATE TABLE IF NOT EXISTS whoop_connections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    whoop_user_id TEXT,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    token_expires_at TIMESTAMP NOT NULL,
    scopes TEXT,
    connected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Cached WHOOP workout data
CREATE TABLE IF NOT EXISTS whoop_workout_cache (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    whoop_workout_id TEXT NOT NULL,
    sport_id INTEGER,
    sport_name TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    timezone_offset TEXT,
    strain REAL,
    avg_heart_rate INTEGER,
    max_heart_rate INTEGER,
    kilojoules REAL,
    calories INTEGER,
    score_state TEXT,
    zone_durations JSONB,
    raw_data JSONB,
    session_id INTEGER,
    synced_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, whoop_workout_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_whoop_workout_cache_user_time
    ON whoop_workout_cache(user_id, start_time, end_time);

-- Short-lived CSRF tokens for OAuth flow
CREATE TABLE IF NOT EXISTS whoop_oauth_states (
    id SERIAL PRIMARY KEY,
    state_token TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_whoop_oauth_states_token
    ON whoop_oauth_states(state_token);

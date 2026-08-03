-- 118_strava_integration_pg.sql
-- Strava OAuth integration tables (PostgreSQL / production).
-- See 118_strava_integration.sql for the SQLite (local dev) variant.
--
-- Replaces the biometric capture path lost when the Garmin push job died: Wahoo (and any other
-- device that auto-uploads to Strava) becomes the workout source, and RivaFlow pulls from
-- Strava's API rather than from a machine on the user's desk.
--
-- Shape deliberately mirrors the retired whoop_* OAuth tables (075) so the connect/sync/match
-- flow stays recognisable: one connection row per user, an idempotent activity cache keyed on
-- the provider's activity id, and short-lived CSRF states for the redirect dance.
-- (Keep these comments free of the semicolon character, which the migration runner splits on.)

-- OAuth token storage (one per user)
CREATE TABLE IF NOT EXISTS strava_connections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    athlete_id TEXT,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    token_expires_at TIMESTAMP NOT NULL,
    scopes TEXT,
    connected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP,
    auto_create_sessions BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Cached Strava activity data
-- dismissed lets the user hide a non-training activity from the import list without
-- deleting the cache row, so the next sync does not resurrect it.
CREATE TABLE IF NOT EXISTS strava_activity_cache (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    strava_activity_id TEXT NOT NULL,
    external_id TEXT,
    name TEXT,
    activity_type TEXT,
    sport_type TEXT,
    start_time TIMESTAMP NOT NULL,
    start_time_local TIMESTAMP,
    timezone TEXT,
    elapsed_time_sec INTEGER,
    moving_time_sec INTEGER,
    distance_m REAL,
    avg_heart_rate INTEGER,
    max_heart_rate INTEGER,
    has_heartrate BOOLEAN NOT NULL DEFAULT FALSE,
    calories INTEGER,
    kilojoules REAL,
    suffer_score REAL,
    device_name TEXT,
    trainer BOOLEAN NOT NULL DEFAULT FALSE,
    manual BOOLEAN NOT NULL DEFAULT FALSE,
    detail_fetched BOOLEAN NOT NULL DEFAULT FALSE,
    raw_data TEXT,
    session_id INTEGER,
    dismissed BOOLEAN NOT NULL DEFAULT FALSE,
    synced_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, strava_activity_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_strava_activity_cache_user_time
    ON strava_activity_cache(user_id, start_time);

CREATE INDEX IF NOT EXISTS idx_strava_activity_cache_session
    ON strava_activity_cache(session_id);

-- Short-lived CSRF tokens for OAuth flow
CREATE TABLE IF NOT EXISTS strava_oauth_states (
    id SERIAL PRIMARY KEY,
    state_token TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_strava_oauth_states_token
    ON strava_oauth_states(state_token);

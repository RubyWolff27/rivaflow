-- 113_whoop_sessions.sql
-- SQLite local-dev variant of 113_whoop_sessions_pg.sql.
-- (Keep these comments free of the semicolon character, which the migration runner splits on.)
CREATE TABLE IF NOT EXISTS whoop_sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    activity    TEXT    NOT NULL,
    started_at  TEXT    NOT NULL,
    ended_at    TEXT,
    source      TEXT    NOT NULL DEFAULT 'app',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS whoop_sessions_user_started_idx
    ON whoop_sessions (user_id, started_at DESC);

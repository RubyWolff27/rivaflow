-- 111_whoop_alerts.sql
-- SQLite local-dev variant of 111_whoop_alerts_pg.sql.
-- (Keep these comments free of the semicolon character, which the migration runner splits on.)
CREATE TABLE IF NOT EXISTS whoop_alerts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    day         TEXT    NOT NULL,
    alert_key   TEXT    NOT NULL,
    tier        TEXT    NOT NULL,
    headline    TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, day, alert_key),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS whoop_alerts_user_day_idx ON whoop_alerts (user_id, day);

-- 112_whoop_cockpit_snapshot.sql
-- SQLite local-dev variant of 112_whoop_cockpit_snapshot_pg.sql.
-- (Keep these comments free of the semicolon character, which the migration runner splits on.)
CREATE TABLE IF NOT EXISTS whoop_cockpit_snapshot (
    user_id     INTEGER PRIMARY KEY,
    html        TEXT    NOT NULL,
    rendered_at TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

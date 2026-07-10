-- 117_whoop_daily_agg.sql
-- SQLite local-dev variant of 117_whoop_daily_agg_pg.sql.
-- (Keep these comments free of the semicolon character, which the migration runner splits on.)
CREATE TABLE IF NOT EXISTS whoop_daily_agg (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    day             TEXT    NOT NULL,
    metrics_json    TEXT    NOT NULL,
    deriver_version TEXT    NOT NULL,
    sample_count    INTEGER NOT NULL,
    complete        BOOLEAN NOT NULL DEFAULT 1,
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (user_id, day)
);

CREATE INDEX IF NOT EXISTS whoop_daily_agg_user_day_idx
    ON whoop_daily_agg (user_id, day);

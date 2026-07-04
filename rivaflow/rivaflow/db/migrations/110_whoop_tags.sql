-- 110_whoop_tags.sql
-- SQLite local-dev variant of 110_whoop_tags_pg.sql.
-- (Keep these comments free of the semicolon character, which the migration runner splits on.)
CREATE TABLE IF NOT EXISTS whoop_tags (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    day         TEXT    NOT NULL,
    tag         TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, day, tag),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS whoop_tags_user_day_idx ON whoop_tags (user_id, day);
CREATE INDEX IF NOT EXISTS whoop_tags_user_tag_idx ON whoop_tags (user_id, tag);

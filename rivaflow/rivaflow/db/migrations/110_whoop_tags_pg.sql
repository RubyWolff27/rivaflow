-- 110_whoop_tags_pg.sql
-- Journal tags for the WHOOP data platform (PostgreSQL / production).
-- See 110_whoop_tags.sql for the SQLite (local dev) variant.
--
-- A tag records that something happened on a given LOCAL day (alcohol, late-training, ill,
-- poor-sleep, travel, sabbath-rest). Tags feed B11 behaviour correlation and the B6 prevention
-- validation gate, where an "ill" tag is an illness-onset label. One row per (user, day, tag).
-- (Keep these comments free of the semicolon character, which the migration runner treats as a
--  statement separator even inside a comment.)
CREATE TABLE IF NOT EXISTS whoop_tags (
    id          BIGSERIAL   PRIMARY KEY,
    user_id     INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day         DATE        NOT NULL,
    tag         TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, day, tag)
);

CREATE INDEX IF NOT EXISTS whoop_tags_user_day_idx ON whoop_tags (user_id, day);
CREATE INDEX IF NOT EXISTS whoop_tags_user_tag_idx ON whoop_tags (user_id, tag);

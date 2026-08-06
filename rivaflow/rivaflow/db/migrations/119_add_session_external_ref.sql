-- 119_add_session_external_ref.sql
-- Idempotent ingest key (SQLite / local dev).
-- See 119_add_session_external_ref_pg.sql for the PostgreSQL (production) variant.
--
-- external_ref uniquely identifies the upstream source record for a session
-- (for example a Google Health point id from the Wahoo push), so replaying the
-- same source record cannot create a duplicate session. Manually-logged
-- sessions leave external_ref NULL and stay unconstrained because the unique
-- index is partial (only non-null refs are indexed).

ALTER TABLE sessions ADD COLUMN external_ref TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS sessions_user_external_ref_uidx
    ON sessions (user_id, external_ref)
    WHERE external_ref IS NOT NULL;

-- 119_add_session_external_ref_pg.sql
-- Idempotent ingest key (PostgreSQL / production).
--
-- external_ref uniquely identifies the upstream source record for a session
-- (for example a Google Health point id from the Wahoo push), so replaying the
-- same source record cannot create a duplicate session. The unique index is
-- partial so it covers only non-null refs, leaving manually-logged sessions
-- (external_ref NULL) unconstrained.

ALTER TABLE sessions ADD COLUMN IF NOT EXISTS external_ref TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS sessions_user_external_ref_uidx
    ON sessions (user_id, external_ref)
    WHERE external_ref IS NOT NULL;

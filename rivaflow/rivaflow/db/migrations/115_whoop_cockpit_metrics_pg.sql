-- 115_whoop_cockpit_metrics_pg.sql
-- Persist the cockpit's structured metrics alongside the rendered HTML (PG).
-- Before this the snapshot stored only HTML, so nothing could read "what the
-- cockpit knew" as data without re-running the ~40s recompute. metrics_json is
-- the whoop_summary JSON contract the phone and a future model layer consume,
-- deriver_version records which analytics version produced it.
ALTER TABLE whoop_cockpit_snapshot ADD COLUMN IF NOT EXISTS metrics_json TEXT;
ALTER TABLE whoop_cockpit_snapshot ADD COLUMN IF NOT EXISTS deriver_version TEXT;

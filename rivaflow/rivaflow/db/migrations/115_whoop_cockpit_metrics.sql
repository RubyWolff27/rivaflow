-- 115_whoop_cockpit_metrics.sql
-- Persist the cockpit's structured metrics alongside the HTML (SQLite/test).
-- metrics_json = the whoop_summary JSON contract, deriver_version = its version.
ALTER TABLE whoop_cockpit_snapshot ADD COLUMN metrics_json TEXT;
ALTER TABLE whoop_cockpit_snapshot ADD COLUMN deriver_version TEXT;

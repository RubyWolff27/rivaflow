-- Migration 087: Add session performance score columns
ALTER TABLE sessions ADD COLUMN session_score REAL;
ALTER TABLE sessions ADD COLUMN score_breakdown TEXT;
ALTER TABLE sessions ADD COLUMN score_version INTEGER DEFAULT 1;

CREATE INDEX IF NOT EXISTS idx_sessions_session_score ON sessions(session_score);

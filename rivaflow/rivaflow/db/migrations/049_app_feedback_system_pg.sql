-- PostgreSQL version (auto-generated from sibling .sql file)
-- Translations applied: AUTOINCREMENT→BIGSERIAL, *_id INTEGER→BIGINT,
-- datetime('now')→CURRENT_TIMESTAMP, BOOLEAN 0/1→FALSE/TRUE,
-- PRAGMA/BEGIN/COMMIT removed, CREATE INDEX→IF NOT EXISTS.
-- Regenerate: bun /tmp/translate_sqlite_to_pg.py (see note in header)

-- Migration 049: General app feedback system
-- Created: 2026-02-02
-- Purpose: Allow users to submit feedback about the app

CREATE TABLE IF NOT EXISTS app_feedback (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,  -- 'bug', 'feature', 'improvement', 'question', 'other'
    subject VARCHAR(200),
    message TEXT NOT NULL,
    platform VARCHAR(50),  -- 'web', 'cli', 'api'
    version VARCHAR(20),
    url VARCHAR(500),  -- Page/route where feedback was submitted
    status VARCHAR(20) DEFAULT 'new',  -- 'new', 'reviewing', 'resolved', 'closed'
    admin_notes TEXT,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_app_feedback_user_id ON app_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_app_feedback_category ON app_feedback(category);
CREATE INDEX IF NOT EXISTS idx_app_feedback_status ON app_feedback(status);
CREATE INDEX IF NOT EXISTS idx_app_feedback_created_at ON app_feedback(created_at DESC);

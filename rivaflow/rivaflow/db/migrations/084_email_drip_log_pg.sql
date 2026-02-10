-- Drip email tracking table (PostgreSQL)
CREATE TABLE IF NOT EXISTS email_drip_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email_key TEXT NOT NULL,
    sent_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_email_drip_user_key
    ON email_drip_log(user_id, email_key);

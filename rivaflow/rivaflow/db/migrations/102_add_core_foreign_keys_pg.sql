-- Add missing foreign key constraints for core entity relationships.
-- Uses simple ALTER TABLE statements (no DO $$ blocks — they break the semicolon splitter).
-- The migration runner uses SAVEPOINT per statement, so if a constraint already exists
-- the statement fails safely and processing continues.

-- sessions.user_id -> users(id) ON DELETE CASCADE
ALTER TABLE sessions ADD CONSTRAINT fk_sessions_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- session_techniques.session_id -> sessions(id) ON DELETE CASCADE
ALTER TABLE session_techniques ADD CONSTRAINT fk_session_techniques_session_id FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE;

-- session_rolls.session_id -> sessions(id) ON DELETE CASCADE
ALTER TABLE session_rolls ADD CONSTRAINT fk_session_rolls_session_id FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE;

-- profile.user_id -> users(id) ON DELETE CASCADE
ALTER TABLE profile ADD CONSTRAINT fk_profile_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- readiness.user_id -> users(id) ON DELETE CASCADE
ALTER TABLE readiness ADD CONSTRAINT fk_readiness_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

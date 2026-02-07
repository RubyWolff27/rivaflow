-- 066_add_check_constraints_pg.sql (PostgreSQL)
-- Add CHECK constraints for data integrity on sessions and session_rolls tables.

ALTER TABLE sessions ADD CONSTRAINT chk_sessions_rolls_non_negative CHECK (rolls >= 0);
ALTER TABLE sessions ADD CONSTRAINT chk_sessions_subs_for_non_negative CHECK (submissions_for >= 0);
ALTER TABLE sessions ADD CONSTRAINT chk_sessions_subs_against_non_negative CHECK (submissions_against >= 0);
ALTER TABLE sessions ADD CONSTRAINT chk_sessions_duration_positive CHECK (duration_mins > 0);

ALTER TABLE session_rolls ADD CONSTRAINT chk_session_rolls_roll_number_positive CHECK (roll_number >= 1);
ALTER TABLE session_rolls ADD CONSTRAINT chk_session_rolls_duration_positive CHECK (duration_mins IS NULL OR duration_mins > 0);

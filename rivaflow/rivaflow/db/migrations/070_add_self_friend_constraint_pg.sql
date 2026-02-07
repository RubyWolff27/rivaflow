-- Migration 070: Add CHECK constraint to prevent self-friending
-- PostgreSQL version

-- Remove any existing self-friend rows (should not exist, but be safe)
DELETE FROM friend_connections WHERE requester_id = recipient_id;

ALTER TABLE friend_connections
    ADD CONSTRAINT no_self_friend CHECK (requester_id != recipient_id);

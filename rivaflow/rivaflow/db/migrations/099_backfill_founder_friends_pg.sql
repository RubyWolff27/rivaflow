-- 099: Backfill founder friendships for existing users
-- One-time migration: creates accepted friendships between the founder
-- (rubywolff@gmail.com) and every other user who isn't already connected.
-- Idempotent: skips users who already have a connection row (any status).

INSERT INTO friend_connections (requester_id, recipient_id, status, connection_source, responded_at)
SELECT f.id, u.id, 'accepted', 'founder', NOW()
FROM users u
CROSS JOIN (SELECT id FROM users WHERE email = 'rubywolff@gmail.com') f
WHERE u.id != f.id
  AND NOT EXISTS (
    SELECT 1 FROM friend_connections fc
    WHERE (fc.requester_id = f.id AND fc.recipient_id = u.id)
       OR (fc.requester_id = u.id AND fc.recipient_id = f.id)
  );

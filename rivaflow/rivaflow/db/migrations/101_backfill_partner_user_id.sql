-- Backfill partner_user_id on existing session_rolls by matching partner_name
-- against the session owner's social connections (friend_connections + users)
-- SQLite-compatible: uses correlated subquery instead of UPDATE ... FROM
UPDATE session_rolls
SET partner_user_id = (
    SELECT u.id
    FROM sessions s
    JOIN friend_connections fc ON fc.status = 'accepted'
        AND (fc.requester_id = s.user_id OR fc.recipient_id = s.user_id)
    JOIN users u ON u.id = CASE
        WHEN fc.requester_id = s.user_id THEN fc.recipient_id
        ELSE fc.requester_id
    END
    WHERE s.id = session_rolls.session_id
      AND LOWER(TRIM(session_rolls.partner_name)) = LOWER(TRIM(u.first_name || ' ' || u.last_name))
    LIMIT 1
)
WHERE partner_user_id IS NULL
  AND partner_name IS NOT NULL
  AND EXISTS (
    SELECT 1
    FROM sessions s
    JOIN friend_connections fc ON fc.status = 'accepted'
        AND (fc.requester_id = s.user_id OR fc.recipient_id = s.user_id)
    JOIN users u ON u.id = CASE
        WHEN fc.requester_id = s.user_id THEN fc.recipient_id
        ELSE fc.requester_id
    END
    WHERE s.id = session_rolls.session_id
      AND LOWER(TRIM(session_rolls.partner_name)) = LOWER(TRIM(u.first_name || ' ' || u.last_name))
  );

-- Backfill partner_user_id on existing session_rolls by matching partner_name
-- against the session owner's social connections (friend_connections + users)
UPDATE session_rolls
SET partner_user_id = matched.friend_user_id
FROM (
    SELECT sr.id as roll_id, u.id as friend_user_id
    FROM session_rolls sr
    JOIN sessions s ON sr.session_id = s.id
    JOIN friend_connections fc ON fc.status = 'accepted'
        AND (fc.requester_id = s.user_id OR fc.recipient_id = s.user_id)
    JOIN users u ON u.id = CASE
        WHEN fc.requester_id = s.user_id THEN fc.recipient_id
        ELSE fc.requester_id
    END
    WHERE sr.partner_user_id IS NULL
      AND sr.partner_name IS NOT NULL
      AND LOWER(TRIM(sr.partner_name)) = LOWER(TRIM(u.first_name || ' ' || u.last_name))
) AS matched
WHERE session_rolls.id = matched.roll_id;

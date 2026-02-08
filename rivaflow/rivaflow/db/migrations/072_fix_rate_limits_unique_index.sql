-- Migration 072: Ensure grapple_rate_limits unique index exists
-- The unique index on (user_id, window_start) is required for ON CONFLICT upsert.
-- Deduplicate any existing rows first, keeping the one with the highest message_count.

DELETE FROM grapple_rate_limits
WHERE id NOT IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (
            PARTITION BY user_id, window_start
            ORDER BY message_count DESC, created_at DESC
        ) AS rn
        FROM grapple_rate_limits
    ) sub
    WHERE rn = 1
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_grapple_rate_limits_user_window
    ON grapple_rate_limits(user_id, window_start);

-- Migration 057: Fix PostgreSQL sequences after data migration
-- Reset all sequences to match current max IDs
-- This fixes "duplicate key" errors when inserting new records

-- Users
SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 1), true);

-- Profile
SELECT setval('profile_id_seq', COALESCE((SELECT MAX(id) FROM profile), 1), true);

-- Streaks - CRITICAL for registration
SELECT setval('streaks_id_seq', COALESCE((SELECT MAX(id) FROM streaks), 1), true);

-- Sessions
SELECT setval('sessions_id_seq', COALESCE((SELECT MAX(id) FROM sessions), 1), true);

-- Gradings
SELECT setval('gradings_id_seq', COALESCE((SELECT MAX(id) FROM gradings), 1), true);

-- Readiness
SELECT setval('readiness_id_seq', COALESCE((SELECT MAX(id) FROM readiness), 1), true);

-- Friends
SELECT setval('friends_id_seq', COALESCE((SELECT MAX(id) FROM friends), 1), true);

-- Movements Glossary
SELECT setval('movements_glossary_id_seq', COALESCE((SELECT MAX(id) FROM movements_glossary), 1), true);

-- Gyms
SELECT setval('gyms_id_seq', COALESCE((SELECT MAX(id) FROM gyms), 1), true);

-- Daily Checkins
SELECT setval('daily_checkins_id_seq', COALESCE((SELECT MAX(id) FROM daily_checkins), 1), true);

-- Goal Progress
SELECT setval('goal_progress_id_seq', COALESCE((SELECT MAX(id) FROM goal_progress), 1), true);

-- Refresh Tokens
SELECT setval('refresh_tokens_id_seq', COALESCE((SELECT MAX(id) FROM refresh_tokens), 1), true);

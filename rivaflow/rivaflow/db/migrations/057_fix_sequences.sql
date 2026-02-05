-- Migration 057: Fix PostgreSQL sequences after data migration
-- Reset all sequences to match current max IDs
-- This fixes "duplicate key" errors when inserting new records
-- Each sequence check is a separate DO block to work with semicolon-based statement splitting

-- Users
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'users_id_seq') THEN
        PERFORM setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 1), true);
    END IF;
END $$;

-- Profile
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'profile_id_seq') THEN
        PERFORM setval('profile_id_seq', COALESCE((SELECT MAX(id) FROM profile), 1), true);
    END IF;
END $$;

-- Streaks - CRITICAL for registration
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'streaks_id_seq') THEN
        PERFORM setval('streaks_id_seq', COALESCE((SELECT MAX(id) FROM streaks), 1), true);
    END IF;
END $$;

-- Sessions
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'sessions_id_seq') THEN
        PERFORM setval('sessions_id_seq', COALESCE((SELECT MAX(id) FROM sessions), 1), true);
    END IF;
END $$;

-- Gradings
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'gradings_id_seq') THEN
        PERFORM setval('gradings_id_seq', COALESCE((SELECT MAX(id) FROM gradings), 1), true);
    END IF;
END $$;

-- Readiness
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'readiness_id_seq') THEN
        PERFORM setval('readiness_id_seq', COALESCE((SELECT MAX(id) FROM readiness), 1), true);
    END IF;
END $$;

-- Friends
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'friends_id_seq') THEN
        PERFORM setval('friends_id_seq', COALESCE((SELECT MAX(id) FROM friends), 1), true);
    END IF;
END $$;

-- Movements Glossary
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'movements_glossary_id_seq') THEN
        PERFORM setval('movements_glossary_id_seq', COALESCE((SELECT MAX(id) FROM movements_glossary), 1), true);
    END IF;
END $$;

-- Gyms
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'gyms_id_seq') THEN
        PERFORM setval('gyms_id_seq', COALESCE((SELECT MAX(id) FROM gyms), 1), true);
    END IF;
END $$;

-- Daily Checkins
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'daily_checkins_id_seq') THEN
        PERFORM setval('daily_checkins_id_seq', COALESCE((SELECT MAX(id) FROM daily_checkins), 1), true);
    END IF;
END $$;

-- Goal Progress
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'goal_progress_id_seq') THEN
        PERFORM setval('goal_progress_id_seq', COALESCE((SELECT MAX(id) FROM goal_progress), 1), true);
    END IF;
END $$;

-- Refresh Tokens
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'refresh_tokens_id_seq') THEN
        PERFORM setval('refresh_tokens_id_seq', COALESCE((SELECT MAX(id) FROM refresh_tokens), 1), true);
    END IF;
END $$;

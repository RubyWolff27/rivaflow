-- Manual sequence fix for RivaFlow PostgreSQL database
-- Run this in the Render database shell to fix sequence issues
-- This script safely resets only sequences that exist

-- First, let's see which sequences actually exist:
SELECT schemaname, sequencename
FROM pg_sequences
WHERE schemaname = 'public';

-- Now reset sequences for tables that have them
-- Each statement is wrapped in DO block to handle missing sequences gracefully

DO $$
BEGIN
    -- Users
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'users_id_seq') THEN
        PERFORM setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 1), true);
        RAISE NOTICE 'Reset users_id_seq';
    END IF;

    -- Streaks (CRITICAL for registration)
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'streaks_id_seq') THEN
        PERFORM setval('streaks_id_seq', COALESCE((SELECT MAX(id) FROM streaks), 1), true);
        RAISE NOTICE 'Reset streaks_id_seq';
    END IF;

    -- Sessions
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'sessions_id_seq') THEN
        PERFORM setval('sessions_id_seq', COALESCE((SELECT MAX(id) FROM sessions), 1), true);
        RAISE NOTICE 'Reset sessions_id_seq';
    END IF;

    -- Gradings
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'gradings_id_seq') THEN
        PERFORM setval('gradings_id_seq', COALESCE((SELECT MAX(id) FROM gradings), 1), true);
        RAISE NOTICE 'Reset gradings_id_seq';
    END IF;

    -- Readiness
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'readiness_id_seq') THEN
        PERFORM setval('readiness_id_seq', COALESCE((SELECT MAX(id) FROM readiness), 1), true);
        RAISE NOTICE 'Reset readiness_id_seq';
    END IF;

    -- Friends
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'friends_id_seq') THEN
        PERFORM setval('friends_id_seq', COALESCE((SELECT MAX(id) FROM friends), 1), true);
        RAISE NOTICE 'Reset friends_id_seq';
    END IF;

    -- Movements Glossary
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'movements_glossary_id_seq') THEN
        PERFORM setval('movements_glossary_id_seq', COALESCE((SELECT MAX(id) FROM movements_glossary), 1), true);
        RAISE NOTICE 'Reset movements_glossary_id_seq';
    END IF;

    -- Profile
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'profile_id_seq') THEN
        PERFORM setval('profile_id_seq', COALESCE((SELECT MAX(id) FROM profile), 1), true);
        RAISE NOTICE 'Reset profile_id_seq';
    END IF;

    -- Gyms
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'gyms_id_seq') THEN
        PERFORM setval('gyms_id_seq', COALESCE((SELECT MAX(id) FROM gyms), 1), true);
        RAISE NOTICE 'Reset gyms_id_seq';
    END IF;

    -- Daily Checkins
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'daily_checkins_id_seq') THEN
        PERFORM setval('daily_checkins_id_seq', COALESCE((SELECT MAX(id) FROM daily_checkins), 1), true);
        RAISE NOTICE 'Reset daily_checkins_id_seq';
    END IF;

    -- Goal Progress
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'goal_progress_id_seq') THEN
        PERFORM setval('goal_progress_id_seq', COALESCE((SELECT MAX(id) FROM goal_progress), 1), true);
        RAISE NOTICE 'Reset goal_progress_id_seq';
    END IF;

    -- Refresh Tokens
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'refresh_tokens_id_seq') THEN
        PERFORM setval('refresh_tokens_id_seq', COALESCE((SELECT MAX(id) FROM refresh_tokens), 1), true);
        RAISE NOTICE 'Reset refresh_tokens_id_seq';
    END IF;
END $$;

-- ============================================================================
-- MIGRATION 046: Comprehensive Social Features (Strava-style)
-- Created: 2026-02-01
-- Purpose: Add complete social/friend discovery system with profiles, connections,
--          suggestions, activity feed, and privacy controls
-- ============================================================================

-- ============================================================================
-- PART 1: ENHANCE USERS TABLE WITH SOCIAL PROFILE FIELDS
-- ============================================================================

-- Add username (unique handle for search/mentions)
ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(50) UNIQUE;

-- Add display name (public name shown to others)
ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name VARCHAR(100);

-- Add bio (profile description)
ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT;

-- Add belt rank and stripes
ALTER TABLE users ADD COLUMN IF NOT EXISTS belt_rank VARCHAR(20) DEFAULT 'white' CHECK (
    belt_rank IN ('white', 'blue', 'purple', 'brown', 'black', 'red_black', 'red_white', 'red')
);
ALTER TABLE users ADD COLUMN IF NOT EXISTS belt_stripes INTEGER DEFAULT 0 CHECK (belt_stripes >= 0 AND belt_stripes <= 4);

-- Add location fields (city, state, country, coordinates)
ALTER TABLE users ADD COLUMN IF NOT EXISTS location_city VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS location_state VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS location_country VARCHAR(100) DEFAULT 'USA';
ALTER TABLE users ADD COLUMN IF NOT EXISTS location_lat DECIMAL(10, 8);
ALTER TABLE users ADD COLUMN IF NOT EXISTS location_lng DECIMAL(11, 8);

-- Add profile photo (already exists as avatar_url, but add profile_photo_url for clarity)
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_photo_url TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS cover_photo_url TEXT;

-- Add training info
ALTER TABLE users ADD COLUMN IF NOT EXISTS started_training DATE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_style VARCHAR(20) DEFAULT 'both' CHECK (
    preferred_style IN ('gi', 'no-gi', 'both')
);
ALTER TABLE users ADD COLUMN IF NOT EXISTS weight_class VARCHAR(20);

-- Add social links (JSON)
ALTER TABLE users ADD COLUMN IF NOT EXISTS social_links JSONB DEFAULT '{}';

-- Add privacy settings (defaults to friends-only)
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_visibility VARCHAR(20) DEFAULT 'friends' CHECK (
    profile_visibility IN ('public', 'friends', 'private')
);
ALTER TABLE users ADD COLUMN IF NOT EXISTS activity_visibility VARCHAR(20) DEFAULT 'friends' CHECK (
    activity_visibility IN ('public', 'friends', 'private')
);
ALTER TABLE users ADD COLUMN IF NOT EXISTS searchable BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS show_location BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS show_gym BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS allow_tagging BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS require_tag_approval BOOLEAN DEFAULT FALSE;

-- Create indexes for user search and discovery
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username) WHERE username IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_display_name ON users(display_name) WHERE display_name IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_location_city ON users(location_city, location_country) WHERE location_city IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_belt_rank ON users(belt_rank);
CREATE INDEX IF NOT EXISTS idx_users_searchable ON users(searchable) WHERE searchable = TRUE;

-- ============================================================================
-- PART 2: ENHANCE GYMS TABLE
-- ============================================================================

-- Add slug for URL-friendly gym names
ALTER TABLE gyms ADD COLUMN IF NOT EXISTS slug VARCHAR(200) UNIQUE;

-- Add affiliation (e.g., "Gracie Barra", "10th Planet")
ALTER TABLE gyms ADD COLUMN IF NOT EXISTS affiliation VARCHAR(100);

-- Add coordinates for location-based search
ALTER TABLE gyms ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 8);
ALTER TABLE gyms ADD COLUMN IF NOT EXISTS longitude DECIMAL(11, 8);

-- Add contact info
ALTER TABLE gyms ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
ALTER TABLE gyms ADD COLUMN IF NOT EXISTS instagram VARCHAR(100);

-- Add head coach info
ALTER TABLE gyms ADD COLUMN IF NOT EXISTS head_coach VARCHAR(100);

-- Add member count (cached)
ALTER TABLE gyms ADD COLUMN IF NOT EXISTS member_count INTEGER DEFAULT 0;

-- Add postal code
ALTER TABLE gyms ADD COLUMN IF NOT EXISTS postal_code VARCHAR(20);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_gyms_slug ON gyms(slug) WHERE slug IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_gyms_affiliation ON gyms(affiliation) WHERE affiliation IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_gyms_city_country ON gyms(city, country);

-- ============================================================================
-- PART 3: USER-GYMS JUNCTION TABLE (MANY-TO-MANY)
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_gyms (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    gym_id INTEGER NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
    is_primary BOOLEAN DEFAULT FALSE,
    joined_at DATE,
    left_at DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'former', 'visitor')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, gym_id)
);

CREATE INDEX IF NOT EXISTS idx_user_gyms_user ON user_gyms(user_id);
CREATE INDEX IF NOT EXISTS idx_user_gyms_gym ON user_gyms(gym_id);
CREATE INDEX IF NOT EXISTS idx_user_gyms_status ON user_gyms(status) WHERE status = 'active';

-- ============================================================================
-- PART 4: FRIEND CONNECTIONS TABLE (BIDIRECTIONAL WITH REQUEST FLOW)
-- ============================================================================

CREATE TABLE IF NOT EXISTS friend_connections (
    id SERIAL PRIMARY KEY,
    requester_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'accepted', 'declined', 'blocked', 'cancelled')
    ),
    connection_source VARCHAR(30) CHECK (
        connection_source IN ('search', 'gym', 'mutual', 'partner', 'location', 'import', 'qr_code')
    ),
    request_message TEXT,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    responded_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_connection UNIQUE (requester_id, recipient_id),
    CONSTRAINT no_self_friend CHECK (requester_id != recipient_id)
);

CREATE INDEX IF NOT EXISTS idx_friend_connections_requester ON friend_connections(requester_id);
CREATE INDEX IF NOT EXISTS idx_friend_connections_recipient ON friend_connections(recipient_id);
CREATE INDEX IF NOT EXISTS idx_friend_connections_status ON friend_connections(status);
CREATE INDEX IF NOT EXISTS idx_friend_connections_pending ON friend_connections(recipient_id, status)
    WHERE status = 'pending';

-- ============================================================================
-- PART 5: BLOCKED USERS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS blocked_users (
    id SERIAL PRIMARY KEY,
    blocker_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    blocked_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason TEXT,
    blocked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(blocker_id, blocked_id),
    CONSTRAINT no_self_block CHECK (blocker_id != blocked_id)
);

CREATE INDEX IF NOT EXISTS idx_blocked_users_blocker ON blocked_users(blocker_id);
CREATE INDEX IF NOT EXISTS idx_blocked_users_blocked ON blocked_users(blocked_id);

-- ============================================================================
-- PART 6: FRIEND SUGGESTIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS friend_suggestions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    suggested_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score DECIMAL(5, 2) DEFAULT 0,
    reasons JSONB DEFAULT '[]',
    mutual_friends_count INTEGER DEFAULT 0,
    dismissed BOOLEAN DEFAULT FALSE,
    dismissed_at TIMESTAMP WITH TIME ZONE,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, suggested_user_id)
);

CREATE INDEX IF NOT EXISTS idx_friend_suggestions_user ON friend_suggestions(user_id);
CREATE INDEX IF NOT EXISTS idx_friend_suggestions_score ON friend_suggestions(user_id, score DESC)
    WHERE dismissed = FALSE;
CREATE INDEX IF NOT EXISTS idx_friend_suggestions_generated ON friend_suggestions(generated_at);

-- ============================================================================
-- PART 7: ACTIVITY FEED TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS activity_feed (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL CHECK (
        activity_type IN ('session', 'milestone', 'streak', 'belt_promotion', 'new_gym', 'friend_joined')
    ),
    content JSONB NOT NULL,
    related_id INTEGER, -- Session ID, milestone ID, etc.
    visibility VARCHAR(20) DEFAULT 'friends' CHECK (
        visibility IN ('public', 'friends', 'private')
    ),
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activity_feed_user ON activity_feed(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_feed_created ON activity_feed(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_feed_type ON activity_feed(activity_type);
CREATE INDEX IF NOT EXISTS idx_activity_feed_visibility ON activity_feed(visibility);

-- ============================================================================
-- PART 8: FEED LIKES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS feed_likes (
    id SERIAL PRIMARY KEY,
    activity_id INTEGER NOT NULL REFERENCES activity_feed(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(activity_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_feed_likes_activity ON feed_likes(activity_id);
CREATE INDEX IF NOT EXISTS idx_feed_likes_user ON feed_likes(user_id);

-- ============================================================================
-- PART 9: FEED COMMENTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS feed_comments (
    id SERIAL PRIMARY KEY,
    activity_id INTEGER NOT NULL REFERENCES activity_feed(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL CHECK (length(content) > 0 AND length(content) <= 1000),
    parent_comment_id INTEGER REFERENCES feed_comments(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feed_comments_activity ON feed_comments(activity_id);
CREATE INDEX IF NOT EXISTS idx_feed_comments_user ON feed_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_feed_comments_parent ON feed_comments(parent_comment_id);

-- ============================================================================
-- PART 10: PARTNER LINKS TABLE (LINK TEXT PARTNERS TO REAL USERS)
-- ============================================================================

CREATE TABLE IF NOT EXISTS partner_links (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    partner_name VARCHAR(100) NOT NULL, -- The text name used in sessions
    linked_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    link_status VARCHAR(20) DEFAULT 'suggested' CHECK (
        link_status IN ('suggested', 'confirmed', 'rejected')
    ),
    confidence DECIMAL(3, 2) DEFAULT 0, -- 0.00 to 1.00
    session_count INTEGER DEFAULT 0, -- How many times they've trained together
    suggested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confirmed_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, partner_name)
);

CREATE INDEX IF NOT EXISTS idx_partner_links_user ON partner_links(user_id);
CREATE INDEX IF NOT EXISTS idx_partner_links_linked_user ON partner_links(linked_user_id);
CREATE INDEX IF NOT EXISTS idx_partner_links_status ON partner_links(link_status);

-- ============================================================================
-- DATA MIGRATION: SYNC EXISTING DATA
-- ============================================================================

-- Sync primary_gym_id to user_gyms table (for existing users with home gym set)
INSERT INTO user_gyms (user_id, gym_id, is_primary, status, joined_at)
SELECT id, primary_gym_id, TRUE, 'active', created_at::date
FROM users
WHERE primary_gym_id IS NOT NULL
ON CONFLICT (user_id, gym_id) DO NOTHING;

-- Generate slugs for existing gyms (simple slug: lowercase, replace spaces with hyphens)
UPDATE gyms
SET slug = LOWER(REGEXP_REPLACE(name || '-' || COALESCE(city, 'gym'), '[^a-zA-Z0-9]+', '-', 'g'))
WHERE slug IS NULL;

-- Set display_name to first_name + last_name for existing users
UPDATE users
SET display_name = TRIM(CONCAT(first_name, ' ', last_name))
WHERE display_name IS NULL AND (first_name IS NOT NULL OR last_name IS NOT NULL);

-- Generate usernames from email (before @ symbol) for existing users
UPDATE users
SET username = LOWER(REGEXP_REPLACE(SPLIT_PART(email, '@', 1), '[^a-z0-9_]', '', 'g'))
WHERE username IS NULL;

-- Handle duplicate usernames by appending user ID
UPDATE users u1
SET username = username || '_' || id
WHERE username IS NOT NULL
  AND EXISTS (
    SELECT 1 FROM users u2
    WHERE u2.username = u1.username AND u2.id < u1.id
  );

-- ============================================================================
-- COMMENTS & NOTES
-- ============================================================================

-- This migration adds complete social features:
-- 1. Enhanced user profiles with privacy controls
-- 2. Enhanced gyms with location and affiliation
-- 3. Many-to-many user-gym relationships
-- 4. Bidirectional friend connections with request/accept flow
-- 5. Blocking functionality
-- 6. Friend suggestions with scoring
-- 7. Activity feed for sharing training updates
-- 8. Partner linking to connect text names to real users
--
-- Privacy-first design:
-- - All visibility defaults to 'friends' only
-- - Users can control profile, activity, location, and gym visibility
-- - Blocked users are completely invisible to each other
-- - Partner linking requires consent
--
-- Next steps:
-- - Implement backend repositories and services
-- - Create API endpoints with privacy filtering
-- - Build frontend UI for profiles, connections, and feed
-- - Implement suggestion algorithm
-- - Add background jobs for suggestion generation

COMMENT ON TABLE friend_connections IS 'Bidirectional friend connections with request/accept flow (like Facebook/Strava)';
COMMENT ON TABLE user_relationships IS 'Legacy one-way following (migration 026). Use friend_connections for new social features.';
COMMENT ON TABLE friend_suggestions IS 'AI-generated friend suggestions based on gym, mutual friends, partner matching, location';
COMMENT ON TABLE partner_links IS 'Links text partner names from sessions to real user accounts (with consent)';
COMMENT ON TABLE activity_feed IS 'Centralized activity feed for sharing training milestones with friends';

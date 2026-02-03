-- Migration 044: Add Grapple AI Coach foundation tables and subscription tiers (PostgreSQL)
-- Created: 2026-02-01
-- Purpose: Foundation for Grapple AI Coach feature with subscription system

-- ============================================================================
-- PART 1: Subscription Tiers & Beta User Management
-- ============================================================================

-- Add subscription tier to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(20) DEFAULT 'free';
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_beta_user BOOLEAN DEFAULT FALSE;

-- Mark all existing users as beta users (grandfathering)
UPDATE users SET subscription_tier = 'beta', is_beta_user = TRUE WHERE subscription_tier = 'free';

-- Add index for quick tier lookups
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users(subscription_tier);

-- ============================================================================
-- PART 2: Enable pgvector Extension for Semantic Search
-- ============================================================================

-- Enable pgvector extension for embedding storage
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- PART 3: Chat Sessions & Messages
-- ============================================================================

-- Chat sessions for organizing conversations
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10, 6) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at DESC);

-- Individual chat messages within sessions
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost_usd DECIMAL(10, 6) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at DESC);

-- ============================================================================
-- PART 4: Token Usage & Cost Monitoring
-- ============================================================================

-- Comprehensive token usage logs for monitoring and billing
CREATE TABLE IF NOT EXISTS token_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,
    message_id UUID REFERENCES chat_messages(id) ON DELETE SET NULL,
    provider VARCHAR(50) NOT NULL,  -- 'groq', 'together', 'ollama'
    model VARCHAR(100) NOT NULL,    -- e.g., 'llama3-70b-8192'
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    cost_usd DECIMAL(10, 6) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_token_usage_logs_user_id ON token_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_logs_created_at ON token_usage_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_token_usage_logs_provider ON token_usage_logs(provider);

-- ============================================================================
-- PART 5: BJJ Knowledge Base for RAG
-- ============================================================================

-- BJJ knowledge base with semantic search via embeddings
CREATE TABLE IF NOT EXISTS bjj_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(50) NOT NULL,  -- 'technique', 'concept', 'position', 'strategy', 'conditioning'
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    source_url TEXT,  -- Optional reference URL
    embedding vector(384),  -- sentence-transformers all-MiniLM-L6-v2 produces 384-dim vectors
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bjj_knowledge_category ON bjj_knowledge(category);

-- Vector similarity search index (using cosine distance)
CREATE INDEX IF NOT EXISTS idx_bjj_knowledge_embedding ON bjj_knowledge
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ============================================================================
-- PART 6: Grapple Feedback System
-- ============================================================================

-- User feedback on AI responses for continuous improvement
CREATE TABLE IF NOT EXISTS grapple_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    rating VARCHAR(10) NOT NULL CHECK (rating IN ('positive', 'negative')),
    category VARCHAR(50),  -- 'helpful', 'accurate', 'relevant', 'unclear', 'incorrect', 'irrelevant'
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_grapple_feedback_user_id ON grapple_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_grapple_feedback_message_id ON grapple_feedback(message_id);
CREATE INDEX IF NOT EXISTS idx_grapple_feedback_rating ON grapple_feedback(rating);
CREATE INDEX IF NOT EXISTS idx_grapple_feedback_created_at ON grapple_feedback(created_at DESC);

-- ============================================================================
-- PART 7: Rate Limiting Tracking
-- ============================================================================

-- Track message counts for rate limiting (alternative to Redis)
CREATE TABLE IF NOT EXISTS grapple_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_grapple_rate_limits_user_id ON grapple_rate_limits(user_id);
CREATE INDEX IF NOT EXISTS idx_grapple_rate_limits_window ON grapple_rate_limits(window_start, window_end);

-- Cleanup old rate limit records (keep last 7 days for analytics)
-- This can be run periodically via a cleanup job

-- ============================================================================
-- PART 8: Admin Monitoring Views
-- ============================================================================

-- Create view for daily usage statistics
CREATE OR REPLACE VIEW grapple_daily_stats AS
SELECT
    DATE(created_at) as date,
    provider,
    COUNT(*) as request_count,
    SUM(total_tokens) as total_tokens,
    SUM(cost_usd) as total_cost_usd,
    AVG(total_tokens) as avg_tokens_per_request
FROM token_usage_logs
GROUP BY DATE(created_at), provider
ORDER BY date DESC, provider;

-- Create view for user usage summary
CREATE OR REPLACE VIEW grapple_user_usage AS
SELECT
    u.id as user_id,
    u.email,
    u.subscription_tier,
    COUNT(DISTINCT cs.id) as total_sessions,
    COUNT(cm.id) as total_messages,
    SUM(tul.total_tokens) as total_tokens,
    SUM(tul.cost_usd) as total_cost_usd,
    MAX(cs.updated_at) as last_activity
FROM users u
LEFT JOIN chat_sessions cs ON u.id = cs.user_id
LEFT JOIN chat_messages cm ON cs.id = cm.session_id
LEFT JOIN token_usage_logs tul ON u.id = tul.user_id
GROUP BY u.id, u.email, u.subscription_tier;

-- ============================================================================
-- Notes & Next Steps
-- ============================================================================

-- This migration establishes:
-- 1. ✓ Subscription tier system (free, beta, premium, admin)
-- 2. ✓ Beta user grandfathering for existing users
-- 3. ✓ Chat sessions and message storage
-- 4. ✓ Comprehensive token usage tracking
-- 5. ✓ BJJ knowledge base with vector embeddings
-- 6. ✓ Feedback system for AI responses
-- 7. ✓ Rate limiting infrastructure
-- 8. ✓ Admin monitoring views

-- Next implementation steps (Phase 1):
-- - Add Grapple dependencies to requirements.txt
-- - Create services/grapple/llm_client.py
-- - Create services/grapple/rate_limiter.py
-- - Create services/grapple/token_monitor.py
-- - Create middleware/feature_access.py
-- - Create routes/grapple.py
-- - Create routes/admin_grapple.py

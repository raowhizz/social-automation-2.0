-- Multi-Tenant Social Media Automation Database Schema
-- PostgreSQL 14+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- TENANTS (RESTAURANTS)
-- ============================================================================
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'trial', 'churned')),
    plan_type VARCHAR(50) DEFAULT 'basic' CHECK (plan_type IN ('basic', 'pro', 'enterprise')),

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    CONSTRAINT slug_format CHECK (slug ~ '^[a-z0-9_]+$')
);

CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_status ON tenants(status);
CREATE INDEX idx_tenants_created ON tenants(created_at);

-- ============================================================================
-- TENANT USERS (Restaurant Admins/Staff)
-- ============================================================================
CREATE TABLE tenant_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'admin' CHECK (role IN ('owner', 'admin', 'manager', 'staff')),

    -- Authentication (for future)
    password_hash VARCHAR(255),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,

    -- Constraints
    UNIQUE(tenant_id, email)
);

CREATE INDEX idx_tenant_users_tenant ON tenant_users(tenant_id);
CREATE INDEX idx_tenant_users_email ON tenant_users(email);

-- ============================================================================
-- SOCIAL ACCOUNTS (Facebook Pages & Instagram Accounts)
-- ============================================================================
CREATE TABLE social_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Platform details
    platform VARCHAR(50) NOT NULL CHECK (platform IN ('facebook', 'instagram', 'tiktok', 'twitter')),
    platform_account_id VARCHAR(255) NOT NULL,
    platform_username VARCHAR(255),
    account_name VARCHAR(255),
    account_type VARCHAR(50),

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sync_at TIMESTAMP,

    -- Constraints
    UNIQUE(tenant_id, platform, platform_account_id)
);

CREATE INDEX idx_social_accounts_tenant ON social_accounts(tenant_id);
CREATE INDEX idx_social_accounts_platform ON social_accounts(platform);
CREATE INDEX idx_social_accounts_tenant_platform ON social_accounts(tenant_id, platform);
CREATE INDEX idx_social_accounts_active ON social_accounts(is_active);

-- ============================================================================
-- OAUTH TOKENS (Encrypted Storage)
-- ============================================================================
CREATE TABLE oauth_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    social_account_id UUID NOT NULL REFERENCES social_accounts(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Token data (ENCRYPTED - use application-level encryption)
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',

    -- Token metadata
    scope TEXT,
    issued_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_refreshed_at TIMESTAMP,
    last_used_at TIMESTAMP,

    -- Security
    client_id VARCHAR(255),
    token_version INTEGER DEFAULT 1,
    is_revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP,
    revoked_reason TEXT,

    -- Audit
    created_by_user_id UUID REFERENCES tenant_users(id),
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_oauth_tokens_social_account ON oauth_tokens(social_account_id);
CREATE INDEX idx_oauth_tokens_tenant ON oauth_tokens(tenant_id);
CREATE INDEX idx_oauth_tokens_active ON oauth_tokens(tenant_id, is_revoked) WHERE is_revoked = FALSE;
CREATE INDEX idx_oauth_tokens_expires ON oauth_tokens(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_oauth_tokens_last_used ON oauth_tokens(last_used_at);

-- ============================================================================
-- TOKEN REFRESH HISTORY (Audit Trail)
-- ============================================================================
CREATE TABLE token_refresh_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    oauth_token_id UUID REFERENCES oauth_tokens(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Refresh details
    refreshed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    old_expires_at TIMESTAMP,
    new_expires_at TIMESTAMP,
    refresh_status VARCHAR(50) CHECK (refresh_status IN ('success', 'failed', 'revoked')),
    error_message TEXT
);

CREATE INDEX idx_token_refresh_token ON token_refresh_history(oauth_token_id);
CREATE INDEX idx_token_refresh_tenant_date ON token_refresh_history(tenant_id, refreshed_at);

-- ============================================================================
-- POST HISTORY (Content Audit)
-- ============================================================================
CREATE TABLE post_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    social_account_id UUID NOT NULL REFERENCES social_accounts(id),

    -- Platform
    platform VARCHAR(50) NOT NULL,
    platform_post_id VARCHAR(255),

    -- Content
    caption TEXT,
    image_url TEXT,
    campaign_name VARCHAR(255),
    item_name VARCHAR(255),

    -- Status
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'published', 'failed', 'deleted', 'scheduled')),
    posted_at TIMESTAMP,
    scheduled_for TIMESTAMP,
    error_message TEXT,

    -- Engagement metrics (updated via webhook or API)
    engagement_metrics JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_post_history_tenant ON post_history(tenant_id);
CREATE INDEX idx_post_history_social_account ON post_history(social_account_id);
CREATE INDEX idx_post_history_status ON post_history(status);
CREATE INDEX idx_post_history_posted_date ON post_history(tenant_id, posted_at);
CREATE INDEX idx_post_history_campaign ON post_history(campaign_name);

-- ============================================================================
-- WEBHOOK EVENTS (For token expiration notifications, etc.)
-- ============================================================================
CREATE TABLE webhook_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id),

    -- Event details
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,

    -- Processing
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP,
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_webhook_events_processed ON webhook_events(processed, created_at);
CREATE INDEX idx_webhook_events_tenant ON webhook_events(tenant_id);
CREATE INDEX idx_webhook_events_type ON webhook_events(event_type);

-- ============================================================================
-- OAUTH STATE (CSRF Protection)
-- ============================================================================
CREATE TABLE oauth_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    state_token VARCHAR(255) UNIQUE NOT NULL,
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Metadata
    return_url TEXT,
    ip_address INET,
    user_agent TEXT,

    -- Expiration (states expire after 10 minutes)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP + INTERVAL '10 minutes',
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP
);

CREATE INDEX idx_oauth_state_token ON oauth_state(state_token);
CREATE INDEX idx_oauth_state_tenant ON oauth_state(tenant_id);
CREATE INDEX idx_oauth_state_expires ON oauth_state(expires_at) WHERE used = FALSE;

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Cleanup expired OAuth states (run daily)
CREATE OR REPLACE FUNCTION cleanup_expired_oauth_states()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM oauth_state
    WHERE expires_at < CURRENT_TIMESTAMP
    AND used = TRUE;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS (For convenient queries)
-- ============================================================================

-- Active connections per tenant
CREATE OR REPLACE VIEW tenant_active_connections AS
SELECT
    t.id as tenant_id,
    t.slug,
    t.name,
    COUNT(DISTINCT sa.id) as total_connections,
    COUNT(DISTINCT CASE WHEN sa.platform = 'facebook' THEN sa.id END) as facebook_connections,
    COUNT(DISTINCT CASE WHEN sa.platform = 'instagram' THEN sa.id END) as instagram_connections,
    COUNT(DISTINCT CASE WHEN ot.is_revoked = FALSE THEN ot.id END) as active_tokens
FROM tenants t
LEFT JOIN social_accounts sa ON t.id = sa.tenant_id AND sa.is_active = TRUE
LEFT JOIN oauth_tokens ot ON sa.id = ot.social_account_id
GROUP BY t.id, t.slug, t.name;

-- Tokens expiring soon
CREATE OR REPLACE VIEW tokens_expiring_soon AS
SELECT
    t.slug as tenant_slug,
    sa.platform,
    sa.account_name,
    ot.expires_at,
    EXTRACT(DAY FROM (ot.expires_at - CURRENT_TIMESTAMP)) as days_until_expiration
FROM oauth_tokens ot
JOIN social_accounts sa ON ot.social_account_id = sa.id
JOIN tenants t ON ot.tenant_id = t.id
WHERE ot.is_revoked = FALSE
AND ot.expires_at IS NOT NULL
AND ot.expires_at < CURRENT_TIMESTAMP + INTERVAL '7 days'
ORDER BY ot.expires_at ASC;

-- ============================================================================
-- SAMPLE DATA (for development/testing)
-- ============================================================================

-- Insert sample tenant
INSERT INTO tenants (slug, name, email, status, plan_type) VALUES
('hults_cafe', 'Hults Cafe', 'admin@hultscafe.com', 'active', 'basic'),
('krusti_pizza_and_pasta', 'Krusty Pizza & Pasta', 'admin@krustypizza.com', 'active', 'pro');

-- Insert sample admin users
INSERT INTO tenant_users (tenant_id, email, name, role) VALUES
((SELECT id FROM tenants WHERE slug = 'hults_cafe'), 'admin@hultscafe.com', 'Hults Admin', 'owner'),
((SELECT id FROM tenants WHERE slug = 'krusti_pizza_and_pasta'), 'admin@krustypizza.com', 'Krusty Admin', 'owner');

COMMENT ON TABLE tenants IS 'Restaurants/businesses using the platform';
COMMENT ON TABLE tenant_users IS 'Users who can manage tenant accounts';
COMMENT ON TABLE social_accounts IS 'Connected social media accounts (Facebook pages, Instagram accounts, etc.)';
COMMENT ON TABLE oauth_tokens IS 'Encrypted OAuth tokens for social media API access';
COMMENT ON TABLE post_history IS 'Audit log of all social media posts';
COMMENT ON TABLE webhook_events IS 'Events received from social media platforms';
COMMENT ON TABLE oauth_state IS 'CSRF protection tokens for OAuth flow';

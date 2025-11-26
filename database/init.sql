-- Boloo Database Schema
-- PostgreSQL 15 + PostGIS

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    name VARCHAR(255),
    languages TEXT[] DEFAULT '{"en", "hi"}',
    is_first_timer BOOLEAN DEFAULT TRUE,
    reputation_score INTEGER DEFAULT 0,
    role VARCHAR(50) DEFAULT 'citizen',  -- citizen, moderator, officer, admin
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_role CHECK (role IN ('citizen', 'moderator', 'officer', 'admin'))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Entities table (government offices)
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- district, block, gp, dept
    contact_phone VARCHAR(20),
    contact_email VARCHAR(255),
    escalation_parent_id UUID REFERENCES entities(id),
    coverage_geojson JSONB,  -- GeoJSON polygon for coverage area
    metadata JSONB,  -- Additional info (competencies, etc.)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_entity_type CHECK (type IN ('district', 'block', 'gp', 'dept'))
);

CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_entities_parent ON entities(escalation_parent_id);
CREATE INDEX idx_entities_coverage ON entities USING GIN(coverage_geojson);

-- Taxonomies table (issue types, topics, languages)
CREATE TABLE taxonomies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) NOT NULL,  -- issue, topic, language
    key VARCHAR(100) NOT NULL,
    label_en VARCHAR(255),
    label_hi VARCHAR(255),
    parent_key VARCHAR(100),
    metadata JSONB,  -- Additional info (competent entities, etc.)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_taxonomy UNIQUE(type, key),
    CONSTRAINT valid_taxonomy_type CHECK (type IN ('issue', 'topic', 'language'))
);

CREATE INDEX idx_taxonomies_type ON taxonomies(type);
CREATE INDEX idx_taxonomies_key ON taxonomies(key);

-- Cases table
CREATE TABLE cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    title VARCHAR(500),
    summary TEXT,
    transcript_text TEXT,
    audio_url VARCHAR(1000),
    media_urls TEXT[],
    location_point GEOMETRY(POINT, 4326),  -- GPS coordinates
    location_text VARCHAR(500),  -- Human-readable location
    issue_type VARCHAR(100),
    entity_id UUID REFERENCES entities(id),
    status VARCHAR(50) DEFAULT 'draft',
    priority VARCHAR(20) DEFAULT 'normal',
    sla_due_at TIMESTAMP,
    is_public BOOLEAN DEFAULT FALSE,
    metadata JSONB,  -- Flexible storage for additional data
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_status CHECK (status IN (
        'draft', 'submitted', 'moderation', 'routed',
        'officer_accepted', 'in_progress', 'resolved',
        'verified', 'closed', 'rejected', 'duplicate', 'withdrawn', 'escalated'
    )),
    CONSTRAINT valid_priority CHECK (priority IN ('low', 'normal', 'high', 'urgent'))
);

CREATE INDEX idx_cases_user ON cases(user_id);
CREATE INDEX idx_cases_entity ON cases(entity_id);
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_location ON cases USING GIST(location_point);
CREATE INDEX idx_cases_sla ON cases(sla_due_at) WHERE status IN ('routed', 'officer_accepted', 'in_progress');
CREATE INDEX idx_cases_created ON cases(created_at DESC);
CREATE INDEX idx_cases_transcript_search ON cases USING GIN(to_tsvector('english', transcript_text));
CREATE INDEX idx_cases_public ON cases(is_public) WHERE is_public = TRUE;

-- Case events table (audit log)
CREATE TABLE case_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,  -- submitted, routed, accepted, updated, resolved, escalated, closed, rejected
    actor_id UUID REFERENCES users(id),
    actor_role VARCHAR(50),
    note TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_event_type CHECK (event_type IN (
        'submitted', 'routed', 'accepted', 'updated', 'resolved',
        'escalated', 'closed', 'verified', 'rejected', 'flagged', 'assigned'
    ))
);

CREATE INDEX idx_case_events_case ON case_events(case_id);
CREATE INDEX idx_case_events_type ON case_events(event_type);
CREATE INDEX idx_case_events_created ON case_events(created_at DESC);

-- Community posts table (Phase 2)
CREATE TABLE community_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    title VARCHAR(500),
    summary TEXT,
    transcript_text TEXT,
    audio_url VARCHAR(1000),
    media_urls TEXT[],
    tags TEXT[],
    location_point GEOMETRY(POINT, 4326),
    location_text VARCHAR(500),
    status VARCHAR(50) DEFAULT 'draft',
    views_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_post_status CHECK (status IN ('draft', 'submitted', 'moderation', 'published', 'featured', 'rejected'))
);

CREATE INDEX idx_community_posts_user ON community_posts(user_id);
CREATE INDEX idx_community_posts_status ON community_posts(status);
CREATE INDEX idx_community_posts_location ON community_posts USING GIST(location_point);
CREATE INDEX idx_community_posts_tags ON community_posts USING GIN(tags);

-- Flags table (for moderation)
CREATE TABLE flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_type VARCHAR(50) NOT NULL,  -- case, post
    subject_id UUID NOT NULL,
    reason VARCHAR(100) NOT NULL,  -- duplicate, spam, toxicity, pii_leak
    risk_score FLOAT,
    reviewer_id UUID REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending',
    resolution_note TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    CONSTRAINT valid_subject_type CHECK (subject_type IN ('case', 'post')),
    CONSTRAINT valid_flag_status CHECK (status IN ('pending', 'confirmed', 'dismissed'))
);

CREATE INDEX idx_flags_subject ON flags(subject_type, subject_id);
CREATE INDEX idx_flags_status ON flags(status) WHERE status = 'pending';
CREATE INDEX idx_flags_reviewer ON flags(reviewer_id);

-- Notifications table
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    channel VARCHAR(20) DEFAULT 'push',  -- push, sms, email, voice
    template_id VARCHAR(100),
    payload JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    sent_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_channel CHECK (channel IN ('push', 'sms', 'email', 'voice')),
    CONSTRAINT valid_notification_status CHECK (status IN ('pending', 'sent', 'failed'))
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_status ON notifications(status) WHERE status = 'pending';
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);

-- OTP table (for authentication)
CREATE TABLE otps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    otp_code VARCHAR(6) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_otps_email ON otps(email);
CREATE INDEX idx_otps_expires ON otps(expires_at);

-- Sessions table (for JWT management)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    user_agent TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(token_hash);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);

-- Analytics/Metrics table (for dashboard)
CREATE TABLE metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type VARCHAR(100) NOT NULL,  -- case_submitted, case_resolved, sla_breached, etc.
    entity_id UUID REFERENCES entities(id),
    user_id UUID REFERENCES users(id),
    value JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    date DATE DEFAULT CURRENT_DATE
);

CREATE INDEX idx_metrics_type ON metrics(metric_type);
CREATE INDEX idx_metrics_entity ON metrics(entity_id);
CREATE INDEX idx_metrics_date ON metrics(date);
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp DESC);

-- Audit log table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    changes JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);

-- Functions for updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_entities_updated_at BEFORE UPDATE ON entities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cases_updated_at BEFORE UPDATE ON cases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_community_posts_updated_at BEFORE UPDATE ON community_posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default admin user
INSERT INTO users (email, name, role, is_first_timer) VALUES
('admin@boloo.app', 'System Admin', 'admin', FALSE);

-- Insert default taxonomies for languages
INSERT INTO taxonomies (type, key, label_en, label_hi) VALUES
('language', 'en', 'English', 'अंग्रेज़ी'),
('language', 'hi', 'Hindi', 'हिंदी');

COMMIT;

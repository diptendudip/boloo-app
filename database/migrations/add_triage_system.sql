-- Migration: Add 3-way triage system
-- Date: 2025-10-26

-- Add case kind enum
CREATE TYPE case_kind AS ENUM ('grievance', 'community_story', 'personal');

-- Add triage intent enum
CREATE TYPE triage_intent AS ENUM ('grievance', 'community', 'personal', 'uncertain');

-- Alter cases table
ALTER TABLE cases ADD COLUMN IF NOT EXISTS kind case_kind DEFAULT 'grievance';
ALTER TABLE cases ADD COLUMN IF NOT EXISTS triage_intent triage_intent;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS routing_confidence FLOAT DEFAULT 0.0;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS raw_audio_url TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS raw_transcript TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS hindi_transcript TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS formal_summary TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS can_convert_to_grievance BOOLEAN DEFAULT FALSE;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS reminder_at TIMESTAMP;

-- Add slot extraction fields
ALTER TABLE cases ADD COLUMN IF NOT EXISTS location_text TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS when_started TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS scope_affected TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS prior_contact TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS rights_consent BOOLEAN DEFAULT FALSE;

-- Create community_posts table (separate from cases)
CREATE TABLE IF NOT EXISTS community_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    citizen_id UUID NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    topic VARCHAR(50), -- song/medicine/tradition/news
    location_text TEXT,
    location GEOMETRY(POINT, 4326),
    media_urls TEXT[],
    raw_audio_url TEXT,
    transcript TEXT,
    rights_consent BOOLEAN DEFAULT FALSE,
    is_approved BOOLEAN DEFAULT FALSE,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_community_posts_location ON community_posts USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_community_posts_topic ON community_posts(topic);

-- Add entity versioning
ALTER TABLE entities ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;
ALTER TABLE entities ADD COLUMN IF NOT EXISTS last_verified_at TIMESTAMP;
ALTER TABLE entities ADD COLUMN IF NOT EXISTS suggested_updates JSONB;
ALTER TABLE entities ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES users(id);

-- Create consents table
CREATE TABLE IF NOT EXISTS consents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    case_id UUID REFERENCES cases(id),
    post_id UUID REFERENCES community_posts(id),
    grievance_public BOOLEAN DEFAULT FALSE,
    community_public BOOLEAN DEFAULT TRUE,
    personal_private BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add SLA and escalation tracking
CREATE TABLE IF NOT EXISTS case_sla_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id),
    responsible_entity_id UUID REFERENCES entities(id),
    sla_hours INTEGER NOT NULL, -- Expected response time
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP,
    escalated_at TIMESTAMP,
    escalation_level INTEGER DEFAULT 0, -- 0=initial, 1=BDO, 2=District, etc.
    who_has_ball VARCHAR(50) NOT NULL, -- 'citizen', 'moderator', 'officer', 'system'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sla_case ON case_sla_tracking(case_id);
CREATE INDEX IF NOT EXISTS idx_sla_pending ON case_sla_tracking(responded_at) WHERE responded_at IS NULL;

-- Add user locale preferences
ALTER TABLE users ADD COLUMN IF NOT EXISTS locale_preference VARCHAR(10) DEFAULT 'hi-IN';
ALTER TABLE users ADD COLUMN IF NOT EXISTS village_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_contact_method VARCHAR(20) DEFAULT 'sms'; -- sms/whatsapp/call

COMMIT;

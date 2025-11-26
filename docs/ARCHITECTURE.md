


# Boloo Architecture

## System Overview

Boloo is a microservices-based citizen reporting platform with voice-first interaction, automatic routing, and SLA tracking.

## Components

### 1. Mobile App (React Native)
- **Purpose**: Citizen-facing voice reporting interface
- **Platform**: Android 8.0+ (API 26+)
- **Key Features**:
  - Voice recording and upload
  - Offline queue with background sync
  - GPS location capture
  - Push notifications
  - Multi-language UI (Hindi/English)

### 2. Backend API (FastAPI)
- **Purpose**: Core business logic and data management
- **Key Responsibilities**:
  - Authentication (Email OTP)
  - Case CRUD operations
  - Voice processing pipeline
  - Routing logic
  - Notification management
  - File upload handling

### 3. Background Workers (Celery)
- **Purpose**: Async job processing
- **Jobs**:
  - SLA escalation (hourly)
  - Duplicate detection
  - Notification dispatch
  - Audio transcription

### 4. Web Consoles (Next.js)
- **Admin Console**: Manage entities, taxonomies, view analytics
- **Moderator Console**: Triage queue, approve/flag submissions
- **Officer Console**: Case inbox, updates, resolution

### 5. Database (PostgreSQL + PostGIS)
- **Purpose**: Primary data store
- **Extensions**: PostGIS for geospatial queries
- **Scale**: Designed for 1M+ users

### 6. Object Storage (MinIO/S3)
- **Purpose**: Store audio recordings and media files
- **Features**: Presigned URLs, lifecycle policies

### 7. Cache & Queue (Redis)
- **Purpose**: Session cache, job queue, rate limiting

## Data Model

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    name VARCHAR(255),
    languages TEXT[] DEFAULT '{"en", "hi"}',
    is_first_timer BOOLEAN DEFAULT TRUE,
    reputation_score INTEGER DEFAULT 0,
    role VARCHAR(50) DEFAULT 'citizen',

    -- AI Coach Training State (New in AI Coach Onboarding)
    training_reports_count INTEGER DEFAULT 0,
    training_completed BOOLEAN DEFAULT FALSE,
    training_mode_enabled BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Cases Table
```sql
CREATE TABLE cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    title VARCHAR(500),
    summary TEXT,
    transcript_text TEXT,
    audio_url VARCHAR(1000),
    media_urls TEXT[],
    location_point GEOMETRY(POINT, 4326),
    location_text VARCHAR(500),
    issue_type VARCHAR(100),
    entity_id UUID REFERENCES entities(id),
    status VARCHAR(50) DEFAULT 'draft',
    priority VARCHAR(20) DEFAULT 'normal',
    sla_due_at TIMESTAMP,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cases_location ON cases USING GIST(location_point);
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_sla ON cases(sla_due_at) WHERE status IN ('routed', 'officer_accepted', 'in_progress');
```

### CaseEvents Table
```sql
CREATE TABLE case_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id),
    event_type VARCHAR(50) NOT NULL,
    actor_id UUID REFERENCES users(id),
    actor_role VARCHAR(50),
    note TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_case_events_case ON case_events(case_id);
```

### Conversations Table (AI Coach Onboarding)
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    case_id UUID REFERENCES cases(id),
    turn_count INTEGER DEFAULT 1,
    is_complete BOOLEAN DEFAULT FALSE,
    completeness_score FLOAT DEFAULT 0.0,

    -- Collected information tracking
    collected_fields TEXT[] DEFAULT '{}',
    missing_fields JSONB DEFAULT '[]',

    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_case ON conversations(case_id);
```

### ConversationTurns Table (AI Coach Onboarding)
```sql
CREATE TABLE conversation_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) NOT NULL,
    turn_number INTEGER NOT NULL,

    -- Audio and transcription
    audio_url VARCHAR(1000),
    transcript_text TEXT NOT NULL,
    language_detected VARCHAR(10),

    -- AI response
    ai_prompt TEXT,
    ai_response TEXT,
    ai_question_asked TEXT,

    -- Analysis
    intent VARCHAR(50),
    confidence FLOAT,
    fields_extracted JSONB,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(conversation_id, turn_number)
);

CREATE INDEX idx_conversation_turns_conversation ON conversation_turns(conversation_id);
```

### Media Table (Photo Upload System)
```sql
CREATE TABLE media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) NOT NULL,
    user_id UUID REFERENCES users(id) NOT NULL,

    -- Storage details
    storage_url VARCHAR(1000) NOT NULL,
    storage_key VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,  -- image/jpeg, image/png, etc.
    file_size INTEGER NOT NULL,  -- bytes

    -- Metadata
    width INTEGER,
    height INTEGER,
    caption TEXT,

    -- Moderation
    is_approved BOOLEAN DEFAULT FALSE,
    moderation_status VARCHAR(20) DEFAULT 'pending',
    moderation_notes TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP
);

CREATE INDEX idx_media_case ON media(case_id);
CREATE INDEX idx_media_user ON media(user_id);
CREATE INDEX idx_media_moderation ON media(moderation_status) WHERE moderation_status = 'pending';
```

### Entities Table
```sql
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    contact_phone VARCHAR(20),
    contact_email VARCHAR(255),
    escalation_parent_id UUID REFERENCES entities(id),
    coverage_geojson JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_entities_type ON entities(type);
```

### Taxonomies Table
```sql
CREATE TABLE taxonomies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) NOT NULL,
    key VARCHAR(100) NOT NULL,
    label_en VARCHAR(255),
    label_hi VARCHAR(255),
    parent_key VARCHAR(100),
    metadata JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(type, key)
);
```

### Notifications Table
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    channel VARCHAR(20) DEFAULT 'push',
    template_id VARCHAR(100),
    payload JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_status ON notifications(status) WHERE status = 'pending';
```

### Flags Table
```sql
CREATE TABLE flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_type VARCHAR(50),
    subject_id UUID,
    reason VARCHAR(100),
    risk_score FLOAT,
    reviewer_id UUID REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Case State Machine

```
Draft
  ↓
Submitted
  ↓
Moderation (if first-timer or flagged)
  ↓
Routed → Officer-Accepted → In-Progress → Resolved → Verified → Closed
  ↓          ↓ (72h)           ↓ (72h)       ↓
Escalated ←──┴─────────────────┘            ↓
                                           Rejected/Duplicate/Withdrawn
```

## Routing Logic

```python
def route_case(location_point, issue_type):
    # 1. Find matching entities by coverage area
    entities = db.query(Entity).filter(
        Entity.type.in_(['gp', 'district', 'dept']),
        ST_Contains(Entity.coverage_geojson, location_point)
    ).all()

    # 2. Filter by issue_type competency
    # (based on taxonomy metadata)

    # 3. Select most specific entity (GP > Block > District)

    # 4. Return entity_id
    return entity_id
```

## SLA Escalation

```python
@celery.task
def escalate_overdue_cases():
    overdue = db.query(Case).filter(
        Case.status.in_(['routed', 'officer_accepted', 'in_progress']),
        Case.sla_due_at < datetime.now()
    ).all()

    for case in overdue:
        # 1. Get escalation parent
        parent_entity = case.entity.escalation_parent

        # 2. Reassign case
        case.entity_id = parent_entity.id
        case.sla_due_at = datetime.now() + timedelta(hours=72)

        # 3. Create event
        CaseEvent(
            case_id=case.id,
            event_type='escalated',
            note=f'Auto-escalated to {parent_entity.name}'
        )

        # 4. Notify all parties
        send_notification(case.user_id, 'case_escalated')
        send_notification(parent_entity.contact_email, 'case_assigned')
```

## AI Processing Pipeline

### Voice Intake Flow (Dual-Mode: Training vs Simple)

#### Mode Selection
```python
def determine_mode(user):
    """Determine if user should be in training mode"""
    if not user.training_mode_enabled:
        return "simple"

    if user.training_completed:
        return "simple"

    if user.training_reports_count < 5:
        return "training"

    # Auto-graduate after 5 reports
    user.training_completed = True
    return "graduation"
```

#### Simple Mode Flow (Post-Training, Experienced Users)
```
1. User records voice (one-shot)
   ↓
2. Upload audio to MinIO
   ↓
3. Azure Speech Services → Transcription
   ↓
4. Azure OpenAI (GPT-4o-mini) → Extract slots:
   - location_text
   - issue_type
   - contact_phone
   - short_description
   ↓
5. Resolve routing (geo + issue_type)
   ↓
6. Azure OpenAI → Generate summary (2-3 lines)
   ↓
7. Create Case record
   ↓
8. Queue moderation check
   ↓
9. Send notification to citizen

Cost: ~$0.01 per report
```

#### Training Mode Flow (First 5 Reports, AI Coach Active)
```
1. User records voice (Turn 1)
   ↓
2. Upload audio to MinIO
   ↓
3. Azure Speech Services → Transcription
   ↓
4. Azure OpenAI (GPT-4o-mini) → Analyze completeness:
   - Extract: location, issue_type, description, duration, contact
   - Identify CRITICAL missing fields
   - Generate conversational follow-up question (max 2 questions)
   ↓
5. IF complete (all critical fields present):
   → Create Case record
   → Increment training_reports_count
   → Show success celebration
   ELSE:
   → Store conversation_turn
   → Ask follow-up question in Hindi/English
   → Wait for Turn 2/3
   ↓
6. Turn 2/3: Repeat steps 1-5 with conversation context
   ↓
7. After completion:
   → Resolve routing (geo + issue_type)
   → Generate summary
   → Create Case record
   → Increment training_reports_count
   → If count >= 5: Auto-graduate, show celebration
   ↓
8. Queue moderation check
   ↓
9. Send notification to citizen

Cost: ~$0.045 per training conversation (3 turns avg)
Max turns: 3 (initial + 2 follow-ups)
```

### Completeness Analysis (AI Coach)

```python
def analyze_completeness(transcript: str, intent: str, user_location: Optional[str]) -> dict:
    """
    Analyze what critical information is missing from transcript.
    Uses Azure OpenAI GPT-4o-mini for intelligent analysis.

    Returns only HIGH importance missing fields to maintain minimalist UX.
    """

    if intent == "grievance":
        required_fields = {
            "location": "critical",
            "issue_type": "critical",
            "description": "critical",
            "duration": "high",
            "contact": "medium"  # Skip medium/low for minimal UX
        }

    # Use GPT-4o-mini to extract fields from transcript
    extracted = extract_fields_from_transcript(transcript)

    # Determine missing critical fields
    missing = []
    for field, importance in required_fields.items():
        if importance == "critical" and field not in extracted:
            missing.append({
                "field": field,
                "importance": importance,
                "prompt_hi": get_field_question_hindi(field),
                "prompt_en": get_field_question_english(field)
            })

    # Rule: Maximum 2 follow-up questions
    missing = missing[:2]

    return {
        "collected_fields": list(extracted.keys()),
        "missing_fields": missing,
        "completeness_score": len(extracted) / len(required_fields),
        "is_complete": len(missing) == 0
    }
```

### Duplicate Detection

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def detect_duplicates(case):
    # 1. Generate embedding
    embedding = model.encode(case.summary)

    # 2. Find similar cases (cosine similarity > 0.85)
    similar = db.query(Case).filter(
        Case.status != 'closed',
        Case.created_at > datetime.now() - timedelta(days=30)
    ).all()

    # 3. Calculate similarity
    for candidate in similar:
        similarity = cosine_similarity(embedding, candidate.embedding)
        if similarity > 0.85:
            # Flag as potential duplicate
            Flag.create(
                subject_type='case',
                subject_id=case.id,
                reason='duplicate',
                risk_score=similarity
            )
```

## Feed System (Community Stories)

### Feed Architecture

**Purpose**: RSS-style feed showing approved community stories with photos

**Feed Types**:
1. **Community Feed** - All approved public stories from user's district
2. **My Reports** - User's own submitted cases with status updates
3. **Local Feed** - Stories within 5km radius of user's location

### Feed API

```python
@router.get("/v1/feed/{feed_type}")
async def get_feed(
    feed_type: str,  # "community", "my_reports", "local"
    user_id: UUID,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    limit: int = 20,
    offset: int = 0
):
    """
    Get feed stories with photos and engagement metrics

    Returns:
        stories: [{
            case_id, title, summary, photos[],
            location_text, created_at, status,
            likes_count, comments_count
        }]
    """

    query = db.query(Case).filter(
        Case.is_public == True,
        Case.status.in_(['resolved', 'in_progress', 'routed'])
    )

    if feed_type == "community":
        # User's district stories
        user_district = get_user_district(user_id)
        query = query.join(Entity).filter(Entity.id == user_district.id)

    elif feed_type == "local":
        # Within 5km radius
        if not lat or not lon:
            raise ValueError("lat/lon required for local feed")

        user_point = f"POINT({lon} {lat})"
        query = query.filter(
            ST_DWithin(Case.location_point, user_point, 5000)  # 5km
        )

    elif feed_type == "my_reports":
        # User's own cases
        query = query.filter(Case.user_id == user_id)

    # Join with media for photos
    stories = query.outerjoin(Media).order_by(
        Case.created_at.desc()
    ).limit(limit).offset(offset).all()

    return format_feed_response(stories)
```

### Feed UI Design (Minimalist RSS-Style)

```
┌─────────────────────────────────────┐
│  📱 Community Feed                  │
├─────────────────────────────────────┤
│                                     │
│  [Photo Grid - 1-3 photos]         │
│  📍 Raipur, Sector 5                │
│  🏗️ Road Repair Completed          │
│  "पोथोल भरे गए, सड़क ठीक हो गई।"  │
│  👍 45    💬 12    🕐 2h ago        │
│                                     │
├─────────────────────────────────────┤
│                                     │
│  [Photo Grid - 1-3 photos]         │
│  📍 Raipur, Gandhi Chowk            │
│  💡 Street Lights Fixed             │
│  "अब रात में रोशनी है, सुरक्षित..."│
│  👍 23    💬 5     🕐 5h ago        │
│                                     │
└─────────────────────────────────────┘
```

### Photo Upload & Storage

**Storage Backend**: MinIO (S3-compatible object storage)

**Configuration** (`.env`):
```bash
# MinIO Configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=boloo-media
MINIO_USE_SSL=false
```

**Upload Flow**:
```
1. User selects photos (max 3)
   ↓
2. Mobile app validates:
   - File type (JPEG, PNG)
   - File size (max 5MB each)
   - Image dimensions (min 300px)
   ↓
3. Compress images (client-side)
   ↓
4. Upload to backend → POST /v1/media/upload
   ↓
5. Backend stores in MinIO
   ↓
6. Create media record with case_id
   ↓
7. Queue for moderation (if needed)
   ↓
8. Return presigned URLs for display
```

**Media Service** (`app/services/media_service.py`):
```python
class MediaService:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL
        )

    async def upload_photo(
        self,
        file: UploadFile,
        case_id: UUID,
        user_id: UUID
    ) -> Media:
        """Upload photo to MinIO and create media record"""

        # Validate file
        if file.size > 5 * 1024 * 1024:  # 5MB
            raise ValueError("File too large")

        # Generate unique key
        file_ext = file.filename.split('.')[-1]
        storage_key = f"cases/{case_id}/{uuid4()}.{file_ext}"

        # Upload to MinIO
        self.client.put_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=storage_key,
            data=file.file,
            length=file.size,
            content_type=file.content_type
        )

        # Generate presigned URL (7 days)
        storage_url = self.client.presigned_get_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=storage_key,
            expires=timedelta(days=7)
        )

        # Create media record
        media = Media.create(
            case_id=case_id,
            user_id=user_id,
            storage_url=storage_url,
            storage_key=storage_key,
            file_type=file.content_type,
            file_size=file.size
        )

        return media
```

## Security

### Authentication Flow (Email OTP)

```
1. User enters email → POST /auth/otp/request
   ↓
2. Backend generates 6-digit OTP
   ↓
3. Store in Redis (5 min expiry)
   ↓
4. Send email to diptendudip@gmail.com (for Phase 1)
   ↓
5. User enters OTP → POST /auth/otp/verify
   ↓
6. Validate OTP, create JWT token
   ↓
7. Return token + user profile
```

### Authorization

- **Citizen**: Can create cases, view own cases
- **Moderator**: Can view moderation queue, approve/flag/edit
- **Officer**: Can view assigned cases, update status
- **Admin**: Full access to entities, taxonomies, analytics

### PII Masking

```python
def mask_pii(case, viewer_role):
    if viewer_role not in ['moderator', 'officer', 'admin']:
        # Public view
        case.user.phone = None
        case.location_point = approximate_location(case.location_point, 1000)  # 1km radius
    return case
```

## Scalability

### Database
- **Partitioning**: Cases table partitioned by created_at (monthly)
- **Indexes**: Optimized for common queries (status, location, SLA)
- **Connection Pooling**: Max 100 connections

### API
- **Rate Limiting**: 100 req/min per user
- **Caching**: Redis for frequent queries (entities, taxonomies)
- **Async Processing**: Celery for heavy tasks

### Storage
- **Media Files**: CDN for audio playback
- **Lifecycle Policies**: Archive old recordings after 2 years

## Monitoring & Observability

### Metrics
- Case submission rate
- SLA compliance %
- API response time (p50, p95, p99)
- Worker job latency
- Azure API usage and cost

### Alerts
- Azure cost > $16 (80% threshold) → Email
- Azure cost > $20 (100% threshold) → Email + Block
- SLA breach rate > 20% → Email
- Error rate > 5% → Email

### Logging
- Structured JSON logs
- Request ID tracing
- Audit log for sensitive operations

## Deployment

### Development
```bash
docker-compose up
```

### Production (Azure)
- **App Service**: Backend API + Workers
- **Database**: Azure Database for PostgreSQL (Flexible Server)
- **Storage**: Azure Blob Storage
- **Cache**: Azure Cache for Redis
- **Monitoring**: Azure Monitor + Application Insights

## Cost Estimates (Monthly)

- Azure Speech Services: $20 (hard limit)
- Claude API: Covered by user's subscription
- Database (10GB): ~$25
- App Service (B1): ~$13
- Storage (100GB): ~$3
- Redis: ~$10

**Total**: ~$71/month (excluding Claude API)

## Moderation System

### Moderation Queue

**Purpose**: Review first-timer reports and photo uploads before publishing

**Moderation Types**:
1. **Case Moderation** - First-time users, flagged content
2. **Photo Moderation** - All photos before appearing in feed
3. **Auto-Moderation** - GPT-4o-mini pre-screening for inappropriate content

**Moderation Console Flow**:
```
1. Moderator logs into web console
   ↓
2. View queue: pending cases and photos
   ↓
3. For each item, moderator can:
   - ✅ Approve (publish to feed)
   - ❌ Reject (notify user, provide reason)
   - ✏️ Edit (fix typos, improve summary)
   - 🚩 Flag (escalate to admin)
   ↓
4. Actions logged in case_events
   ↓
5. User notified of moderation decision
```

**Future Enhancement**: Use open-source CMS (after app trial)
- Options to evaluate: Strapi, Directus, Payload CMS
- Custom moderation workflows
- Bulk actions and shortcuts
- AI-assisted moderation recommendations

## AI Coach Training Graduation

### Graduation Celebration (After 5th Report)

**Trigger**: `user.training_reports_count >= 5`

**UX Flow**:
```
┌─────────────────────────────────────┐
│  🎉 बधाई हो! Congratulations!      │
│                                     │
│  आपने प्रशिक्षण पूरा कर लिया है!   │
│  You've completed AI Coach training!│
│                                     │
│  From now on:                       │
│  ✓ Faster reporting (one recording)│
│  ✓ No follow-up questions          │
│  ✓ Instant submission              │
│                                     │
│  You can re-enable training mode    │
│  anytime from Settings > AI Coach   │
│                                     │
│  [Continue]                         │
└─────────────────────────────────────┘
```

**Backend Logic**:
```python
@router.post("/v1/conversations/complete")
async def complete_conversation(conversation_id: UUID, user_id: UUID):
    """Mark conversation complete and check for graduation"""

    conversation = db.query(Conversation).get(conversation_id)
    conversation.is_complete = True
    conversation.completed_at = datetime.now()

    user = db.query(User).get(user_id)
    user.training_reports_count += 1

    # Check for graduation
    if user.training_reports_count >= 5 and not user.training_completed:
        user.training_completed = True
        return {
            "success": True,
            "graduated": True,
            "message": "Training complete! Switching to simple mode."
        }

    return {
        "success": True,
        "graduated": False,
        "training_progress": f"{user.training_reports_count}/5"
    }
```

## Future Enhancements

- Horizontal scaling with load balancer
- Read replicas for analytics queries
- Elasticsearch for full-text search
- Real-time updates via WebSockets
- Mobile app for Officers
- WhatsApp integration
- Video evidence upload (Phase 3)
- Offline photo capture with sync (Phase 3)
- Advanced feed filters (by issue type, status, date range)
- Feed engagement analytics dashboard

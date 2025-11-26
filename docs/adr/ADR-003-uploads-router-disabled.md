# ADR-003: Uploads Router Temporarily Disabled

**Date**: 2025-11-12
**Status**: Accepted
**Decision Makers**: Development Team
**Technical Story**: Missing CaseAttachment model causing backend crashes

## Context

The uploads router (`app/routers/uploads.py`) was causing the FastAPI backend to crash on startup due to a missing `CaseAttachment` model reference. The error occurred when attempting to import the router in `app/main.py`.

### Error Details
```python
ImportError: cannot import name 'CaseAttachment' from 'app.models'
File: /backend/app/routers/uploads.py:15
```

### Investigation Findings

1. **uploads.py imports CaseAttachment** - The router expects a SQLAlchemy model that doesn't exist
2. **No migration exists** - No Alembic migration file creates the `case_attachments` table
3. **Model not in models/__init__.py** - The model was never implemented
4. **Feature partially implemented** - API routes exist but database schema is missing

## Decision

**Temporarily disable the uploads router** by commenting it out in `main.py` until a decision is made to either:
- **Option A**: Fully implement the feature with proper model and migrations
- **Option B**: Remove the feature entirely if not needed

### Code Change
```python
# main.py line 14
from app.routers import auth, cases, entities, taxonomies, admin, monitoring, monitoring_v2, triage, transcription, next_steps, users, chat, feed  # , uploads  # TODO: Fix CaseAttachment model

# main.py line 129
# app.include_router(uploads.router, prefix="/v1/uploads", tags=["Uploads"])  # TODO: Fix CaseAttachment model
```

## Consequences

### Positive
- ✅ Backend starts successfully without crashes
- ✅ All other features remain functional
- ✅ Clear TODO comments indicate temporary nature
- ✅ Easy to re-enable once model is implemented

### Negative
- ❌ File upload functionality unavailable to users
- ❌ Media attachments for cases not working through this router
- ❌ API documentation shows incomplete feature set

### Neutral
- ℹ️ Media upload may be handled through other means (e.g., direct MinIO integration)
- ℹ️ Cases table already has `media_urls` field suggesting alternative implementation

## Implementation Requirements

To properly implement this feature, the following is needed:

### 1. Create CaseAttachment Model
```python
# app/models/attachment.py
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime

class CaseAttachment(Base):
    __tablename__ = "case_attachments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    file_url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # image, audio, video, document
    file_size = Column(Integer, nullable=False)  # bytes
    mime_type = Column(String, nullable=False)
    original_filename = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    case = relationship("Case", back_populates="attachments")
```

### 2. Create Alembic Migration
```bash
alembic revision -m "Add case_attachments table"
# Then edit the migration file to create the table
```

### 3. Update Case Model
```python
# Add to Case model
attachments = relationship("CaseAttachment", back_populates="case")
```

### 4. Re-enable Router
```python
# Uncomment in main.py
from app.routers import uploads
app.include_router(uploads.router, prefix="/v1/uploads", tags=["Uploads"])
```

## Alternative Solutions Considered

### 1. Use media_urls Field Only
- Cases already have `media_urls: List[str]` field
- Could store URLs directly without separate attachment table
- Simpler but less metadata (no file size, mime type, etc.)

### 2. Direct MinIO Integration
- Upload files directly to MinIO from mobile app
- Backend only stores URLs in `media_urls`
- Reduces backend complexity
- Less control over upload validation

### 3. Inline Attachments in Case Creation
- Accept file uploads during case creation
- Store in MinIO and populate `media_urls`
- No separate attachments table needed
- Implemented in `cases` router instead

## Current Workaround

Users can still attach media to cases through:
1. **Case creation endpoint** - Accepts media during initial report
2. **Direct MinIO upload** - Mobile app can upload directly and pass URLs
3. **media_urls field** - Cases support multiple media URLs without attachment model

## Monitoring

Track the following to inform final decision:
- User requests for file upload functionality
- Prevalence of media in case submissions
- Alternative upload method usage
- Performance of direct MinIO integration

## References

- [FastAPI File Uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- [SQLAlchemy Relationships](https://docs.sqlalchemy.org/en/14/orm/relationships.html)
- [MinIO Python SDK](https://docs.min.io/docs/python-client-quickstart-guide.html)

## Next Steps

**Immediate** (Done):
- ✅ Comment out uploads router
- ✅ Add TODO comments
- ✅ Document decision in ADR

**Short-term** (1-2 weeks):
- [ ] Decide: Implement full feature vs remove entirely
- [ ] Test existing media upload through case creation
- [ ] Evaluate user needs for separate attachment management

**Long-term** (if implementing):
- [ ] Create CaseAttachment model
- [ ] Write migration
- [ ] Add comprehensive tests
- [ ] Update API documentation
- [ ] Security review for file uploads

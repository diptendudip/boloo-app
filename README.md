# Boloo - Conversational AI Citizen Reporting Platform

A voice-first mobile application for citizens to report grievances and share community content, with automated routing, SLA tracking, and multi-role web consoles.

## Overview

Boloo enables citizens to:
- Report grievances via voice in Hindi or English
- Get automatic routing to the correct government office
- Track case status with 72-hour SLA and escalations
- View masked public feed of reports

Government officials can:
- Moderate first-time submissions
- Accept and resolve cases
- Track SLA compliance
- View analytics and metrics

## Architecture

```
boloo-app/
├── backend/          # FastAPI REST API + background workers
├── mobile/           # React Native Android app
├── web/              # Next.js admin/moderator/officer consoles
├── database/         # PostgreSQL schema, migrations, seeds
├── docker/           # Docker configuration
├── docs/             # Documentation
└── scripts/          # Utility scripts
```

## Technology Stack

### Mobile App
- React Native (Expo)
- SQLite for offline storage
- expo-av for voice recording
- expo-notifications for push notifications

### Backend
- FastAPI (Python 3.11)
- PostgreSQL 15 + PostGIS
- SQLAlchemy ORM
- Celery + Redis (background jobs)
- Alembic (migrations)

### Web Consoles
- Next.js 14 + TypeScript
- TailwindCSS
- React Query

### AI Services
- Azure Speech Services (ASR/TTS) - $20/month budget with alerts
- Claude API (NLU and intake processing)
- Sentence transformers (duplicate detection)

### Infrastructure
- Docker Compose (development)
- PostgreSQL + PostGIS
- Redis
- MinIO (object storage)

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- Android Studio (for mobile development)

### Development Setup

1. **Clone and setup:**
```bash
cd boloo-app
cp .env.example .env
# Edit .env with your configuration
```

2. **Start backend services:**
```bash
docker-compose up -d postgres redis minio
cd backend
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed_data
uvicorn app.main:app --reload
```

3. **Start web console:**
```bash
cd web
npm install
npm run dev
```

4. **Start mobile app:**
```bash
cd mobile
npm install
npx expo start
```

### Building Android APK

```bash
cd mobile
eas build --platform android --profile production
```

## Key Features

### Phase 1 - Grievance Reporting
- [x] Voice-first intake (Hindi/English)
- [x] Email OTP authentication
- [x] Offline support with background sync
- [x] Auto-routing based on location + issue type
- [x] 72h SLA with automatic escalation
- [x] Moderator queue for first-time users
- [x] Officer inbox and case management
- [x] Admin dashboard with metrics
- [x] PII masking in public views
- [x] Duplicate detection
- [x] Push notifications
- [x] Audit logs

### Future Phases
- [ ] Community content posts
- [ ] SMS/Voice notifications
- [ ] Mobile app for Moderator/Officer
- [ ] Advanced analytics
- [ ] Multi-language expansion

## Data Model

### Core Entities
- **Users**: Citizens, Moderators, Officers, Admins
- **Cases**: Grievance reports with status tracking
- **CaseEvents**: Audit log of case state changes
- **Entities**: Government offices (Districts, GPs, Departments)
- **Taxonomies**: Issue categories, languages
- **Notifications**: Multi-channel notification queue

See [ARCHITECTURE.md](./docs/ARCHITECTURE.md) for detailed schema.

## API Endpoints

### Authentication
- `POST /v1/auth/otp/request` - Request OTP
- `POST /v1/auth/otp/verify` - Verify OTP and login

### Cases
- `POST /v1/cases` - Create case from voice
- `GET /v1/cases/:id` - Get case details
- `PATCH /v1/cases/:id` - Update case status
- `GET /v1/cases` - List cases (filtered)

### Admin
- `POST /v1/admin/entities` - Manage government offices
- `POST /v1/admin/taxonomies` - Manage issue categories
- `POST /v1/admin/bulk-import` - CSV/Google Sheets import

See full [API Documentation](./docs/API.md)

## Security & Privacy

- Email OTP authentication only (Phase 1)
- Role-based access control
- PII masking in public views (phone, exact location)
- Audit logs for all edits
- Rate limiting
- HTTPS only
- Secure storage of media files

## Google Play Store Compliance

- Privacy Policy included
- Data deletion capability
- Permissions requested with justification
- Target SDK: Android 13 (API 33)
- Min SDK: Android 8.0 (API 26)

## Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Mobile Tests
```bash
cd mobile
npm test
```

### E2E Tests
```bash
npm run test:e2e
```

## Deployment

See [DEPLOYMENT.md](./docs/DEPLOYMENT.md) for production deployment instructions.

## Cost Monitoring

Azure Speech Services is configured with:
- $20/month budget limit
- Email alerts to diptendudip@gmail.com at 80% and 100% thresholds
- Auto-block at $20 to prevent overages

## License

Proprietary - All rights reserved

## Support

For issues and questions, contact: diptendudip@gmail.com

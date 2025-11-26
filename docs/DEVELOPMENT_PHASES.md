# Boloo Development Phases

## Overview
This document outlines the phased approach to building the Boloo Conversational AI Reporting platform.

**Total Estimated Time**: 30-43 hours of development

---

## Phase 1: MVP (Minimum Viable Product) - 6-8 hours

### Objectives
- Get core grievance reporting flow working
- Test locally with all components running
- Verify voice recording and basic AI processing

### Backend Components
- [x] Database schema and migrations
- [x] Seed data generation (entities + taxonomies)
- [ ] SQLAlchemy models (Users, Cases, Entities, Taxonomies, OTPs)
- [ ] Email OTP authentication (login only)
- [ ] Core API endpoints:
  - `POST /v1/auth/otp/request`
  - `POST /v1/auth/otp/verify`
  - `POST /v1/cases` (create case from voice)
  - `GET /v1/cases/:id`
  - `GET /v1/cases` (list with filters)
  - `GET /v1/taxonomies`
  - `GET /v1/entities`
- [ ] Basic voice file upload to MinIO
- [ ] Claude API integration for intake processing (extract slots)
- [ ] Basic case routing logic
- [ ] **Daemon mode server** (runs independently of terminal)
- [ ] **System monitoring dashboard API** (endpoint health checks)

### Android App Components
- [x] Expo React Native project setup
- [x] Basic UI with Hindi/English toggle
- [x] Voice recording (expo-av)
- [x] Email OTP login screen
- [ ] Case submission form
- [ ] My Cases list view
- [ ] **Auto-restart capability via script**

### Web Admin Console
- [ ] Next.js project setup
- [ ] Authentication (same OTP system)
- [ ] **Navigation panel with links to all admin pages**
- [ ] **Operational Monitoring Dashboard**:
  - API endpoint health status (all endpoints)
  - Backend server status
  - Database connection status
  - Redis connection status
  - MinIO storage status
  - Azure Speech API status
  - Claude API status
  - Auto-refresh every 60 seconds
- [ ] Cases list view (all cases)
- [ ] Case detail view
- [ ] Basic metrics dashboard:
  - Total cases count
  - Cases by status
  - Cases by issue type
  - Recent activity
- [ ] Entity management (view list, basic CRUD)
- [ ] Taxonomy management (view list)

### Infrastructure
- [x] Docker Compose configuration
- [ ] **One-line restart script** for all services:
  - Backend API server (daemon mode)
  - Web admin server
  - Android development server
  - Database, Redis, MinIO
- [ ] Environment configuration (.env setup)
- [ ] Basic logging

### Testing Phase 1
- [ ] Test OTP email delivery
- [ ] Test voice recording and upload
- [ ] Test case creation flow
- [ ] Test admin dashboard access
- [ ] Test monitoring dashboard (all endpoints green)
- [ ] Test daemon mode (close terminal, verify server still running)
- [ ] Test restart script
- [ ] Verify data in database

### Deliverables Phase 1
- Working backend API (daemon mode)
- Working Android app (can record voice and submit cases)
- Working web admin console with navigation and monitoring
- One-line restart command
- Documentation for running locally

---

## Phase 2: Advanced Features - 8-10 hours

### Backend Enhancements
- [ ] Azure Speech Services integration (STT/TTS)
- [ ] Cost monitoring for Azure ($20 limit + email alerts)
- [ ] Advanced Claude API processing:
  - Multi-turn conversation
  - Better slot extraction
  - Summary generation
- [ ] Celery worker setup
- [ ] SLA tracking and escalation worker
- [ ] Duplicate detection (text embeddings)
- [ ] PII masking logic
- [ ] Audit logging system
- [ ] Notification system (push notifications)

### Android App Enhancements
- [ ] Offline mode with SQLite
- [ ] Background sync queue
- [ ] Push notification handling
- [ ] GPS location capture
- [ ] Photo/video attachment
- [ ] Case status tracking
- [ ] Better UI/UX with animations
- [ ] Hindi/English voice interface (actual TTS)

### Web Console Enhancements
- [ ] Moderator console:
  - Triage queue
  - First-time caller review
  - Flag management
  - Audio playback
- [ ] Officer console:
  - Assigned cases inbox
  - Accept/update/resolve actions
  - Evidence upload
  - SLA timers
- [ ] Admin enhancements:
  - Advanced analytics
  - Escalation policy management
  - User role management
  - CSV/Google Sheets import for entities
  - Export functionality

### Monitoring Enhancements
- [ ] Add Celery worker status to monitoring dashboard
- [ ] Add job queue metrics
- [ ] Add Azure cost tracking to dashboard
- [ ] Alert system for failures

### Testing Phase 2
- [ ] Test offline mode and sync
- [ ] Test SLA escalation
- [ ] Test duplicate detection
- [ ] Test all three web consoles
- [ ] Test push notifications
- [ ] Load testing (100+ concurrent users)
- [ ] Test Azure cost limits and alerts

---

## Phase 3: Production Readiness - 6-8 hours

### Android App
- [ ] Build release APK
- [ ] Test on Android 8.0+ devices
- [ ] Test on top 10 Android phones in India:
  - Samsung Galaxy series
  - Xiaomi Redmi series
  - Realme series
  - OnePlus series
  - Vivo series
- [ ] Performance optimization
- [ ] Google Play Store compliance:
  - Privacy policy
  - Data deletion
  - Permissions justification
  - Content rating
- [ ] App signing

### Backend
- [ ] Production environment configuration
- [ ] Database optimization (indexes, partitioning)
- [ ] API rate limiting
- [ ] Security hardening
- [ ] HTTPS/SSL configuration
- [ ] Backup strategy
- [ ] Monitoring and alerting

### Web Consoles
- [ ] Production build optimization
- [ ] Security audit
- [ ] Responsive design for mobile browsers
- [ ] Performance optimization

### Infrastructure
- [ ] Production deployment scripts
- [ ] Database migration strategy
- [ ] Scaling configuration (for 1M users)
- [ ] CDN setup for media files
- [ ] Log aggregation
- [ ] Error tracking (Sentry or similar)

### Testing Phase 3
- [ ] Security testing
- [ ] Performance testing
- [ ] Cross-browser testing
- [ ] Mobile device testing
- [ ] User acceptance testing

---

## Phase 4: Community Content (Future) - 6-8 hours

### Implementation
- [ ] Community posts data model
- [ ] Community post creation flow
- [ ] Moderation for community content
- [ ] Public feed with filters
- [ ] Sharing functionality
- [ ] Featured content selection

### Testing
- [ ] Test community post submission
- [ ] Test moderation flow
- [ ] Test public feed

---

## Phase 5: Advanced Features (Future) - 8-10 hours

### Features
- [ ] SMS/Voice notifications (when infrastructure available)
- [ ] WhatsApp integration
- [ ] Multi-language expansion (beyond Hindi/English)
- [ ] Mobile app for Officers/Moderators
- [ ] Real-time updates via WebSockets
- [ ] Advanced analytics and reporting
- [ ] Elasticsearch integration for full-text search
- [ ] Geo-visualization of cases
- [ ] Citizen satisfaction surveys

---

## Special Requirements (Integrated in Phase 1)

### 1. Daemon Mode Server
- Backend server must run independently of terminal session
- Use process managers: PM2 (Node.js) or Supervisor (Python)
- Auto-restart on failure
- Log output to files

### 2. One-Line Restart Script
Create `restart.sh` that restarts:
- Backend API server
- Web admin server
- Android development server (Expo)
- All Docker services (PostgreSQL, Redis, MinIO)

Usage: `./restart.sh`

### 3. Admin Navigation Panel
- Persistent navigation sidebar/header on all admin pages
- Links to:
  - Dashboard (home)
  - Monitoring Dashboard (new)
  - Cases Management
  - Entity Management
  - Taxonomy Management
  - User Management
  - Analytics & Reports
  - Settings
  - Profile/Logout

### 4. Operational Monitoring Dashboard
Real-time status dashboard showing:
- **API Endpoints Status** (all v1 endpoints):
  - /health
  - /v1/auth/*
  - /v1/cases/*
  - /v1/admin/*
  - Response time
  - Last check timestamp
- **Infrastructure Status**:
  - Backend server (UP/DOWN)
  - PostgreSQL database (connection status)
  - Redis (connection status)
  - MinIO storage (connection status)
- **External Services Status**:
  - Azure Speech API (reachable, quota)
  - Claude API (reachable)
  - SMTP server (reachable)
- **Metrics**:
  - Current Azure costs
  - API call counts
  - Active users
  - Recent errors
- **Auto-refresh**: Every 60 seconds
- **Visual indicators**: Green (healthy), Yellow (warning), Red (down)

---

## Success Criteria

### Phase 1 MVP Success
- ✅ User can sign up/login via email OTP
- ✅ User can record voice and submit grievance
- ✅ Case is created in database
- ✅ Admin can view all cases
- ✅ Admin can see all systems healthy on monitoring dashboard
- ✅ Server runs in daemon mode
- ✅ One-line restart works for all services
- ✅ All navigation links functional

### Phase 2 Success
- ✅ Voice is transcribed to text
- ✅ AI extracts structured data from voice
- ✅ Cases auto-route to correct entity
- ✅ SLA escalation works automatically
- ✅ Offline mode works on mobile
- ✅ All three consoles functional

### Phase 3 Success
- ✅ APK builds successfully
- ✅ App works on 10 different Android phones
- ✅ Passes Google Play Store requirements
- ✅ No security vulnerabilities
- ✅ Performance meets targets (<2s API response)

---

## Current Status

**Last Updated**: 2025-10-26

**Current Phase**: Phase 1 - MVP Development

**Completed**:
- ✅ Project structure
- ✅ Database schema
- ✅ Seed data (entities + taxonomies)
- ✅ Docker Compose setup
- ✅ Architecture documentation
- ✅ Monitoring system (60% - database, API endpoints, health checks)
- ✅ Monitoring dashboard API endpoints
- ✅ Android app Expo setup with navigation
- ✅ Email OTP authentication (mobile integrated with backend)
- ✅ Voice recording with expo-av
- ✅ Hindi/English language toggle system

**In Progress**:
- 🔄 Backend API implementation (SQLAlchemy models for Cases)
- 🔄 Web admin console
- 🔄 Case submission flow completion

**Next Steps** (Priority Order):
1. **Complete case submission flow in Android app** ← CURRENT
2. Implement location picker and photo upload
3. Build case submission review screen
4. Complete backend SQLAlchemy models (Cases, Entities, Taxonomies)
5. Implement case creation API endpoint
6. Build web admin console with monitoring integration
7. Integration testing
8. Debug and fix issues

---

## File Reference
For any updates or to check current phase, refer to this file:
`/Users/diptendu/boloo app/boloo-app/docs/DEVELOPMENT_PHASES.md`

## Related Documentation
- [README.md](../README.md) - Project overview
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
- [API.md](./API.md) - API documentation (to be created)
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment guide (to be created)

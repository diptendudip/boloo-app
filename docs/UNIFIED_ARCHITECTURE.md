# Boloo/Bultoo Unified Architecture

## Overview

Boloo (also known as Bultoo) is a citizen grievance reporting platform that enables users to report civic issues through voice or text in Hindi and English. The platform uses AI to extract structured information from conversations.

## Production URLs

| Component | URL | Description |
|-----------|-----|-------------|
| **Backend API** | https://boloo-backend-api.azurewebsites.net | FastAPI backend |
| **Web App** | https://bultoo.com | React web frontend |
| **Mobile App** | React Native (Expo) | iOS/Android app |

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND CLIENTS                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│   │   bultoo.com │    │  Mobile App  │    │   Admin UI   │        │
│   │   (React)    │    │(React Native)│    │   (Future)   │        │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘        │
│          │                   │                   │                 │
│          └───────────────────┴───────────────────┘                 │
│                              │                                      │
│                    HTTPS (REST API)                                │
│                              │                                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AZURE APP SERVICE                                │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │              boloo-backend-api.azurewebsites.net            │  │
│   │                     (FastAPI + Gunicorn)                     │  │
│   │                                                              │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │  │
│   │  │   Auth      │  │   Chat      │  │   Reports   │         │  │
│   │  │   Router    │  │   Router    │  │   Router    │         │  │
│   │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │  │
│   │         │                │                │                  │  │
│   │  ┌──────┴────────────────┴────────────────┴──────┐          │  │
│   │  │              Service Layer                     │          │  │
│   │  │                                                │          │  │
│   │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐    │          │  │
│   │  │  │ MSG91    │  │ Azure    │  │ Health   │    │          │  │
│   │  │  │ Service  │  │ OpenAI   │  │ Monitor  │    │          │  │
│   │  │  └──────────┘  └──────────┘  └──────────┘    │          │  │
│   │  └────────────────────────────────────────────────┘          │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│   Azure OpenAI    │ │   PostgreSQL      │ │  Azure Speech     │
│   (East US)       │ │   (Azure DB)      │ │  (Central India)  │
│                   │ │                   │ │                   │
│  Model: gpt-4o-   │ │  Host: boloo-db-  │ │  Speech-to-Text   │
│  mini             │ │  server.postgres. │ │  Text-to-Speech   │
│                   │ │  database.azure.  │ │                   │
│                   │ │  com              │ │                   │
└───────────────────┘ └───────────────────┘ └───────────────────┘
```

## Authentication Flow

### Demo Account (For Testing)
```
Phone: 9999999999 (or +919999999999)
OTP: 123456
```

### Production Flow (Real Users)
```
1. User enters phone number
2. Backend sends OTP via MSG91 SMS
3. User enters OTP
4. Backend validates OTP
5. JWT token issued
6. All subsequent requests use Bearer token
```

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │     │ Backend  │     │  MSG91   │     │ Database │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │ POST /auth/    │                │                │
     │ otp/request    │                │                │
     │───────────────>│                │                │
     │                │                │                │
     │                │ Send OTP SMS   │                │
     │                │───────────────>│                │
     │                │                │                │
     │                │ Store OTP hash │                │
     │                │───────────────────────────────>│
     │                │                │                │
     │ {success:true} │                │                │
     │<───────────────│                │                │
     │                │                │                │
     │ POST /auth/    │                │                │
     │ otp/verify     │                │                │
     │───────────────>│                │                │
     │                │                │                │
     │                │ Verify OTP     │                │
     │                │───────────────────────────────>│
     │                │                │                │
     │ {access_token, │                │                │
     │  user}         │                │                │
     │<───────────────│                │                │
     │                │                │                │
```

## Chat Conversation Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │     │ Backend  │     │ Azure    │     │ Azure    │
│          │     │          │     │ Speech   │     │ OpenAI   │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │ POST /chat/    │                │                │
     │ start          │                │                │
     │───────────────>│                │                │
     │                │                │                │
     │ {conversation_ │                │                │
     │  id, greeting} │                │                │
     │<───────────────│                │                │
     │                │                │                │
     │ POST /chat/    │                │                │
     │ turn (voice)   │                │                │
     │───────────────>│                │                │
     │                │ Speech-to-Text │                │
     │                │───────────────>│                │
     │                │                │                │
     │                │ transcription  │                │
     │                │<───────────────│                │
     │                │                │                │
     │                │ Process with   │                │
     │                │ AI             │                │
     │                │───────────────────────────────>│
     │                │                │                │
     │                │ AI response    │                │
     │                │<───────────────────────────────│
     │                │                │                │
     │ {ai_response,  │                │                │
     │  extracted_    │                │                │
     │  data}         │                │                │
     │<───────────────│                │                │
     │                │                │                │
```

## API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/auth/otp/request` | POST | Request OTP |
| `/v1/auth/otp/verify` | POST | Verify OTP |
| `/v1/auth/otp/resend` | POST | Resend OTP |

### Chat
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/start` | POST | Start conversation |
| `/v1/chat/turn` | POST | Send message (text/voice) |
| `/v1/chat/{id}/summary` | GET | Get conversation summary |
| `/v1/chat/{id}/submit` | POST | Submit as report |

### Health
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Basic health check |
| `/health/live` | GET | Liveness probe |
| `/health/ready` | GET | Readiness probe |
| `/health/detailed` | GET | Detailed diagnostics |

## Environment Configuration

### Backend (Azure App Service)
```bash
# Application
APP_NAME=Boloo
APP_ENV=production
DEBUG=False
ALLOWED_ORIGINS=https://bultoo.com,https://boloo-backend-api.azurewebsites.net

# Database
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require

# Azure OpenAI (Chat AI)
AZURE_OPENAI_ENDPOINT=https://boloo-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# Azure Speech (Voice)
AZURE_SPEECH_KEY=<key>
AZURE_SPEECH_REGION=centralindia

# MSG91 SMS (Production OTP)
MSG91_API_KEY=<key>
MSG91_SENDER_ID=BOLOOO
MSG91_TEMPLATE_ID=<template_id>

# Demo Account (Bypass OTP)
DEMO_PHONE_NUMBER=+919999999999
DEMO_OTP_CODE=123456

# JWT
JWT_SECRET_KEY=<secure_random_key>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### Mobile App (Expo)
```json
// app.json
{
  "expo": {
    "extra": {
      "apiUrl": "https://boloo-backend-api.azurewebsites.net"
    }
  }
}
```

### Web App (React)
```javascript
// Environment
REACT_APP_API_URL=https://boloo-backend-api.azurewebsites.net
```

## Azure Resources

| Resource | Type | Region | Purpose |
|----------|------|--------|---------|
| boloo-production-rg | Resource Group | Central India | All resources |
| boloo-backend-api | App Service | Central India | API hosting |
| boloo-db-server | PostgreSQL Flexible | Central India | Database |
| boloo-openai | Cognitive Services | East US | Chat AI |
| boloospeech | Cognitive Services | Central India | Voice processing |
| bolooaudiostorage | Storage Account | Central India | Audio files |

## Security Features

1. **Authentication**: JWT-based with phone OTP verification
2. **HTTPS**: All endpoints require HTTPS
3. **CORS**: Restricted to allowed origins only
4. **Rate Limiting**: 100 requests/minute per IP
5. **Database SSL**: Required in production
6. **Input Validation**: Phone numbers validated for Indian format

## Monitoring

- **Application Insights**: Automatic error and performance tracking
- **Health Endpoints**: Kubernetes-ready probes
- **Logging**: Structured JSON logs

## Deployment

### Backend
```bash
# Deploy via Azure CLI
az webapp deploy --resource-group boloo-production-rg \
  --name boloo-backend-api --src-path backend.zip --type zip
```

### Web Frontend
```bash
# Build and deploy to Static Web App
npm run build
# Upload to Azure Static Web Apps
```

### Mobile App
```bash
# Build with Expo
npx expo build:android
npx expo build:ios
```

## Cost Estimation (Monthly)

| Service | Estimated Cost |
|---------|---------------|
| App Service (B1) | ~$13 |
| PostgreSQL (B1ms) | ~$15 |
| Azure OpenAI | ~$5-20 |
| Azure Speech | ~$1-5 |
| Storage | ~$1 |
| **Total** | **~$35-55/month** |

---

*Last Updated: November 2024*

# AGENTS.md - Codex Configuration for Boloo

## Project Overview

Boloo (also known as Bultoo) is a citizen grievance reporting platform that enables users to report civic issues through voice or text in Hindi and English. The platform uses Azure OpenAI to extract structured information from natural conversations.

## Repository Structure

```
boloo-app/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── routers/           # API endpoints
│   │   │   └── chat.py        # Main chat conversation logic
│   │   ├── services/          # Business logic
│   │   │   ├── azure_openai_service.py  # AI prompts & responses
│   │   │   ├── transcription_service.py # Speech-to-text
│   │   │   └── completeness_analyzer.py # Report completeness
│   │   ├── models/            # SQLAlchemy models
│   │   └── utils/             # Utility functions
│   ├── requirements.txt       # Python dependencies
│   └── tests/                 # pytest test suite
├── mobile/                    # React Native (Expo) mobile app
│   ├── src/
│   │   ├── components/        # React components
│   │   │   └── ChatInterface.tsx  # Main chat UI
│   │   ├── services/          # API clients
│   │   │   └── chat.ts        # Chat API service
│   │   ├── screens/           # App screens
│   │   └── context/           # React context providers
│   └── package.json           # NPM dependencies
├── web/                       # React web frontend
└── docs/                      # Documentation
```

## Key Files for Chat Logic

When working on the conversational system, focus on these files:

### Backend (Python/FastAPI)
- `backend/app/routers/chat.py` - Chat API endpoints, conversation flow
- `backend/app/services/azure_openai_service.py` - AI prompts, personality
- `backend/app/services/completeness_analyzer.py` - Report completeness logic
- `backend/app/services/journalist_summary.py` - Summary generation

### Frontend (React Native/TypeScript)
- `mobile/src/components/ChatInterface.tsx` - Chat UI component
- `mobile/src/services/chat.ts` - Chat API client
- `mobile/src/screens/HomeScreen.tsx` - Home screen

## Development Commands

### Backend
```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run linting
ruff check .

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Mobile App
```bash
# Navigate to mobile
cd mobile

# Install dependencies
npm install

# Start Expo development server
npx expo start

# Run linting
npm run lint

# Type checking
npx tsc --noEmit
```

## Environment Variables

The backend requires these environment variables (DO NOT commit actual values):

```
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# Azure Speech
AZURE_SPEECH_KEY=your-key
AZURE_SPEECH_REGION=centralindia

# Database
DATABASE_URL=postgresql://user:pass@host/db

# MSG91 SMS (India OTP)
MSG91_API_KEY=your-key
MSG91_SENDER_ID=BOLOOO
MSG91_TEMPLATE_ID=your-template
```

## API Endpoints

### Authentication
- `POST /v1/auth/otp/request` - Request OTP
- `POST /v1/auth/otp/verify` - Verify OTP and get JWT

### Chat
- `POST /v1/chat/start` - Start new conversation
- `POST /v1/chat/turn` - Send message (text or voice)
- `GET /v1/chat/{id}/summary` - Get conversation summary
- `POST /v1/chat/{id}/submit` - Submit as report

### Health
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed diagnostics

## Production URLs

- Backend API: https://boloo-backend-api.azurewebsites.net
- Web App: https://bultoo.com

## Demo Account (Testing)

```
Phone: 9999999999 or +919999999999
OTP: 123456
```

## Known Issues to Fix

1. **Conversation sounds robotic** - Review prompts in `azure_openai_service.py:531-570`
2. **Submit button not working** - Check `ChatInterface.tsx:454-546` and `chat.py:1582-1770`

## Code Style

- Python: Follow PEP 8, use type hints
- TypeScript: Use strict mode, prefer functional components
- Keep files under 500 lines when possible
- Write tests for new features

## Testing

```bash
# Backend tests
cd backend && pytest -v

# Mobile type check
cd mobile && npx tsc --noEmit
```

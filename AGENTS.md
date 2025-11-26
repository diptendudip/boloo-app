# AGENTS.md - Codex Configuration for Boloo

## Project Overview

Boloo (also known as Bultoo) is a citizen grievance reporting platform that enables users to report civic issues through voice or text in Hindi and English.

## ⚠️ IMPORTANT: 3-Agent Multi-Agent Architecture (Current System)

The platform uses a **3-Agent Multi-Agent System** (enabled by default via `USE_MULTI_AGENT=1`):

### Agent Architecture

| Agent | File | Purpose |
|-------|------|---------|
| **Agent A** | `backend/app/prompts/agent_a_report_formatter.py` | Final CGNet-style Hindi report generator |
| **Agent B** | `backend/app/prompts/agent_b_collector.py` | User-facing conversational collector |
| **Agent C** | `backend/app/prompts/agent_c_planner.py` | Strategic question planner/policy agent |

### Orchestration Flow

```
User Message → /turn endpoint
                    ↓
              USE_MULTI_AGENT=1? (default: yes)
                    ↓ yes
              process_chat_turn_v2()
                    ↓
         MultiAgentOrchestrator.process_user_turn()
                    ↓
    ┌───────────────┼───────────────┐
    ↓               ↓               ↓
Agent C         Agent B         Agent A
(Planner)     (Collector)     (Formatter)
```

### Key Files (MULTI-AGENT SYSTEM)

**Orchestrator:**
- `backend/app/services/multi_agent_orchestrator.py` (921 lines) - Main orchestration logic

**Agent Prompts:**
- `backend/app/prompts/agent_a_report_formatter.py` - Report formatting
- `backend/app/prompts/agent_b_collector.py` - Conversational collection with `<meta>` blocks
- `backend/app/prompts/agent_c_planner.py` - Planning directives (ASK_FOR_SLOT, SUBMIT_NOW, etc.)

**Router:**
- `backend/app/routers/chat.py` - Lines 1165-1176 delegate to `process_chat_turn_v2` when `USE_MULTI_AGENT=1`

**State Management:**
- `backend/app/models/conversation_state.py` - ConversationState, AgentDirective, SLOT_REGISTRY

## Repository Structure

```
boloo-app/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── routers/
│   │   │   └── chat.py        # /turn → process_chat_turn_v2 (multi-agent)
│   │   ├── services/
│   │   │   ├── multi_agent_orchestrator.py  # ⭐ 3-AGENT ORCHESTRATOR
│   │   │   ├── azure_openai_service.py      # Legacy (USE_MULTI_AGENT=0 only)
│   │   │   └── ...
│   │   ├── prompts/           # ⭐ AGENT PROMPTS
│   │   │   ├── agent_a_report_formatter.py
│   │   │   ├── agent_b_collector.py
│   │   │   └── agent_c_planner.py
│   │   ├── models/
│   │   │   └── conversation_state.py  # ConversationState, SLOT_REGISTRY
│   │   └── utils/
│   ├── requirements.txt
│   └── tests/
│       └── test_multi_agent.py  # Multi-agent tests
├── mobile/                    # React Native (Expo) mobile app
├── web/                       # React web frontend
└── docs/
```

## Agent B Output Format

Agent B returns natural text + structured `<meta>` block:

```
नमस्ते! कृपया अपनी समस्या के बारे में बताएं।

<meta>
{
  "slots": {
    "location_village": "कोटवार पारा",
    "problem_category": "road"
  },
  "frustration_level": "low",
  "user_wants_submit": false
}
</meta>
```

## Agent C Directives

Agent C returns JSON planning decisions:

```json
{
  "mode": "ASK_FOR_SLOT",
  "target_slot": "reporter.phone",
  "reason": "Phone required for follow-up contact"
}
```

Modes: `ASK_FOR_SLOT`, `CONFIRM_AND_SUBMIT`, `SUBMIT_NOW`, `SMALL_TALK_REASSURE`

## Feature Flag

```python
# backend/app/routers/chat.py:65
USE_MULTI_AGENT = os.getenv("USE_MULTI_AGENT", "1") == "1"  # Default: ENABLED
```

- `USE_MULTI_AGENT=1` (default): Uses 3-agent system via `process_chat_turn_v2`
- `USE_MULTI_AGENT=0`: Falls back to legacy `azure_openai_service.py`

## Development Commands

### Backend
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pytest -v
uvicorn app.main:app --reload --port 8000
```

### Mobile App
```bash
cd mobile
npm install
npx expo start
```

## API Endpoints

### Chat (Multi-Agent)
- `POST /v1/chat/start` - Start new conversation
- `POST /v1/chat/turn` - Send message → delegates to multi-agent orchestrator
- `POST /v1/chat/turn-v2` - Direct multi-agent endpoint
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

## Code Style

- Python: PEP 8, type hints
- TypeScript: Strict mode, functional components
- Keep files under 500 lines
- Write tests for new features

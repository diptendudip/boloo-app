# AI Coach Training Mode Implementation

## Overview

This document describes the complete implementation of the AI Coach Onboarding System for the Boloo mobile application. The system provides temporary training for new users during their first 5 reports, using multi-turn conversational voice interactions to ensure complete and high-quality grievance submissions.

## Architecture

### Backend Components

#### 1. Database Models

**User Model** (`backend/app/models/user.py`)
- Added 3 new fields for training state tracking:
  - `training_reports_count`: Integer, default 0
  - `training_completed`: Boolean, default False
  - `training_mode_enabled`: Boolean, default True
  - `conversations`: Relationship to Conversation model

**Conversation Model** (`backend/app/models/conversation.py`)
- Tracks multi-turn AI Coach conversations
- Fields:
  - `id`: UUID primary key
  - `user_id`: Foreign key to users
  - `case_id`: Optional foreign key to cases
  - `turn_count`: Current turn number (max 3)
  - `is_complete`: Boolean flag
  - `completeness_score`: Float 0.0-1.0
  - `collected_fields`: Array of collected field names
  - `missing_fields`: JSONB array of missing field details
  - `created_at`, `completed_at`: Timestamps

**ConversationTurn Model** (`backend/app/models/conversation_turn.py`)
- Individual turns within conversations
- Fields:
  - `id`: UUID primary key
  - `conversation_id`: Foreign key
  - `turn_number`: Integer (unique per conversation)
  - `audio_url`: Optional audio file reference
  - `transcript_text`: User's voice transcript
  - `language_detected`: Detected language (hi/en)
  - `ai_prompt`, `ai_response`, `ai_question_asked`: AI interaction
  - `intent`, `confidence`: Classification results
  - `fields_extracted`: JSONB of extracted field data

#### 2. Services

**CompletenessAnalyzer** (`backend/app/services/completeness_analyzer.py`)
- Uses Azure OpenAI GPT-4o-mini for intelligent analysis
- Analyzes transcripts to:
  - Extract structured field data
  - Calculate completeness score (0.0-1.0)
  - Identify missing critical information
  - Generate contextual follow-up questions in Hindi
- Defines 5 required fields with importance levels:
  - `issue_description` (critical)
  - `location` (critical)
  - `when_started` (high)
  - `affected_people` (medium)
  - `previous_action` (medium)

**TrainingService** (`backend/app/services/training_service.py`)
- Manages training mode state and graduation logic
- Key methods:
  - `is_in_training_mode()`: Check if user should use training
  - `should_graduate()`: Check if user completed 5 reports
  - `increment_report_count()`: Track progress
  - `graduate_user()`: Mark training complete, trigger celebration
  - `get_training_progress()`: Return progress details
  - `enable/disable_training_mode()`: Settings toggles

**AICoachConversationService** (`backend/app/services/ai_coach_conversation_service.py`)
- Manages conversation sessions and turns
- Key methods:
  - `create_conversation()`: Start new session
  - `add_turn()`: Add user input and AI response
  - `update_completeness()`: Update scores and fields
  - `complete_conversation()`: Mark session complete
  - `should_continue_conversation()`: Check if should ask follow-up
  - `get_conversation_history_for_ai()`: Format context for AI

#### 3. API Endpoint

**Training Mode Endpoint** (`backend/app/routers/transcription.py`)
- Route: `POST /v1/transcription/ai-coach-training`
- Request:
  - `audio`: Audio file (multipart/form-data)
  - `user_id`: UUID string
  - `conversation_id`: Optional UUID (for continuing conversations)
  - `language`: Language code (default: hi-IN)
- Response:
  ```json
  {
    "success": true,
    "transcript": "transcribed text",
    "language_detected": "hi-IN",
    "conversation_id": "uuid",
    "turn_number": 1,
    "is_complete": false,
    "completeness_score": 0.6,
    "collected_fields": ["issue_description", "location"],
    "missing_fields": [...],
    "next_question_hi": "यह समस्या कब से हो रही है?",
    "next_question_en": "Since when has this issue been occurring?",
    "should_continue": true,
    "report_count": 1,
    "graduation": {
      "graduated": false,
      "message": "",
      "total_reports": 1
    }
  }
  ```

**Flow:**
1. Transcribe audio (Azure Speech)
2. Get/create conversation
3. Analyze completeness (Azure OpenAI)
4. Add turn to conversation
5. Update completeness scores
6. Check if should continue (max 3 turns)
7. Auto-complete if score >= 0.8 or max turns reached
8. Increment report count if complete
9. Check graduation (after 5 complete reports)

### Mobile Components

#### 1. Types (`mobile/src/types/aiCoach.ts`)
- `AICoachTrainingResponse`: API response type
- `MissingField`: Field definition with bilingual prompts
- `ConversationTurn`: Turn history item
- `TrainingProgress`: Progress tracking data

#### 2. Service (`mobile/src/services/aiCoach.ts`)
- `AICoachService` class with methods:
  - `submitTrainingTurn()`: Upload audio and get analysis
  - `getTrainingProgress()`: Fetch user progress
  - `enableTrainingMode()`: Turn on training
  - `disableTrainingMode()`: Turn off training

#### 3. Screens

**TrainingVoiceScreen** (`mobile/src/screens/TrainingVoiceScreen.tsx`)
- Multi-turn conversation interface
- Features:
  - Turn counter (1/3, 2/3, 3/3)
  - Completeness score display with color coding
  - Current question display in Hindi
  - Voice recording with playback
  - Conversation history preview
  - Progress bar visualization
- Handles:
  - Audio recording and playback
  - API submission with loading states
  - Turn progression
  - Automatic completion detection
  - Graduation detection and navigation

**GraduationScreen** (`mobile/src/screens/GraduationScreen.tsx`)
- Celebration screen after completing 5 reports
- Features:
  - Confetti animation (50 pieces)
  - Scale-in animation for graduation cap
  - Stats display (reports completed, 100% progress)
  - Achievement badge
  - "What's Next" information box
  - Continue to home button
- Shown when user graduates from training mode

**IssueSelectionScreen** (updated)
- Detects training mode on load
- Routes to appropriate screen:
  - TrainingVoice if `in_training_mode === true`
  - VoiceRecord if `in_training_mode === false`
- Displays training mode badge when active

#### 4. Navigation

Updated `AppNavigator.tsx` to include:
- `TrainingVoice` screen (with AI Coach header)
- `Graduation` screen (headerless for full-screen experience)

Updated `RootStackParamList` types:
- `TrainingVoice: { taxonomyId: string; userId: string }`
- `Graduation: { totalReports: number; message: string }`

## User Flow

### New User (Training Mode)

1. **Login** → User authenticates
2. **Home** → Tap "Report New Issue"
3. **Issue Selection** → See "🎓 Training Mode Active" badge, select issue
4. **Training Voice Screen (Turn 1)**
   - See question: "अपनी समस्या के बारे में बताएं"
   - Record voice describing issue
   - Submit → AI analyzes completeness
   - Shows score (e.g., 40%) and next question

5. **Training Voice Screen (Turn 2)**
   - See previous turn in history
   - Answer follow-up question (e.g., location)
   - Submit → AI analyzes again
   - Shows improved score (e.g., 70%) and next question

6. **Training Voice Screen (Turn 3)**
   - See previous 2 turns
   - Answer final follow-up (e.g., timing)
   - Submit → AI analyzes
   - Score reaches 85% → Conversation complete!

7. **After Report Complete**
   - See "Report Complete!" message
   - Reports count increments (1/5)
   - Return to home

8. **After 5 Reports**
   - Final report triggers graduation
   - Navigate to **Graduation Screen**
   - See celebration animation and stats
   - Continue to home

9. **Graduated User (Simple Mode)**
   - Training mode automatically disabled
   - Future reports use simple one-tap recording
   - Can re-enable training in Settings if desired

### Experienced User (Simple Mode)

1. **Login** → User with `training_completed === true`
2. **Issue Selection** → No training badge, select issue
3. **Voice Record Screen** → Simple one-tap recording
4. **Submit** → Direct submission (existing flow)

## Configuration

### Environment Variables (Backend)

```bash
# Azure OpenAI (for completeness analysis)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# Azure Speech Services (for transcription)
AZURE_SPEECH_KEY=your-speech-key
AZURE_SPEECH_REGION=eastus
```

### Training Parameters

**Backend** (`training_service.py`):
- `graduation_threshold = 5` (reports needed)
- `completeness_threshold = 0.8` (80% to mark complete)

**Backend** (`ai_coach_conversation_service.py`):
- `max_turns = 3` (initial + 2 follow-ups)

**Mobile** (TrainingVoiceScreen):
- `maxTurns = 3`
- Color coding: Green (≥80%), Yellow (≥50%), Red (<50%)

## Database Migrations

Migration file: `backend/alembic/versions/202510311400_add_ai_coach_training.py`

**Changes:**
1. Add columns to `users` table:
   - `training_reports_count INTEGER DEFAULT 0`
   - `training_completed BOOLEAN DEFAULT false`
   - `training_mode_enabled BOOLEAN DEFAULT true`

2. Create `conversations` table with all fields

3. Create `conversation_turns` table with unique constraint on (conversation_id, turn_number)

**Run migration:**
```bash
cd backend
alembic upgrade head
```

## Testing

### Backend Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test AI Coach training endpoint (with audio file)
curl -X POST http://localhost:8000/v1/transcription/ai-coach-training \
  -F "audio=@test_audio.m4a" \
  -F "user_id=user-uuid" \
  -F "language=hi-IN"

# Test get training progress
curl http://localhost:8000/v1/users/{user_id}/training-progress
```

### Mobile Testing

1. **Install dependencies:**
```bash
cd mobile
npm install
```

2. **Start Expo:**
```bash
npx expo start
```

3. **Test flow:**
   - Login with test OTP: 123456
   - Navigate to Issue Selection
   - Verify training mode badge appears
   - Select issue → Should route to TrainingVoiceScreen
   - Record audio and test multi-turn flow
   - Complete 5 reports to test graduation

## Key Features

### Intelligent Completeness Analysis
- Uses Azure OpenAI for context-aware field extraction
- Analyzes Hindi, English, and Chhattisgarhi
- Generates culturally appropriate follow-up questions
- Adapts based on conversation history

### Graduation System
- Automatic tracking of completed reports
- Triggers celebration at 5 reports
- Auto-disables training mode
- Confetti animation and achievement badge

### Bilingual Support
- All prompts in Hindi and English
- Language-aware transcription
- Follow-up questions in Hindi by default

### Flexible Turn Management
- Max 3 turns per report
- Early completion if score ≥ 80%
- Conversation history display
- Progress visualization

### User Experience
- Training mode badge for awareness
- Real-time completeness feedback
- Color-coded score display
- Smooth animations and transitions
- Clear instructions at each step

## API Integration Points

### Mobile → Backend
1. `POST /v1/transcription/ai-coach-training` - Submit audio turn
2. `GET /v1/users/{user_id}/training-progress` - Get progress
3. `POST /v1/users/{user_id}/enable-training` - Enable training
4. `POST /v1/users/{user_id}/disable-training` - Disable training

### Backend → Azure Services
1. **Azure Speech Services** - Audio transcription
2. **Azure OpenAI** - Completeness analysis, field extraction, question generation

## Troubleshooting

### Issue: Training mode not detecting

**Check:**
1. User has `training_mode_enabled = true`
2. User has `training_completed = false`
3. API endpoint `/v1/users/{user_id}/training-progress` is accessible

### Issue: Completeness always low

**Check:**
1. Azure OpenAI credentials are correct
2. User is speaking clearly in Hindi/English
3. Check logs for transcription quality
4. Verify prompt in `completeness_analyzer.py`

### Issue: Not graduating after 5 reports

**Check:**
1. Reports are actually completing (check `is_complete = true`)
2. `training_reports_count` is incrementing
3. Graduation threshold is set to 5

## Future Enhancements

1. **Settings Screen**: Add toggle for training mode on/off
2. **Progress Dashboard**: Show training progress on home screen
3. **Custom Questions**: Allow admins to configure required fields
4. **Offline Support**: Cache training data for offline use
5. **Analytics**: Track training effectiveness and completion rates
6. **Localization**: Add more regional languages
7. **Voice Feedback**: Audio responses from AI Coach
8. **Tutorial**: First-time user walkthrough

## Files Modified/Created

### Backend
- ✅ `app/models/user.py` - Added training fields
- ✅ `app/models/conversation.py` - New model
- ✅ `app/models/conversation_turn.py` - New model
- ✅ `app/models/case.py` - Added conversations relationship
- ✅ `app/services/completeness_analyzer.py` - New service
- ✅ `app/services/training_service.py` - New service
- ✅ `app/services/ai_coach_conversation_service.py` - New service
- ✅ `app/routers/transcription.py` - Added `/ai-coach-training` endpoint
- ✅ `alembic/versions/202510311400_add_ai_coach_training.py` - Migration

### Mobile
- ✅ `src/types/aiCoach.ts` - New types
- ✅ `src/services/aiCoach.ts` - New service
- ✅ `src/screens/TrainingVoiceScreen.tsx` - New screen
- ✅ `src/screens/GraduationScreen.tsx` - New screen
- ✅ `src/screens/IssueSelectionScreen.tsx` - Updated routing
- ✅ `src/navigation/AppNavigator.tsx` - Added routes
- ✅ `src/types/index.ts` - Updated RootStackParamList

## Summary

The AI Coach Onboarding System is now fully implemented and integrated into the Boloo mobile application. The system provides:

1. **Backend**: Complete API with Azure OpenAI integration for intelligent completeness analysis
2. **Mobile**: Full UI with training mode detection, multi-turn conversations, and graduation celebration
3. **Database**: Proper models and migrations for conversation tracking
4. **User Flow**: Seamless experience from training mode through graduation to simple mode

The implementation follows the original requirements from TRIAGE_AND_UX_REQUIREMENTS.md Section 9 and AI_STORY_COACH_SYSTEM.md, providing a Steve Jobs-level minimalist UX that guides new users through their first 5 reports before graduating them to the simple one-tap experience.

---
**Status**: ✅ Complete and Ready for Testing
**Last Updated**: October 31, 2025

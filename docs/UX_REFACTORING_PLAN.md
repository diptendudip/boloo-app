# Boloo App UX Refactoring Implementation Plan

**Date:** January 2025
**Status:** Planning
**Estimated Timeline:** 4-6 weeks

## Overview

This document outlines the complete refactoring plan based on comprehensive UX/UI audit. The work is divided into 3 phases prioritized by impact and dependencies.

---

## Phase 1: Critical Infrastructure (Week 1-2)

### 1.1 Remove Testing UI Banner ⚠️ **CRITICAL**
**Files to Modify:**
- `/mobile/src/screens/VerifyOTPScreen.tsx` (Lines 121-124)
- `/mobile/src/screens/LoginScreen.tsx`
- `/mobile/src/context/AuthContext.tsx` (Lines 99-127)

**Changes:**
```tsx
// Remove testing banner from production, but keep dummy OTP logic in __DEV__
{__DEV__ && (
  <View style={styles.devBanner}>
    <Text style={styles.devText}>DEV MODE</Text>
  </View>
)}

// In AuthContext.tsx - keep this for development
if (__DEV__ && otp === '123456') {
  // Dummy auth logic remains for local testing
  console.log('DEV MODE: Using dummy OTP');
  // ... rest of dummy login
}
```

**Important:**
- Remove visible testing banner from UI (unprofessional)
- **Keep dummy OTP logic** in `__DEV__` mode for development testing
- Use environment variable `EXPO_PUBLIC_ENABLE_TEST_MODE` for finer control

**Backend:** Already fixed with MSG91 OTP integration.

---

### 1.2 Remove Training Mode System
**Files to DELETE:**
- `/mobile/src/screens/TrainingVoiceScreen.tsx`
- `/mobile/src/screens/GraduationScreen.tsx`
- `/mobile/src/services/aiCoach.ts`

**Files to MODIFY:**
- `/mobile/src/screens/IssueSelectionScreen.tsx` - Remove training mode checks (Lines 29-50, 114-126)
- `/mobile/src/navigation/AppNavigator.tsx` - Remove training screens from navigator
- `/backend/app/models/user.py` - Remove `is_first_timer`, `training_reports_count`, `training_completed` fields
- `/backend/app/routers/auth.py` - Remove training mode initialization

**Rationale:** User wants conversational AI to guide report completion instead of fixed training flow.

---

### 1.3 Implement Tab-Based Navigation
**New Architecture:**
```
BottomTabNavigator:
  ├─ होम (Home) Tab
  │   └─ Stack: Home → Report Flow (Modal) → CaseSubmitted
  ├─ मेरी शिकायतें (My Reports) Tab
  │   └─ Stack: MyCases → CaseDetail → Timeline
  ├─ सहायता (Help) Tab
  │   └─ Stack: Help → FAQ → Contact
  └─ प्रोफाइल (Profile) Tab
      └─ Stack: Profile → Edit Profile → Change Phone
```

**New Files:**
- `/mobile/src/navigation/BottomTabNavigator.tsx`
- `/mobile/src/screens/HelpScreen.tsx`
- `/mobile/src/screens/ProfileScreen.tsx`
- `/mobile/src/screens/CaseDetailScreen.tsx`
- `/mobile/src/screens/CaseTimelineScreen.tsx`

**Benefits:**
- Always-accessible navigation
- No more "back" button confusion
- Persistent context
- Familiar pattern (Instagram, WhatsApp, etc.)

---

### 1.4 Delete MyDiary Feature
**Files to DELETE:**
- `/mobile/src/screens/MyDiaryScreen.tsx`
- `/mobile/src/screens/PersonalNoteDetailScreen.tsx`
- `/mobile/src/screens/CreatePersonalNoteScreen.tsx`

**Database Migration:**
```sql
-- If personal_notes table exists, drop it
DROP TABLE IF EXISTS personal_notes;
```

**Rationale:** User confirmed this is not core feature and should be removed.

---

### 1.5 Hindi-First Error Messages
**New File:**
- `/mobile/src/constants/errorMessages.ts`

```typescript
export const ERROR_MESSAGES = {
  NO_INTERNET: {
    hi: 'इंटरनेट कनेक्शन नहीं है',
    en: 'No internet connection',
    action: 'RETRY'
  },
  SERVER_ERROR: {
    hi: 'सर्वर में समस्या है',
    en: 'Server error',
    action: 'RETRY_LATER'
  },
  CASE_NOT_FOUND: {
    hi: 'शिकायत नहीं मिली',
    en: 'Case not found',
    action: 'GO_HOME'
  },
  // ... more error mappings
};
```

**Files to Modify:**
- `/mobile/src/services/api.ts` - Add error interceptor
- ALL screen files - Replace English errors with Hindi

---

## Phase 2: User Experience Enhancements (Week 3-4)

### 2.1 Welcome Message & Onboarding
**Files to Modify:**
- `/mobile/src/screens/LoginScreen.tsx` - Add welcome banner

**New Files:**
- `/mobile/src/screens/OnboardingScreen.tsx` - Multi-screen swipeable tutorial
- `/mobile/src/components/OnboardingSlide.tsx` - Individual slide component

**Onboarding Flow:**
1. **Slide 1:** "बोलो ऐप में आपका स्वागत है" - What is Boloo?
2. **Slide 2:** "अपनी समस्या बोलें" - How to report (voice/text)
3. **Slide 3:** "क्या होगा आगे?" - What happens after reporting
4. **Slide 4:** "शुरू करें!" - Call to action

---

### 2.2 Offline Mode with Local Caching
**New Files:**
- `/mobile/src/services/storage.ts` - AsyncStorage wrapper
- `/mobile/src/hooks/useOfflineQueue.ts` - Queue management hook
- `/mobile/src/hooks/useNetworkStatus.ts` - Network detection

**Implementation:**
```typescript
// Queue recordings locally
await offlineQueue.add({
  type: 'AUDIO_RECORDING',
  audio: audioUri,
  metadata: caseData,
  timestamp: Date.now()
});

// Auto-sync when online
useEffect(() => {
  if (isOnline) {
    offlineQueue.syncAll();
  }
}, [isOnline]);
```

**Cache Strategy:**
- Issue types (taxonomies) → Cache 24 hours
- User's reports → Cache indefinitely, sync on change
- Next steps data → Cache per case
- Audio recordings → Queue until uploaded

---

### 2.3 Push Notifications
**Setup:**
```bash
npx expo install expo-notifications
```

**New Files:**
- `/mobile/src/services/notifications.ts`
- `/backend/app/services/push_notifications.py`

**Notifications to Send:**
- Report submitted ✅
- Official viewed report 👀
- Action started 🔧
- Issue resolved ✓
- Escalation available 🔴

---

### 2.4 Timeline View for Case Tracking
**New Files:**
- `/mobile/src/components/CaseTimeline.tsx`
- `/mobile/src/components/TimelineItem.tsx`

**Timeline Events:**
```typescript
interface TimelineEvent {
  id: string;
  timestamp: Date;
  type: 'SUBMITTED' | 'VIEWED' | 'ACTION_STARTED' | 'RESOLVED' | 'ESCALATED';
  actor: string; // e.g., "ग्राम पंचायत अधिकारी"
  description_hi: string;
  description_en: string;
  icon: string; // Emoji
}
```

**Visual Design:**
```
✅ 12 जनवरी, 2025 - 2:30 PM
   शिकायत दर्ज की गई
   Complaint registered

   ↓ (connecting line)

👀 13 जनवरी, 2025 - 10:15 AM
   अधिकारी ने देखा
   Official viewed
   ग्राम पंचायत अधिकारी - रामेश कुमार

   ↓

🔧 15 जनवरी, 2025 - 9:00 AM
   काम शुरू हुआ
   Action started

   ↓

[⏳ अभी चल रहा है...]
```

---

### 2.5 Quick Status View on HomeScreen
**Files to Modify:**
- `/mobile/src/screens/HomeScreen.tsx`

**Add Component:**
```tsx
<View style={styles.recentActivity}>
  <Text style={styles.sectionTitle}>हाल की गतिविधि</Text>

  {recentCases.slice(0, 3).map(case => (
    <CaseStatusCard key={case.id} case={case} compact />
  ))}

  <TouchableOpacity onPress={() => navigation.navigate('MyCases')}>
    <Text style={styles.viewAll}>सभी देखें →</Text>
  </TouchableOpacity>
</View>
```

---

### 2.6 Phone Number Change Flow
**New Files:**
- `/mobile/src/screens/ChangePhoneScreen.tsx`
- `/backend/app/routers/profile.py` - Add `/profile/change-phone` endpoint

**Flow:**
1. User enters new phone number
2. Send OTP to new number
3. Verify OTP (no OTP to old number needed)
4. Migrate all reports to new phone's UUID
5. Update user record
6. Logout and force re-login

**Backend Migration:**
```python
@router.post("/profile/change-phone")
async def change_phone_number(
    request: ChangePhoneRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Verify OTP for NEW number only (user requirement)
    # 2. Create new user with new phone
    # 3. Migrate all cases
    db.execute(
        "UPDATE cases SET user_id = :new_id WHERE user_id = :old_id",
        {"new_id": new_user.id, "old_id": current_user.id}
    )
    # 4. Deactivate old user
    current_user.is_active = False
    db.commit()
```

---

### 2.7 Photo & Document Attachment 📸 **NEW FEATURE**
**Purpose:** Allow users to attach photos and documents when reporting issues (broken handpump photo, electricity bill, etc.)

**New Files:**
- `/mobile/src/components/MediaPicker.tsx`
- `/mobile/src/components/AttachmentPreview.tsx`
- `/backend/app/routers/uploads.py`
- `/backend/app/services/file_storage.py`

**Mobile Implementation:**
```bash
# Install required packages
npx expo install expo-image-picker expo-document-picker expo-file-system
```

**MediaPicker Component:**
```tsx
<MediaPicker
  onPhotoSelected={(uri) => setAttachments([...attachments, { type: 'photo', uri }])}
  onDocumentSelected={(uri) => setAttachments([...attachments, { type: 'doc', uri }])}
  maxFiles={5}
  allowedTypes={['photo', 'pdf', 'doc']}
/>

{/* Buttons */}
<TouchableOpacity onPress={openCamera}>
  <Icon name="camera" />
  <Text>फोटो लें</Text>
</TouchableOpacity>

<TouchableOpacity onPress={openGallery}>
  <Icon name="image" />
  <Text>गैलरी से चुनें</Text>
</TouchableOpacity>

<TouchableOpacity onPress={openDocumentPicker}>
  <Icon name="file" />
  <Text>दस्तावेज़ संलग्न करें</Text>
</TouchableOpacity>
```

**Backend Storage:**
```python
# Use AWS S3 or local storage
@router.post("/v1/uploads/attachment")
async def upload_attachment(
    file: UploadFile = File(...),
    case_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file type and size (max 10MB per file)
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large")

    # Upload to S3/storage
    file_url = await storage_service.upload(file, f"cases/{case_id}/{file.filename}")

    # Save to database
    attachment = CaseAttachment(
        case_id=case_id,
        file_url=file_url,
        file_type=file.content_type,
        file_size=file.size,
        uploaded_by=current_user.id
    )
    db.add(attachment)
    db.commit()

    return {"success": True, "file_url": file_url}
```

**Database Schema:**
```sql
CREATE TABLE case_attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    file_url VARCHAR(500) NOT NULL,
    file_type VARCHAR(50),
    file_size INTEGER,
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_attachments_case_id ON case_attachments(case_id);
```

**UX Flow:**
1. User recording complaint → See "📎 Attach Photo" button
2. Choose: Take Photo | Choose from Gallery | Attach Document
3. Preview selected files (with remove option)
4. Files upload with complaint submission
5. Show attachments in case detail view (thumbnail grid)

**Compression:**
- Photos: Compress to 1920x1080 max, 80% quality (reduce from 5MB → 500KB)
- Documents: No compression, but limit to 10MB

---

### 2.8 Public Feed System 📱 **NEW MAJOR FEATURE**
**Purpose:** Social media-style public feed where users can share their grievance stories, build community awareness, and hold officials accountable.

**Similar To:** Facebook/Instagram/X (Twitter) feed with likes, comments, shares

**New Files:**
- `/mobile/src/screens/FeedScreen.tsx` (new tab in bottom navigation)
- `/mobile/src/components/FeedPost.tsx`
- `/mobile/src/components/FeedComments.tsx`
- `/backend/app/routers/feed.py`
- `/backend/app/models/feed.py`

**Database Schema:**
```sql
-- Public posts table
CREATE TABLE feed_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,  -- User chooses to publish or not
    visibility VARCHAR(20) DEFAULT 'public',  -- public, friends, private
    status VARCHAR(50),  -- resolved, pending, escalated
    location VARCHAR(255),
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    views_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Likes table
CREATE TABLE feed_likes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID NOT NULL REFERENCES feed_posts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(post_id, user_id)  -- User can like only once
);

-- Comments table
CREATE TABLE feed_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID NOT NULL REFERENCES feed_posts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    comment_text TEXT NOT NULL,
    parent_comment_id UUID REFERENCES feed_comments(id),  -- For replies
    likes_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Shares table
CREATE TABLE feed_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID NOT NULL REFERENCES feed_posts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    shared_with_text TEXT,  -- Optional comment when sharing
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_feed_posts_created_at ON feed_posts(created_at DESC);
CREATE INDEX idx_feed_posts_user_id ON feed_posts(user_id);
CREATE INDEX idx_feed_likes_post_id ON feed_likes(post_id);
CREATE INDEX idx_feed_comments_post_id ON feed_comments(post_id);
```

**Backend API Endpoints:**
```python
# GET /v1/feed - Get public feed (paginated)
# POST /v1/feed/publish - Publish a case to public feed
# POST /v1/feed/{post_id}/like - Like a post
# DELETE /v1/feed/{post_id}/like - Unlike a post
# GET /v1/feed/{post_id}/comments - Get comments on a post
# POST /v1/feed/{post_id}/comment - Add comment
# POST /v1/feed/{post_id}/share - Share a post
# GET /v1/feed/trending - Get trending posts (most liked/commented)
# GET /v1/feed/resolved - Get resolved issue success stories
```

**Feed Post Component:**
```tsx
<FeedPost>
  {/* Header */}
  <View style={styles.postHeader}>
    <Avatar source={{ uri: user.avatar }} />
    <View>
      <Text style={styles.userName}>{user.name}</Text>
      <Text style={styles.location}>📍 {post.location}</Text>
      <Text style={styles.timestamp}>2 घंटे पहले</Text>
    </View>
    <Badge status={post.status} /> {/* Pending/Resolved/Escalated */}
  </View>

  {/* Content */}
  <View style={styles.postContent}>
    <Text style={styles.contentText}>{post.content}</Text>
    {post.attachments?.length > 0 && (
      <ImageGallery images={post.attachments} />
    )}
  </View>

  {/* Engagement Stats */}
  <View style={styles.engagementStats}>
    <Text>👍 {post.likes_count} पसंद</Text>
    <Text>💬 {post.comments_count} टिप्पणियाँ</Text>
    <Text>↗️ {post.shares_count} शेयर</Text>
  </View>

  {/* Action Buttons */}
  <View style={styles.actionButtons}>
    <TouchableOpacity onPress={handleLike}>
      <Icon name={isLiked ? 'heart' : 'heart-outline'} color={isLiked ? 'red' : 'gray'} />
      <Text>पसंद करें</Text>
    </TouchableOpacity>

    <TouchableOpacity onPress={handleComment}>
      <Icon name="comment-outline" />
      <Text>टिप्पणी करें</Text>
    </TouchableOpacity>

    <TouchableOpacity onPress={handleShare}>
      <Icon name="share-outline" />
      <Text>शेयर करें</Text>
    </TouchableOpacity>
  </View>

  {/* Comments Section (collapsible) */}
  {showComments && (
    <FeedComments postId={post.id} comments={post.comments} />
  )}
</FeedPost>
```

**Feed Algorithm (Ranking):**
```python
def get_feed_posts(user_id: str, limit: int = 20, offset: int = 0):
    """
    Feed ranking algorithm:
    1. Recent posts (created in last 7 days)
    2. Trending posts (high engagement in last 24 hours)
    3. Resolved posts (success stories for motivation)
    4. Nearby posts (same district/state)
    """

    # Score formula: recency + engagement + proximity
    query = """
    SELECT
        fp.*,
        u.name, u.phone, u.location,
        (
            -- Recency score (decay over time)
            (1 - EXTRACT(EPOCH FROM (NOW() - fp.created_at)) / 604800) * 0.3 +

            -- Engagement score
            (fp.likes_count * 2 + fp.comments_count * 3 + fp.shares_count * 5) / 100.0 * 0.4 +

            -- Status score (resolved = higher)
            CASE WHEN fp.status = 'resolved' THEN 0.2 ELSE 0.1 END +

            -- Proximity score (same district)
            CASE WHEN fp.location LIKE :user_district THEN 0.1 ELSE 0 END
        ) AS feed_score
    FROM feed_posts fp
    JOIN users u ON fp.user_id = u.id
    WHERE fp.is_public = TRUE
    ORDER BY feed_score DESC, fp.created_at DESC
    LIMIT :limit OFFSET :offset
    """
```

**Privacy Controls:**
```tsx
// When publishing a case to feed
<PublishModal>
  <Text>अपनी शिकायत सार्वजनिक करें?</Text>

  <RadioGroup value={visibility} onChange={setVisibility}>
    <Radio value="public">
      🌍 सार्वजनिक - सभी लोग देख सकते हैं
    </Radio>
    <Radio value="private">
      🔒 निजी - केवल आप देख सकते हैं
    </Radio>
  </RadioGroup>

  <Checkbox checked={showName} onChange={setShowName}>
    मेरा नाम दिखाएं
  </Checkbox>

  <Checkbox checked={showLocation} onChange={setShowLocation}>
    मेरा स्थान दिखाएं
  </Checkbox>

  <Button onPress={handlePublish}>प्रकाशित करें</Button>
</PublishModal>
```

**Navigation Update:**
```
Tab Navigator:
├─ होम (Home) - Quick report + Recent activity
├─ फीड (Feed) - Public grievance feed ⭐ NEW
├─ मेरी शिकायतें (My Reports) - User's cases
├─ सहायता (Help) - FAQ, support
└─ प्रोफाइल (Profile) - Settings
```

**Feed Filters:**
```tsx
<FeedFilters>
  <FilterButton active={filter === 'all'} onPress={() => setFilter('all')}>
    सभी
  </FilterButton>
  <FilterButton active={filter === 'trending'} onPress={() => setFilter('trending')}>
    🔥 ट्रेंडिंग
  </FilterButton>
  <FilterButton active={filter === 'resolved'} onPress={() => setFilter('resolved')}>
    ✅ हल हुआ
  </FilterButton>
  <FilterButton active={filter === 'nearby'} onPress={() => setFilter('nearby')}>
    📍 आस-पास
  </FilterButton>
</FeedFilters>
```

**Moderation:**
```python
# Backend moderation
@router.post("/v1/feed/report")
async def report_post(
    post_id: str,
    reason: str,  # spam, inappropriate, fake, etc.
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Report inappropriate content"""
    # Flag for admin review
    # Auto-hide if multiple reports
    pass
```

**Benefits:**
1. **Community Awareness** - People see common problems in their area
2. **Social Pressure** - Officials see public attention on issues
3. **Success Stories** - Resolved cases motivate others to report
4. **Viral Potential** - Important issues can trend and get media attention
5. **Data for Analysis** - See which issues are most common

**Privacy Considerations:**
- Users choose whether to publish (opt-in, not default)
- Can publish anonymously or with name
- Can delete posts anytime
- Reports flagged as sensitive (personal info, health) are never auto-published

---

## Phase 3: Polish & Optimization (Week 5-6)

### 3.1 Noto Sans Devanagari Font
**Installation:**
```bash
cd mobile
npx expo install expo-font
```

**Download Font:**
- Download from Google Fonts: [Noto Sans Devanagari](https://fonts.google.com/noto/specimen/Noto+Sans+Devanagari)

**Load Font:**
```typescript
// App.tsx
import { useFonts } from 'expo-font';

export default function App() {
  const [fontsLoaded] = useFonts({
    'Noto-Sans-Devanagari': require('./assets/fonts/NotoSansDevanagari-Regular.ttf'),
    'Noto-Sans-Devanagari-Bold': require('./assets/fonts/NotoSansDevanagari-Bold.ttf'),
  });

  if (!fontsLoaded) return <AppLoading />;

  return <AuthProvider>...</AuthProvider>;
}
```

**Update Styles:**
```typescript
// constants/config.ts
export const FONTS = {
  hindi: {
    regular: 'Noto-Sans-Devanagari',
    bold: 'Noto-Sans-Devanagari-Bold',
    size: {
      small: 14,
      medium: 16,
      large: 18,  // Increased from 16
      xlarge: 22,
    }
  }
};
```

---

### 3.2 Audio Compression (Opus Codec)
**Installation:**
```bash
npm install react-native-opus-recorder
```

**Implementation:**
```typescript
// Start recording with compression
await Audio.Recording.createAsync({
  android: {
    extension: '.ogg',
    outputFormat: Audio.RECORDING_OPTION_ANDROID_OUTPUT_FORMAT_OGG,
    audioEncoder: Audio.RECORDING_OPTION_ANDROID_AUDIO_ENCODER_OPUS,
    sampleRate: 16000,
    numberOfChannels: 1,
    bitRate: 16000, // 16kbps - highly compressed
  },
  ios: {
    extension: '.caf',
    audioQuality: Audio.RECORDING_OPTION_IOS_AUDIO_QUALITY_MIN,
    sampleRate: 16000,
    numberOfChannels: 1,
    bitRate: 16000,
  },
});
```

**Benefits:**
- 10MB recording → 1.2MB (8x compression)
- Faster uploads on 2G/3G
- Less data usage for rural users

---

### 3.3 Real-Time Transcription Preview
**Backend API:**
```python
@router.post("/v1/transcription/streaming")
async def stream_transcription(audio_chunk: bytes):
    """Stream audio chunks for real-time transcription"""
    transcript = await openai_whisper.transcribe_chunk(audio_chunk)
    return {"text": transcript, "confidence": 0.92}
```

**Mobile Implementation:**
```typescript
// Send audio chunks every 2 seconds
const onRecordingStatusUpdate = async (status) => {
  if (status.isRecording && status.durationMillis % 2000 === 0) {
    const chunk = await getAudioChunk();
    const transcript = await api.streamTranscription(chunk);
    setLiveTranscript(prev => prev + ' ' + transcript.text);
  }
};
```

---

### 3.4 Volume & Noise Indicators
**Implementation:**
```typescript
// Monitor audio metering
recording.setOnRecordingStatusUpdate((status) => {
  const volume = status.metering || 0;

  if (volume < -40) {
    setWarning({ type: 'VOLUME_LOW', message: 'बहुत धीमी आवाज़' });
  } else if (volume > -10) {
    setWarning({ type: 'VOLUME_HIGH', message: 'बहुत तेज आवाज़' });
  } else if (status.isRecording && backgroundNoise > 0.7) {
    setWarning({ type: 'NOISE', message: 'शोर ज़्यादा है' });
  } else {
    setWarning(null);
  }
});
```

---

### 3.5 Waveform Visualization
**Library:**
```bash
npm install react-native-audio-waveform
```

**Component:**
```tsx
<AudioWaveform
  audioUri={recordingUri}
  waveColor="#3B82F6"
  scrubColor="#EF4444"
  candleWidth={4}
  candleSpace={2}
  onPlaybackStatusUpdate={(status) => {
    setPosition(status.positionMillis);
  }}
/>
```

---

### 3.6 Touch Target Improvements
**Update All Buttons:**
```typescript
// Before (too small):
const styles = StyleSheet.create({
  button: {
    padding: 12,  // 44px touch target
  }
});

// After (minimum 48px):
const styles = StyleSheet.create({
  button: {
    paddingVertical: 16,  // 48px+ touch target
    paddingHorizontal: 20,
    minHeight: 48,
    minWidth: 48,
  }
});
```

**Add Press States:**
```tsx
<TouchableOpacity
  style={({ pressed }) => [
    styles.button,
    pressed && styles.buttonPressed
  ]}
  activeOpacity={0.7}
>
```

---

### 3.7 Regional Language Support
**New File:**
- `/mobile/src/constants/regionalLanguages.ts`

```typescript
export const REGIONAL_LANGUAGES = {
  chhattisgarhi: {
    code: 'cg',
    name: 'छत्तीसगढ़ी',
    translations: {
      'report_problem': 'समस्या बतावव',
      'my_reports': 'मोर शिकायत',
      // ... more translations
    }
  },
  bhojpuri: {
    code: 'bh',
    name: 'भोजपुरी',
    translations: {
      'report_problem': 'समस्या बताईं',
      // ... more translations
    }
  },
  odia: {
    code: 'or',
    name: 'ଓଡ଼ିଆ',
    translations: {
      'report_problem': 'ସମସ୍ୟା ରିପୋର୍ଟ କରନ୍ତୁ',
      // ... more translations
    }
  }
};
```

**Language Selector:**
```tsx
<LanguagePicker
  languages={['hi', 'en', 'cg', 'bh', 'or']}
  selected={language}
  onChange={setLanguage}
/>
```

---

## Database Migrations

### Migration 1: Remove Training Fields
```sql
-- Remove training-related columns from users table
ALTER TABLE users DROP COLUMN IF EXISTS is_first_timer;
ALTER TABLE users DROP COLUMN IF EXISTS training_reports_count;
ALTER TABLE users DROP COLUMN IF EXISTS training_completed;
ALTER TABLE users DROP COLUMN IF EXISTS training_mode_enabled;
```

### Migration 2: Add Timeline Events Table
```sql
CREATE TABLE case_timeline_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    actor VARCHAR(255),
    description_hi TEXT NOT NULL,
    description_en TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_timeline_case_id ON case_timeline_events(case_id);
CREATE INDEX idx_timeline_created_at ON case_timeline_events(created_at DESC);
```

### Migration 3: Add Offline Queue Table
```sql
CREATE TABLE offline_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    action_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    synced_at TIMESTAMP
);

CREATE INDEX idx_offline_queue_user ON offline_queue(user_id);
CREATE INDEX idx_offline_queue_status ON offline_queue(status);
```

---

## Testing Strategy

### Phase 1 Testing
- ✅ Test with MSG91 OTP in production
- ✅ Verify training mode completely removed
- ✅ Tab navigation works on Android & iOS
- ✅ MyDiary screens deleted without crashes
- ✅ All error messages display in Hindi

### Phase 2 Testing
- ✅ Onboarding shows on first login only
- ✅ Offline queue persists across app restarts
- ✅ Push notifications received on Android & iOS
- ✅ Timeline shows all case events
- ✅ Phone number change migrates all reports

### Phase 3 Testing
- ✅ Noto Sans Devanagari renders properly
- ✅ Audio files compressed (< 2MB for 5 min recording)
- ✅ Real-time transcription appears within 2 seconds
- ✅ Volume warnings trigger correctly
- ✅ All touch targets minimum 48x48px
- ✅ Regional language switching works

---

## Rollout Plan

### Week 1-2: Phase 1 (Critical)
- Day 1-2: Remove testing UI, fix VerifyOTP
- Day 3-5: Remove training mode system
- Day 6-9: Implement tab navigation
- Day 10: Delete MyDiary, translate errors

### Week 3-4: Phase 2 (UX)
- Day 11-13: Add onboarding flow
- Day 14-17: Implement offline mode
- Day 18-20: Add push notifications
- Day 21-23: Build timeline view
- Day 24-25: Phone number change feature

### Week 5-6: Phase 3 (Polish)
- Day 26-27: Install Noto Sans font
- Day 28-30: Audio compression & quality indicators
- Day 31-33: Real-time transcription
- Day 34-36: Touch target improvements
- Day 37-40: Regional language support
- Day 41-42: Final testing & bug fixes

---

## Success Metrics

### Phase 1 Completion:
- ✅ 0 hardcoded test credentials in production
- ✅ Training mode references removed from all files
- ✅ Tab navigation accessible on every screen
- ✅ Error messages 100% in Hindi

### Phase 2 Completion:
- ✅ 80%+ users complete onboarding
- ✅ Offline reports successfully queue and sync
- ✅ Push notification open rate > 40%
- ✅ Timeline view reduces "where is my report?" support tickets by 50%

### Phase 3 Completion:
- ✅ Audio file size reduced by 70%
- ✅ Data usage per report < 2MB
- ✅ Touch target accessibility score 95%+
- ✅ Regional language adoption in target states

---

## Risk Mitigation

### Risk 1: Tab Navigation Breaking Flow
**Mitigation:** Keep stack navigation within each tab, test thoroughly on both platforms

### Risk 2: Offline Mode Data Loss
**Mitigation:** Use SQLite for queue persistence, not just AsyncStorage

### Risk 3: Audio Compression Quality Loss
**Mitigation:** Test transcription accuracy with compressed audio, adjust bitrate if needed

### Risk 4: Push Notification Permission Denial
**Mitigation:** Graceful fallback to in-app notifications, explain value before requesting permission

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Set up feature branches** for each phase
3. **Create Jira/GitHub issues** for each task
4. **Assign developers** to phases
5. **Begin Phase 1 implementation** immediately

---

**Document Version:** 1.0
**Last Updated:** January 2025
**Owner:** Product & Engineering Team

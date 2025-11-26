# Real-Time Transcription Usage Guide

## Overview

The Boloo app now includes real-time audio transcription with Hindi-first support, allowing users to see and edit transcriptions while recording.

## Components

### 1. AudioRecorder (Updated)

Located: `/Users/diptendu/boloo app/boloo-app/mobile/src/components/AudioRecorder.tsx`

#### New Features:
- Real-time transcription during recording (updates every 2 seconds)
- Live transcription display with typing indicator
- Word highlighting for newly transcribed text
- Confidence score display
- Edit transcription button after recording stops
- Integration with backend transcription API

#### Props:

```typescript
interface AudioRecorderProps {
  onRecordingComplete?: (uri: string, fileSize: number, transcription?: string) => void;
  maxDurationSeconds?: number;
  autoCompress?: boolean;
  enableTranscription?: boolean;  // NEW: Enable/disable transcription
  apiBaseUrl?: string;            // NEW: Backend API base URL
}
```

#### Usage Example:

```tsx
import { AudioRecorder } from '../components/AudioRecorder';

const MyScreen = () => {
  const handleRecordingComplete = (uri: string, fileSize: number, transcription?: string) => {
    console.log('Audio URI:', uri);
    console.log('File size:', fileSize);
    console.log('Transcription:', transcription);

    // Submit to backend with transcription
    submitComplaint({
      audioUri: uri,
      transcription: transcription,
    });
  };

  return (
    <AudioRecorder
      onRecordingComplete={handleRecordingComplete}
      maxDurationSeconds={300}
      autoCompress={true}
      enableTranscription={true}
      apiBaseUrl="https://api.boloo.com"
    />
  );
};
```

### 2. TranscriptionEditor (New)

Located: `/Users/diptendu/boloo app/boloo-app/mobile/src/components/TranscriptionEditor.tsx`

#### Features:
- Full-screen modal editor
- Hindi keyboard support
- Real-time word and character count
- Auto-save to AsyncStorage every 3 seconds
- Unsaved changes indicator
- Draft restoration on reopen

#### Props:

```typescript
interface TranscriptionEditorProps {
  visible: boolean;
  initialText: string;
  recordingId?: string;
  onSave: (text: string) => void;
  onCancel: () => void;
  language?: 'hi' | 'en';
}
```

#### Usage Example:

```tsx
import { TranscriptionEditor } from '../components/TranscriptionEditor';

const MyScreen = () => {
  const [showEditor, setShowEditor] = useState(false);
  const [transcription, setTranscription] = useState('');

  const handleSave = (editedText: string) => {
    setTranscription(editedText);
    setShowEditor(false);
    console.log('Saved transcription:', editedText);
  };

  return (
    <>
      <Button onPress={() => setShowEditor(true)}>
        Edit Transcription
      </Button>

      <TranscriptionEditor
        visible={showEditor}
        initialText={transcription}
        recordingId="recording-123"
        onSave={handleSave}
        onCancel={() => setShowEditor(false)}
        language="hi"
      />
    </>
  );
};
```

## Backend API Integration

### Endpoint: `/v1/ai/transcribe`

The AudioRecorder sends audio chunks to this endpoint for transcription.

#### Request Format:

```json
{
  "audio": "base64_encoded_audio_data",
  "language": "hi",
  "partial": true
}
```

#### Expected Response:

```json
{
  "text": "हमारे गांव में पानी की समस्या है।",
  "confidence": 0.92,
  "language": "hi"
}
```

#### Backend Implementation Example:

```typescript
app.post('/v1/ai/transcribe', async (req, res) => {
  const { audio, language, partial } = req.body;

  try {
    // Decode base64 audio
    const audioBuffer = Buffer.from(audio, 'base64');

    // Call your transcription service (e.g., Google Speech-to-Text, Whisper, etc.)
    const transcription = await transcriptionService.transcribe({
      audio: audioBuffer,
      language: language || 'hi',
      streaming: partial,
    });

    res.json({
      text: transcription.text,
      confidence: transcription.confidence,
      language: transcription.language,
    });
  } catch (error) {
    console.error('Transcription error:', error);
    res.status(500).json({ error: 'Transcription failed' });
  }
});
```

## UI Flow

### During Recording:

```
┌─────────────────────────────────────┐
│ Recording...          00:45 / 05:00 │
│ Estimated Size: 234 KB              │
├─────────────────────────────────────┤
│ Live Transcription    ● ● ●  92%    │
│ ┌─────────────────────────────────┐ │
│ │ हमारे गांव में पानी की समस्या है। │ │
│ │ नल में पानी नहीं आता...          │ │
│ │ [new words highlighted]          │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ [Pause]  [Stop]                     │
└─────────────────────────────────────┘
```

### After Recording:

```
┌─────────────────────────────────────┐
│ Ready to Record                     │
├─────────────────────────────────────┤
│ Live Transcription                  │
│ ┌─────────────────────────────────┐ │
│ │ हमारे गांव में पानी की समस्या है। │ │
│ │ नल में पानी नहीं आता है।         │ │
│ │ सुबह से शाम तक पानी नहीं मिलता।  │ │
│ └─────────────────────────────────┘ │
│ ✏️ Edit Transcription / संपादित करें │
├─────────────────────────────────────┤
│ [Start Recording]                   │
└─────────────────────────────────────┘
```

### Transcription Editor:

```
┌─────────────────────────────────────┐
│ Cancel  ट्रांसक्रिप्शन संपादित करें Save │
│         Just now                    │
├─────────────────────────────────────┤
│ Words: 42  │  Characters: 256  │ ●  │
├─────────────────────────────────────┤
│                                     │
│ हमारे गांव में पानी की समस्या है।    │
│ नल में पानी नहीं आता है।             │
│ सुबह से शाम तक पानी नहीं मिलता।      │
│ [cursor]                            │
│                                     │
├─────────────────────────────────────┤
│ 💡 हिन्दी टाइप करने के लिए अपना      │
│    कीबोर्ड स्विच करें                │
└─────────────────────────────────────┘
```

## Features Implementation

### 1. Real-Time Transcription
- Triggered every 2 seconds during recording
- Sends audio chunk to backend API
- Updates UI with new transcription text
- Highlights newly added words for 3 seconds

### 2. Word Highlighting
- New words are highlighted in yellow/orange
- Highlights fade after 3 seconds
- Helps users track transcription progress

### 3. Auto-Save (TranscriptionEditor)
- Saves to AsyncStorage every 3 seconds
- Persists across app restarts
- Shows "Unsaved" indicator when changes exist
- Displays last saved time

### 4. Hindi Keyboard Support
- Keyboard hint at bottom of editor
- Native OS keyboard switching
- Full Unicode support for Devanagari script

### 5. Confidence Score
- Displayed as percentage (e.g., "92% confident")
- Helps users identify potential transcription errors
- Color-coded: green for high confidence

## Optimization for Rural Networks

### Low-Bandwidth Features:
1. Audio chunks sent every 2 seconds (configurable)
2. Throttling to prevent too-frequent API calls
3. Base64 encoding for reliable transfer
4. Automatic compression before upload
5. Error handling with graceful degradation

### Configuration:

```typescript
// Adjust transcription frequency for different network conditions
const TRANSCRIPTION_INTERVAL = 2000; // 2 seconds for good networks
const TRANSCRIPTION_INTERVAL_SLOW = 5000; // 5 seconds for 2G networks

// In AudioRecorder component
if (enableTranscription && recordingState.duration % interval === 0) {
  transcribeAudioChunk();
}
```

## Error Handling

### Network Failures:
- Silent failure during recording (doesn't interrupt)
- User can still edit transcription manually after recording
- Logs errors for debugging

### API Errors:
- Continues recording even if transcription fails
- Shows placeholder text when no transcription available
- User always has option to manually edit

## Testing

### Test Backend Integration:

```bash
# Test transcription endpoint
curl -X POST http://localhost:3000/v1/ai/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "audio": "BASE64_ENCODED_AUDIO",
    "language": "hi",
    "partial": true
  }'
```

### Test Frontend:

1. Start recording
2. Speak in Hindi
3. Verify transcription appears after 2 seconds
4. Check word highlighting
5. Stop recording
6. Click "Edit Transcription"
7. Verify editor opens with correct text
8. Edit text and save
9. Verify changes persist

## Dependencies

Required packages (already installed):
- `expo-av` - Audio recording
- `expo-file-system` - File operations
- `@react-native-async-storage/async-storage` - Local storage

## Notes

1. The hooks (pre-task, post-edit, post-task) failed due to Node.js version mismatch with better-sqlite3. This is a claude-flow coordination issue and doesn't affect the actual implementation.

2. Backend API endpoint (`/v1/ai/transcribe`) needs to be implemented on the server side.

3. For production, consider using a streaming API for real-time transcription instead of chunked requests.

4. Test thoroughly with different Hindi accents and rural dialects.

5. Consider adding offline mode where transcription happens after recording when network is available.

## Future Enhancements

1. Offline transcription using on-device ML models
2. Multiple language support (not just Hindi)
3. Speaker diarization for group recordings
4. Automatic punctuation insertion
5. Voice activity detection to pause transcription during silence
6. Custom vocabulary for government/legal terms

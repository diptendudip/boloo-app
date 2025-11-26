# Backend API Integration for Transcription

## Overview

This document describes the backend API endpoint required for real-time audio transcription in the Boloo mobile app.

## Endpoint Specification

### POST `/v1/ai/transcribe`

Transcribes audio data to text, supporting Hindi language with partial/streaming transcription.

#### Request

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <token> (optional, based on your auth)
```

**Body:**
```json
{
  "audio": "base64_encoded_audio_data",
  "language": "hi",
  "partial": true
}
```

**Parameters:**
- `audio` (string, required): Base64-encoded audio data
- `language` (string, optional): Language code (default: "hi" for Hindi)
- `partial` (boolean, optional): Whether this is a partial transcription during recording

#### Response

**Success (200 OK):**
```json
{
  "text": "हमारे गांव में पानी की समस्या है।",
  "confidence": 0.92,
  "language": "hi"
}
```

**Parameters:**
- `text` (string): Transcribed text
- `confidence` (number): Confidence score (0-1)
- `language` (string): Detected/used language code

**Error (500 Internal Server Error):**
```json
{
  "error": "Transcription failed",
  "message": "Detailed error message"
}
```

## Implementation Examples

### Node.js with Express and Google Speech-to-Text

```typescript
import express from 'express';
import { SpeechClient } from '@google-cloud/speech';

const app = express();
const speechClient = new SpeechClient();

app.post('/v1/ai/transcribe', async (req, res) => {
  try {
    const { audio, language = 'hi', partial = false } = req.body;

    // Decode base64 audio
    const audioBuffer = Buffer.from(audio, 'base64');

    // Configure request
    const request = {
      audio: {
        content: audioBuffer.toString('base64'),
      },
      config: {
        encoding: 'LINEAR16',
        sampleRateHertz: 44100,
        languageCode: language === 'hi' ? 'hi-IN' : 'en-IN',
        enableAutomaticPunctuation: true,
        model: 'latest_long',
      },
    };

    // Perform transcription
    const [response] = await speechClient.recognize(request);
    const transcription = response.results
      .map(result => result.alternatives[0])
      .filter(alt => alt.transcript)
      .map(alt => alt.transcript)
      .join('\n');

    const confidence = response.results[0]?.alternatives[0]?.confidence || 0;

    res.json({
      text: transcription,
      confidence: confidence,
      language: language,
    });
  } catch (error) {
    console.error('Transcription error:', error);
    res.status(500).json({
      error: 'Transcription failed',
      message: error.message,
    });
  }
});
```

### Node.js with OpenAI Whisper API

```typescript
import express from 'express';
import OpenAI from 'openai';
import fs from 'fs';
import path from 'path';

const app = express();
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

app.post('/v1/ai/transcribe', async (req, res) => {
  try {
    const { audio, language = 'hi', partial = false } = req.body;

    // Decode base64 audio and save temporarily
    const audioBuffer = Buffer.from(audio, 'base64');
    const tempFile = path.join('/tmp', `audio_${Date.now()}.wav`);
    fs.writeFileSync(tempFile, audioBuffer);

    // Transcribe with Whisper
    const transcription = await openai.audio.transcriptions.create({
      file: fs.createReadStream(tempFile),
      model: 'whisper-1',
      language: language,
      response_format: 'verbose_json',
    });

    // Clean up temp file
    fs.unlinkSync(tempFile);

    res.json({
      text: transcription.text,
      confidence: 0.95, // Whisper doesn't provide confidence, using default
      language: transcription.language,
    });
  } catch (error) {
    console.error('Transcription error:', error);
    res.status(500).json({
      error: 'Transcription failed',
      message: error.message,
    });
  }
});
```

### Python with FastAPI and Whisper

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64
import tempfile
import os
import whisper

app = FastAPI()
model = whisper.load_model("base")

class TranscriptionRequest(BaseModel):
    audio: str
    language: str = "hi"
    partial: bool = False

@app.post("/v1/ai/transcribe")
async def transcribe_audio(request: TranscriptionRequest):
    try:
        # Decode base64 audio
        audio_data = base64.b64decode(request.audio)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name

        # Transcribe
        result = model.transcribe(
            temp_path,
            language=request.language,
            task="transcribe"
        )

        # Clean up
        os.unlink(temp_path)

        return {
            "text": result["text"],
            "confidence": 0.95,  # Whisper doesn't provide per-segment confidence
            "language": request.language
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Testing

### cURL Example

```bash
# Create a test with base64 audio
curl -X POST http://localhost:3000/v1/ai/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "audio": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",
    "language": "hi",
    "partial": true
  }'
```

### Postman/Insomnia

1. Method: POST
2. URL: `http://your-api.com/v1/ai/transcribe`
3. Headers:
   - Content-Type: application/json
4. Body (JSON):
```json
{
  "audio": "base64_encoded_audio_here",
  "language": "hi",
  "partial": true
}
```

## Performance Considerations

### For Rural Networks:

1. **Audio Chunk Size**: Keep chunks small (2-5 seconds max)
2. **Compression**: Audio is already compressed in the mobile app
3. **Timeout**: Set generous timeout (30+ seconds) for slow connections
4. **Caching**: Cache transcriptions on server to avoid re-processing
5. **Batching**: Consider batching multiple chunks if network is unstable

### Example with Caching:

```typescript
import NodeCache from 'node-cache';

const transcriptionCache = new NodeCache({ stdTTL: 3600 }); // 1 hour

app.post('/v1/ai/transcribe', async (req, res) => {
  const { audio, language, partial } = req.body;

  // Create cache key from audio hash
  const audioHash = crypto
    .createHash('md5')
    .update(audio)
    .digest('hex');

  // Check cache
  const cached = transcriptionCache.get(audioHash);
  if (cached) {
    return res.json(cached);
  }

  // Transcribe...
  const result = await transcribe(audio, language);

  // Cache result
  transcriptionCache.set(audioHash, result);

  res.json(result);
});
```

## Security Considerations

1. **Rate Limiting**: Implement rate limiting to prevent abuse
2. **Authentication**: Require authentication for API access
3. **Input Validation**: Validate audio data size and format
4. **CORS**: Configure CORS properly for mobile app access

### Example with Rate Limiting:

```typescript
import rateLimit from 'express-rate-limit';

const transcriptionLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  message: 'Too many transcription requests',
});

app.post('/v1/ai/transcribe', transcriptionLimiter, async (req, res) => {
  // Transcription logic...
});
```

## Cost Optimization

### Google Speech-to-Text Pricing:
- First 60 minutes/month: Free
- Standard recognition: $0.006 per 15 seconds
- Streaming: $0.009 per 15 seconds

### OpenAI Whisper Pricing:
- $0.006 per minute (rounded to nearest second)

### Cost-Saving Strategies:

1. **Chunk Optimization**: Only send audio every 2-5 seconds
2. **Silence Detection**: Don't send silent audio chunks
3. **Local Caching**: Cache results to avoid re-processing
4. **Hybrid Approach**: Use free tier first, then paid services
5. **On-Device Transcription**: Consider local ML models for basic transcription

## Monitoring

### Metrics to Track:

1. **Latency**: Time from request to response
2. **Accuracy**: Transcription quality (requires manual review)
3. **Error Rate**: Failed transcription attempts
4. **Usage**: Number of requests per day/user
5. **Cost**: Transcription service costs

### Example Logging:

```typescript
app.post('/v1/ai/transcribe', async (req, res) => {
  const startTime = Date.now();

  try {
    const result = await transcribe(req.body.audio);

    // Log metrics
    console.log({
      event: 'transcription_success',
      duration: Date.now() - startTime,
      language: req.body.language,
      textLength: result.text.length,
      confidence: result.confidence,
    });

    res.json(result);
  } catch (error) {
    console.error({
      event: 'transcription_error',
      duration: Date.now() - startTime,
      error: error.message,
    });

    res.status(500).json({ error: 'Transcription failed' });
  }
});
```

## Deployment

### Recommended Services:

1. **Vercel/Netlify**: For Node.js serverless functions
2. **AWS Lambda**: Scalable serverless option
3. **Google Cloud Run**: Container-based deployment
4. **Railway/Render**: Simple deployment with auto-scaling

### Environment Variables:

```bash
# .env file
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_CLOUD_CREDENTIALS=path/to/credentials.json
OPENAI_API_KEY=sk-...
API_BASE_URL=https://api.boloo.com
```

## Troubleshooting

### Common Issues:

1. **Large Audio Files**: Implement chunking on client side
2. **Timeout Errors**: Increase server timeout limits
3. **Low Accuracy**: Improve audio quality, reduce background noise
4. **Language Detection**: Explicitly set language instead of auto-detect
5. **Memory Issues**: Process audio in streams instead of loading fully

### Debug Mode:

```typescript
app.post('/v1/ai/transcribe', async (req, res) => {
  const debug = req.query.debug === 'true';

  if (debug) {
    console.log('Audio size:', Buffer.from(req.body.audio, 'base64').length);
    console.log('Language:', req.body.language);
    console.log('Partial:', req.body.partial);
  }

  // Process...
});
```

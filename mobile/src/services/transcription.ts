/**
 * Transcription Service - Real Voice Recording API
 *
 * Uploads audio and calls backend for:
 * 1. Speech-to-Text transcription (Azure)
 * 2. LLM classification (Claude)
 */

import axios, { AxiosError } from 'axios';
import { API_URL } from '../constants/config';
import type { TriageResult } from '../types/triage';

export interface TranscriptionResult {
  success: boolean;
  transcript: string;
  language_detected: string;
  transcript_confidence: number;
  triage_result?: TriageResult;
  error?: string;
}

class TranscriptionService {
  private baseURL: string;

  constructor() {
    this.baseURL = `${API_URL}/v1/transcription`;
  }

  /**
   * Upload audio and get transcription + classification
   * This is the main endpoint for voice recording flow
   */
  async transcribeAndClassify(
    audioUri: string,
    locationHint?: string
  ): Promise<TranscriptionResult> {
    try {
      console.log('[TranscriptionService] Starting upload:', audioUri);

      // Create form data
      const formData = new FormData();

      // Add audio file
      const audioFile = {
        uri: audioUri,
        type: 'audio/m4a',
        name: 'recording.m4a',
      } as any;

      formData.append('audio', audioFile);

      // Add optional location hint
      if (locationHint) {
        formData.append('location_hint', locationHint);
      }

      // Add language preference
      formData.append('language', 'hi-IN'); // Hindi by default

      console.log('[TranscriptionService] Uploading to:', `${this.baseURL}/transcribe-and-classify`);

      // Upload and process
      const response = await axios.post(
        `${this.baseURL}/transcribe-and-classify`,
        formData,
        {
          timeout: 60000, // 60 second timeout for transcription
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      console.log('[TranscriptionService] Response:', response.data);

      if (!response.data.success) {
        throw new Error(response.data.error || 'Transcription failed');
      }

      return {
        success: true,
        transcript: response.data.transcript,
        language_detected: response.data.language_detected,
        transcript_confidence: response.data.transcript_confidence,
        triage_result: response.data.triage_result
          ? {
              intent: response.data.triage_result.intent,
              confidence: response.data.triage_result.confidence,
              confidence_level: response.data.triage_result.confidence_level,
              reasoning: response.data.triage_result.reasoning,
              suggested_issue_type: response.data.triage_result.suggested_issue_type,
              transcript_summary: response.data.triage_result.transcript_summary,
            }
          : undefined,
        error: response.data.error,
      };
    } catch (error) {
      console.error('[TranscriptionService] Error:', error);

      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError<{ detail?: string }>;

        if (axiosError.code === 'ECONNABORTED') {
          throw new Error('अनुरोध समय समाप्त (Upload timed out - audio file too large?)');
        }

        if (axiosError.response) {
          const status = axiosError.response.status;
          const detail = axiosError.response.data?.detail;

          if (status === 400) {
            throw new Error(detail || 'अमान्य फ़ाइल (Invalid audio file)');
          } else if (status === 413) {
            throw new Error('फ़ाइल बहुत बड़ी है (Audio file too large)');
          } else if (status >= 500) {
            throw new Error('सर्वर त्रुटि (Server error)');
          }

          throw new Error(detail || 'अपलोड विफल (Upload failed)');
        } else if (axiosError.request) {
          throw new Error('नेटवर्क त्रुटि (Network error - check backend connection)');
        }
      }

      throw error;
    }
  }

  /**
   * Just transcribe audio without classification
   */
  async transcribeOnly(
    audioUri: string,
    language: string = 'hi-IN'
  ): Promise<{ transcript: string; confidence: number; language_detected: string }> {
    try {
      const formData = new FormData();

      const audioFile = {
        uri: audioUri,
        type: 'audio/m4a',
        name: 'recording.m4a',
      } as any;

      formData.append('audio', audioFile);
      formData.append('language', language);

      const response = await axios.post(`${this.baseURL}/transcribe`, formData, {
        timeout: 60000,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (!response.data.success) {
        throw new Error(response.data.error || 'Transcription failed');
      }

      return {
        transcript: response.data.transcript,
        confidence: response.data.confidence,
        language_detected: response.data.language_detected,
      };
    } catch (error) {
      console.error('[TranscriptionService] Transcribe-only error:', error);
      throw error;
    }
  }

  /**
   * Get supported languages
   */
  async getSupportedLanguages(): Promise<
    Array<{
      code: string;
      name: string;
      native_name: string;
      default: boolean;
    }>
  > {
    try {
      const response = await axios.get(`${this.baseURL}/languages`);
      return response.data.languages;
    } catch (error) {
      console.error('[TranscriptionService] Failed to get languages:', error);
      return [
        {
          code: 'hi-IN',
          name: 'Hindi (India)',
          native_name: 'हिन्दी',
          default: true,
        },
      ];
    }
  }
}

// Export singleton instance
export const transcriptionService = new TranscriptionService();

/**
 * Chat Service - ChatGPT-like conversational interface
 *
 * Handles communication with the new chat endpoints:
 * - Start conversation with greeting
 * - Process chat turns (text/voice)
 * - Get conversation summary
 * - Submit reports
 */

import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL } from '../constants/config';
import { getUserId } from '../utils/apiAuth';

// Storage key for auth token (must match authStorage.ts)
const AUTH_TOKEN_KEY = '@boloo_auth_token';

export interface ChatStartResponse {
  success: boolean;
  conversation_id: string;
  greeting_hi: string;
  greeting_en: string;
  in_training_mode: boolean;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface ChatTurnResponse {
  success: boolean;
  conversation_id: string;
  turn_number: number;
  user_message: string;
  language_detected: string;
  ai_response_hi: string;  // AUTHORITATIVE - use this for display
  ai_response_en: string;
  completeness_score: number;
  is_complete: boolean;
  collected_fields: string[];  // Field names
  missing_fields: any[];
  extracted_data: Record<string, any>;  // ACTUAL VALUES from user
  should_continue: boolean;
  ready_for_submission: boolean;
  // NEW: UX Enhancement flags
  show_submit_button?: boolean;  // Show submit button immediately
  show_skip_button?: boolean;    // Allow skipping this question
  preview_card?: {               // Preview of what will be submitted
    location?: string;
    issue_description?: string;
    reporter_name?: string;
    phone?: string;
    actions_taken?: string;
  };
  error?: string;
}

export interface ChatSummaryResponse {
  success: boolean;
  conversation_id: string;
  summary_hi: string;  // Keep for backwards compatibility
  summary_en: string;  // Keep for backwards compatibility
  narrative_summary_hi?: string;  // NEW - Journalist-style narrative in Hindi
  narrative_summary_en?: string;  // NEW - Journalist-style narrative in English
  completeness_score: number;
  collected_fields: string[];
  missing_fields: any[];
  extracted_data: Record<string, any>;  // ACTUAL VALUES for display
  detected_taxonomy?: any;
}

export interface ChatSubmitResponse {
  success: boolean;
  case_id?: string;
  submitted_to_moderator: boolean;
  training_progress?: any;
  message_hi: string;
  message_en: string;
}

class ChatService {
  private baseURL: string;

  constructor() {
    this.baseURL = `${API_BASE_URL}/v1/chat`;
  }

  /**
   * Start a new chat conversation
   */
  async startConversation(userId: string, language: string = 'hi'): Promise<ChatStartResponse> {
    try {
      // Get Bearer token for production authentication
      const token = await AsyncStorage.getItem(AUTH_TOKEN_KEY);
      const headers: Record<string, string> = {};

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      } else {
        console.warn('[ChatService] No auth token found for start - request may fail');
      }

      const response = await axios.post(
        `${this.baseURL}/start`,
        null,
        {
          params: { user_id: userId, language },
          headers
        }
      );
      return response.data;
    } catch (error) {
      console.error('[ChatService] Error starting conversation:', error);
      throw error;
    }
  }

  /**
   * Send a text message in the chat
   */
  async sendTextMessage(
    conversationId: string,
    userId: string,
    message: string,
    language: string = 'hi-IN'
  ): Promise<ChatTurnResponse> {
    try {
      const formData = new FormData();
      formData.append('conversation_id', conversationId);
      formData.append('user_id', userId);
      formData.append('text_message', message);
      formData.append('language', language);

      // Get Bearer token for production authentication
      const token = await AsyncStorage.getItem(AUTH_TOKEN_KEY);
      const headers: Record<string, string> = {
        'Content-Type': 'multipart/form-data',
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      } else {
        console.warn('[ChatService] No auth token found - request may fail');
      }

      const response = await axios.post(`${this.baseURL}/turn`, formData, {
        headers,
      });

      return response.data;
    } catch (error) {
      console.error('[ChatService] Error sending text message:', error);
      throw error;
    }
  }

  /**
   * Send a voice recording in the chat
   */
  async sendVoiceMessage(
    conversationId: string,
    userId: string,
    audioUri: string,
    language: string = 'hi-IN'
  ): Promise<ChatTurnResponse> {
    try {
      const formData = new FormData();
      formData.append('conversation_id', conversationId);
      formData.append('user_id', userId);
      formData.append('language', language);

      // Add audio file
      const filename = audioUri.split('/').pop() || 'recording.m4a';
      formData.append('audio', {
        uri: audioUri,
        name: filename,
        type: 'audio/m4a',
      } as any);

      // Get Bearer token for production authentication
      const token = await AsyncStorage.getItem(AUTH_TOKEN_KEY);
      const headers: Record<string, string> = {
        'Content-Type': 'multipart/form-data',
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      } else {
        console.warn('[ChatService] No auth token found - request may fail');
      }

      const response = await axios.post(`${this.baseURL}/turn`, formData, {
        headers,
      });

      return response.data;
    } catch (error) {
      console.error('[ChatService] Error sending voice message:', error);
      throw error;
    }
  }

  /**
   * Get conversation summary before submission
   */
  async getConversationSummary(
    conversationId: string,
    userId: string
  ): Promise<ChatSummaryResponse> {
    try {
      // Get Bearer token for production authentication
      const token = await AsyncStorage.getItem(AUTH_TOKEN_KEY);
      const headers: Record<string, string> = {};

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      } else {
        console.warn('[ChatService] No auth token found for summary - request may fail');
      }

      const response = await axios.get(
        `${this.baseURL}/${conversationId}/summary`,
        {
          params: { user_id: userId },
          headers
        }
      );
      return response.data;
    } catch (error) {
      console.error('[ChatService] Error getting summary:', error);
      throw error;
    }
  }

  /**
   * Submit the conversation as a report
   */
  async submitConversation(
    conversationId: string,
    userId: string
  ): Promise<ChatSubmitResponse> {
    try {
      // Get Bearer token for production authentication
      const token = await AsyncStorage.getItem(AUTH_TOKEN_KEY);
      const headers: Record<string, string> = {};

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      } else {
        console.warn('[ChatService] No auth token found for submit - request may fail');
      }

      const response = await axios.post(
        `${this.baseURL}/${conversationId}/submit`,
        null,
        {
          params: {
            user_id: userId,
            conversation_id: conversationId
          },
          headers
        }
      );
      return response.data;
    } catch (error) {
      console.error('[ChatService] Error submitting conversation:', error);
      throw error;
    }
  }
}

export const chatService = new ChatService();

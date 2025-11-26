/**
 * Triage Service
 *
 * API client for intent classification and triage functionality.
 * Handles API calls with retry logic, caching, and error handling.
 */

import axios, { AxiosError } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL } from '../constants/config';
import type {
  TriageRequest,
  TriageResponse,
  TriageResult,
  TriageHistoryItem,
} from '../types/triage';

const TRIAGE_HISTORY_KEY = 'boloo:triage_history';
const MAX_HISTORY_ITEMS = 50;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

class TriageService {
  private baseURL: string;
  private cache: Map<string, { result: TriageResult; timestamp: number }> = new Map();

  constructor() {
    this.baseURL = `${API_URL}/v1/cases`;
  }

  /**
   * Classify intent from voice transcript
   */
  async classifyIntent(request: TriageRequest): Promise<TriageResult> {
    try {
      // Check cache first
      const cacheKey = this.getCacheKey(request);
      const cached = this.getFromCache(cacheKey);
      if (cached) {
        console.log('[TriageService] Returning cached result');
        return cached;
      }

      console.log('[TriageService] Calling triage API');
      const response = await axios.post<TriageResponse>(
        `${this.baseURL}/triage`,
        request,
        {
          timeout: 15000, // 15 second timeout
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.data.success || !response.data.result) {
        throw new Error(response.data.error || 'Triage classification failed');
      }

      const result = response.data.result;

      // Cache the result
      this.addToCache(cacheKey, result);

      // Save to history
      await this.saveToHistory({
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        transcript: request.transcript_text,
        result,
      });

      return result;
    } catch (error) {
      console.error('[TriageService] Classification error:', error);

      // TESTING MODE: Return dummy classification if network fails
      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError<{ detail?: string }>;

        // If network error, use dummy classification for testing
        if (axiosError.request && !axiosError.response) {
          console.log('[TriageService] TESTING MODE: Using dummy classification');
          return this.getDummyClassification(request.transcript_text);
        }

        if (axiosError.code === 'ECONNABORTED') {
          throw new Error('अनुरोध समय समाप्त हो गया (Request timed out)');
        }

        if (axiosError.response) {
          const status = axiosError.response.status;
          const detail = axiosError.response.data?.detail;

          if (status === 400) {
            throw new Error(detail || 'अमान्य अनुरोध (Invalid request)');
          } else if (status === 429) {
            throw new Error('बहुत सारे अनुरोध। कृपया बाद में प्रयास करें (Too many requests)');
          } else if (status >= 500) {
            throw new Error('सर्वर त्रुटि। कृपया बाद में प्रयास करें (Server error)');
          }
        }
      }

      throw new Error('वर्गीकरण विफल हो गया (Classification failed)');
    }
  }

  /**
   * Generate dummy classification for testing (offline mode)
   */
  private getDummyClassification(transcript: string): TriageResult {
    const text = transcript.toLowerCase();

    // Simple keyword-based classification for testing
    let intent: 'grievance' | 'community' | 'personal' = 'grievance';
    let confidence = 0.85;
    let reasoning = '';

    if (
      text.includes('पानी') ||
      text.includes('water') ||
      text.includes('सड़क') ||
      text.includes('road') ||
      text.includes('बिजली') ||
      text.includes('electricity') ||
      text.includes('समस्या') ||
      text.includes('problem')
    ) {
      intent = 'grievance';
      confidence = 0.88;
      reasoning = '🧪 TESTING MODE: Detected civic infrastructure keywords. Classified as grievance.';
    } else if (
      text.includes('मीटिंग') ||
      text.includes('meeting') ||
      text.includes('इवेंट') ||
      text.includes('event') ||
      text.includes('कार्यक्रम') ||
      text.includes('program')
    ) {
      intent = 'community';
      confidence = 0.82;
      reasoning = '🧪 TESTING MODE: Detected community/event keywords. Classified as community.';
    } else if (
      text.includes('याद') ||
      text.includes('reminder') ||
      text.includes('नोट') ||
      text.includes('note') ||
      text.includes('डायरी') ||
      text.includes('diary')
    ) {
      intent = 'personal';
      confidence = 0.90;
      reasoning = '🧪 TESTING MODE: Detected personal/reminder keywords. Classified as personal.';
    } else {
      // Default fallback
      intent = 'grievance';
      confidence = 0.75;
      reasoning = '🧪 TESTING MODE: No specific keywords detected. Defaulting to grievance.';
    }

    return {
      intent,
      confidence,
      confidence_level: confidence > 0.8 ? 'high' : confidence > 0.6 ? 'medium' : 'low',
      reasoning,
      suggested_issue_type: intent === 'grievance' ? 'infrastructure' : undefined,
      transcript_summary: `Testing mode summary of: ${transcript.substring(0, 100)}`,
    };
  }

  /**
   * Classify with retry logic for reliability
   */
  async classifyWithRetry(
    request: TriageRequest,
    maxRetries: number = 2
  ): Promise<TriageResult> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await this.classifyIntent(request);
      } catch (error) {
        lastError = error as Error;
        console.log(`[TriageService] Attempt ${attempt + 1} failed, retrying...`);

        if (attempt < maxRetries) {
          // Exponential backoff
          await this.delay(Math.pow(2, attempt) * 1000);
        }
      }
    }

    throw lastError || new Error('Classification failed after retries');
  }

  /**
   * Get triage history from local storage
   */
  async getHistory(): Promise<TriageHistoryItem[]> {
    try {
      const json = await AsyncStorage.getItem(TRIAGE_HISTORY_KEY);
      return json ? JSON.parse(json) : [];
    } catch (error) {
      console.error('[TriageService] Error loading history:', error);
      return [];
    }
  }

  /**
   * Save triage result to history
   */
  private async saveToHistory(item: TriageHistoryItem): Promise<void> {
    try {
      const history = await this.getHistory();
      history.unshift(item);

      // Keep only recent items
      const trimmed = history.slice(0, MAX_HISTORY_ITEMS);

      await AsyncStorage.setItem(TRIAGE_HISTORY_KEY, JSON.stringify(trimmed));
    } catch (error) {
      console.error('[TriageService] Error saving history:', error);
    }
  }

  /**
   * Update history item with user action
   */
  async updateHistoryItem(
    id: string,
    updates: Partial<Pick<TriageHistoryItem, 'user_action' | 'final_intent'>>
  ): Promise<void> {
    try {
      const history = await this.getHistory();
      const index = history.findIndex((item) => item.id === id);

      if (index >= 0) {
        history[index] = { ...history[index], ...updates };
        await AsyncStorage.setItem(TRIAGE_HISTORY_KEY, JSON.stringify(history));
      }
    } catch (error) {
      console.error('[TriageService] Error updating history:', error);
    }
  }

  /**
   * Clear triage history
   */
  async clearHistory(): Promise<void> {
    try {
      await AsyncStorage.removeItem(TRIAGE_HISTORY_KEY);
      console.log('[TriageService] History cleared');
    } catch (error) {
      console.error('[TriageService] Error clearing history:', error);
    }
  }

  /**
   * Get cache key for request
   */
  private getCacheKey(request: TriageRequest): string {
    return `${request.transcript_text.substring(0, 50)}_${request.location_hint || ''}`;
  }

  /**
   * Get result from cache if valid
   */
  private getFromCache(key: string): TriageResult | null {
    const cached = this.cache.get(key);
    if (!cached) return null;

    const age = Date.now() - cached.timestamp;
    if (age > CACHE_DURATION) {
      this.cache.delete(key);
      return null;
    }

    return cached.result;
  }

  /**
   * Add result to cache
   */
  private addToCache(key: string, result: TriageResult): void {
    this.cache.set(key, {
      result,
      timestamp: Date.now(),
    });

    // Prevent cache from growing too large
    if (this.cache.size > 20) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }
  }

  /**
   * Delay helper for retry logic
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Clear all caches
   */
  clearCache(): void {
    this.cache.clear();
    console.log('[TriageService] Cache cleared');
  }
}

// Export singleton instance
export const triageService = new TriageService();

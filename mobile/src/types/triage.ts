/**
 * TypeScript type definitions for triage functionality.
 *
 * Defines interfaces for triage classification, results, and API contracts.
 */

export type CaseIntent = 'grievance' | 'community' | 'personal' | 'uncertain';

export type ConfidenceLevel = 'high' | 'medium' | 'low';

export interface TriageResult {
  intent: CaseIntent;
  confidence: number; // 0.0 to 1.0
  confidence_level: ConfidenceLevel;
  reasoning: string;
  suggested_issue_type?: string; // For grievances only
  metadata?: {
    model: string;
    tokens_used: number;
    transcript_length: number;
  };
}

export interface TriageRequest {
  transcript_text: string;
  audio_duration?: number;
  location_hint?: string;
  user_context?: {
    previous_intents?: CaseIntent[];
    location?: string;
    language_preference?: string;
  };
}

export interface TriageResponse {
  success: boolean;
  result?: TriageResult;
  error?: string;
  timestamp: string;
}

export interface TriageState {
  loading: boolean;
  result: TriageResult | null;
  error: string | null;
  visible: boolean;
}

// For storing triage history locally
export interface TriageHistoryItem {
  id: string;
  timestamp: string;
  transcript: string;
  result: TriageResult;
  user_action?: 'accepted' | 'overridden' | 'dismissed';
  final_intent?: CaseIntent;
}

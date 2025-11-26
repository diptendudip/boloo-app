/**
 * TypeScript type definitions for "Agla Kya Hoka" (Next Steps) functionality.
 *
 * Defines interfaces for SLA tracking, responsible entities, and escalation paths.
 */

export type EntityType =
  | 'GRAM_PANCHAYAT'
  | 'BDO'
  | 'DISTRICT_OFFICE'
  | 'STATE_OFFICE';

export type CaseStatus =
  | 'OPEN'
  | 'IN_PROGRESS'
  | 'WAITING_INFO'
  | 'RESOLVED'
  | 'ESCALATED'
  | 'CLOSED';

export interface ResponsibleEntity {
  type: EntityType;
  name: string;
  contact_phone?: string;
  office_location?: string;
  jurisdiction?: string;
}

export interface SLAInfo {
  sla_hours: number; // Total SLA in hours (72h, 48h, 24h)
  elapsed_hours: number; // Time elapsed since case creation
  remaining_hours: number; // Time remaining
  percentage_used: number; // 0-100, how much of SLA consumed
  is_escalated: boolean;
  escalation_level: number; // 0 = initial, 1 = first escalation, etc.
}

export interface EscalationPath {
  current: ResponsibleEntity;
  next?: ResponsibleEntity;
  escalates_at?: string; // ISO timestamp
  escalation_reason?: string;
}

export interface NextStepsInfo {
  case_id: string;
  case_reference: string; // Human-readable ref like "RYP-GRV-2024-001"
  status: CaseStatus;
  created_at: string;
  updated_at: string;
  responsible_entity: ResponsibleEntity;
  sla: SLAInfo;
  escalation_path: EscalationPath;
  expected_actions: string[]; // What citizen can expect
  citizen_actions?: string[]; // What citizen should do (if any)
  updates: CaseUpdate[];
}

export interface CaseUpdate {
  id: string;
  timestamp: string;
  message: string;
  status_change?: {
    from: CaseStatus;
    to: CaseStatus;
  };
  actor: {
    type: 'citizen' | 'official' | 'system';
    name?: string;
  };
}

export interface NextStepsRequest {
  case_id: string;
}

export interface NextStepsResponse {
  success: boolean;
  next_steps?: NextStepsInfo;
  error?: string;
}

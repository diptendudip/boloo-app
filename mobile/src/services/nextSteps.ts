/**
 * Next Steps Service
 *
 * API client for "Agla Kya Hoka" (What happens next) functionality.
 * Fetches SLA tracking, responsible entities, and escalation paths.
 */

import axios, { AxiosError } from 'axios';
import { API_URL } from '../constants/config';
import type {
  NextStepsRequest,
  NextStepsResponse,
  NextStepsInfo,
} from '../types/nextSteps';

class NextStepsService {
  private baseURL: string;

  constructor() {
    this.baseURL = `${API_URL}/api/v1/cases`;
  }

  /**
   * Get next steps information for a case
   */
  async getNextSteps(caseId: string): Promise<NextStepsInfo> {
    try {
      console.log(`[NextStepsService] Fetching next steps for case: ${caseId}`);

      const response = await axios.get<NextStepsResponse>(
        `${this.baseURL}/${caseId}/next-steps`,
        {
          timeout: 10000,
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.data.success || !response.data.next_steps) {
        throw new Error(response.data.error || 'Failed to fetch next steps');
      }

      return response.data.next_steps;
    } catch (error) {
      console.error('[NextStepsService] Error:', error);

      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError<{ detail?: string }>;

        // TESTING MODE: Return dummy next steps if network error
        if (axiosError.request && !axiosError.response) {
          console.log('[NextStepsService] TESTING MODE: Using dummy next steps');
          return this.getDummyNextSteps(caseId);
        }

        if (axiosError.code === 'ECONNABORTED') {
          throw new Error('अनुरोध समय समाप्त (Request timed out)');
        }

        if (axiosError.response) {
          const status = axiosError.response.status;
          const detail = axiosError.response.data?.detail;

          if (status === 404) {
            throw new Error('केस नहीं मिला (Case not found)');
          } else if (status === 403) {
            throw new Error('अनुमति नहीं है (Access denied)');
          } else if (status >= 500) {
            throw new Error('सर्वर त्रुटि (Server error)');
          }

          throw new Error(detail || 'जानकारी नहीं मिली (Failed to fetch)');
        }
      }

      throw new Error('अज्ञात त्रुटि (Unknown error)');
    }
  }

  /**
   * Generate dummy next steps for testing (offline mode)
   */
  private getDummyNextSteps(caseId: string): NextStepsInfo {
    const now = new Date();
    const escalationTime = new Date(now.getTime() + 48 * 60 * 60 * 1000); // 48 hours from now
    const caseReference = caseId.replace('test-case-', 'BOL');

    return {
      case_id: caseId,
      case_reference: caseReference,
      status: 'OPEN',
      sla: {
        sla_hours: 72,
        elapsed_hours: 0.5,
        remaining_hours: 71.5,
        percentage_used: 0.7,
      },
      responsible_entity: {
        id: 'test-gp-001',
        name: 'रायपुर ग्राम पंचायत',
        type: 'GRAM_PANCHAYAT' as any,
        jurisdiction: 'Raipur Block',
        contact_phone: '+91-1234567890',
        contact_email: 'sarpanch@test.gov.in',
      },
      expected_actions: [
        '🧪 शिकायत का सत्यापन (24 घंटे में)',
        'साइट निरीक्षण और मूल्यांकन (48 घंटे में)',
        'समाधान योजना तैयार करना (60 घंटे में)',
      ],
      citizen_actions: [
        '🧪 TESTING MODE: यह डमी डेटा है',
        'अपडेट के लिए नियमित रूप से ऐप जांचें',
        'जरूरत पड़ने पर दस्तावेज़ जमा करें',
        'अधिकारी से संपर्क करें यदि देरी हो',
      ],
      escalation_path: {
        current: {
          name: 'ग्राम पंचायत',
          type: 'GRAM_PANCHAYAT' as any,
        },
        next: {
          name: 'खंड विकास अधिकारी',
          type: 'BDO' as any,
        },
        escalates_at: escalationTime.toISOString(),
      },
      updates: [
        {
          id: 'update-1',
          timestamp: now.toISOString(),
          message: '🧪 शिकायत दर्ज की गई (Testing Mode)',
        },
      ],
    } as any;
  }

  /**
   * Poll next steps with interval for live updates
   */
  async pollNextSteps(
    caseId: string,
    onUpdate: (nextSteps: NextStepsInfo) => void,
    intervalMs: number = 30000 // 30 seconds default
  ): Promise<() => void> {
    let isActive = true;

    const poll = async () => {
      while (isActive) {
        try {
          const nextSteps = await this.getNextSteps(caseId);
          if (isActive) {
            onUpdate(nextSteps);
          }
        } catch (error) {
          console.error('[NextStepsService] Polling error:', error);
        }

        // Wait for interval
        await new Promise((resolve) => setTimeout(resolve, intervalMs));
      }
    };

    // Start polling
    poll();

    // Return cleanup function
    return () => {
      isActive = false;
    };
  }

  /**
   * Calculate time until escalation
   */
  calculateEscalationCountdown(nextSteps: NextStepsInfo): {
    hours: number;
    minutes: number;
    isUrgent: boolean;
  } | null {
    if (!nextSteps.escalation_path.escalates_at) {
      return null;
    }

    const escalationTime = new Date(nextSteps.escalation_path.escalates_at);
    const now = new Date();
    const msRemaining = escalationTime.getTime() - now.getTime();

    if (msRemaining <= 0) {
      return { hours: 0, minutes: 0, isUrgent: true };
    }

    const hours = Math.floor(msRemaining / (1000 * 60 * 60));
    const minutes = Math.floor((msRemaining % (1000 * 60 * 60)) / (1000 * 60));

    return {
      hours,
      minutes,
      isUrgent: hours < 12, // Urgent if less than 12 hours
    };
  }

  /**
   * Format case reference for display
   */
  formatCaseReference(reference: string): string {
    // RYP-GRV-2024-001 -> RYP/GRV/2024/001
    return reference.replace(/-/g, '/');
  }

  /**
   * Get entity display name in Hindi
   */
  getEntityDisplayName(type: string): string {
    const names: Record<string, string> = {
      GRAM_PANCHAYAT: 'ग्राम पंचायत',
      BDO: 'खंड विकास अधिकारी',
      DISTRICT_OFFICE: 'जिला कार्यालय',
      STATE_OFFICE: 'राज्य कार्यालय',
    };
    return names[type] || type;
  }
}

// Export singleton instance
export const nextStepsService = new NextStepsService();

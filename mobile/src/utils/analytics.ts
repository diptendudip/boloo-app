/**
 * Analytics Tracking Utility
 *
 * Centralized analytics tracking for user events
 * Can be integrated with Firebase Analytics, Mixpanel, or custom backend
 */

export enum AnalyticsEvent {
  // Auth Events
  OTP_REQUEST_INITIATED = 'otp_request_initiated',
  OTP_REQUEST_SUCCESS = 'otp_request_success',
  OTP_REQUEST_FAILED = 'otp_request_failed',
  OTP_VERIFY_INITIATED = 'otp_verify_initiated',
  OTP_VERIFY_SUCCESS = 'otp_verify_success',
  OTP_VERIFY_FAILED = 'otp_verify_failed',
  OTP_RESEND_SMS = 'otp_resend_sms',
  OTP_RESEND_VOICE = 'otp_resend_voice',
  LOGIN_SUCCESS = 'login_success',
  LOGOUT = 'logout',

  // Phone Events
  PHONE_NUMBER_ENTERED = 'phone_number_entered',
  PHONE_NUMBER_CHANGED = 'phone_number_changed',
  PHONE_VALIDATION_FAILED = 'phone_validation_failed',

  // Error Events
  NETWORK_ERROR = 'network_error',
  API_ERROR = 'api_error',
  RATE_LIMIT_ERROR = 'rate_limit_error',
}

export interface AnalyticsEventData {
  event: AnalyticsEvent;
  properties?: Record<string, any>;
  timestamp?: string;
}

class AnalyticsService {
  private isEnabled: boolean = true;
  private eventQueue: AnalyticsEventData[] = [];

  /**
   * Track an analytics event
   */
  track(event: AnalyticsEvent, properties?: Record<string, any>): void {
    if (!this.isEnabled) {
      return;
    }

    const eventData: AnalyticsEventData = {
      event,
      properties: {
        ...properties,
        platform: 'mobile',
        timestamp: new Date().toISOString(),
      },
      timestamp: new Date().toISOString(),
    };

    // Log to console in development
    if (__DEV__) {
      console.log('[Analytics]', event, properties);
    }

    // Add to queue for batch processing
    this.eventQueue.push(eventData);

    // TODO: Integrate with actual analytics service
    // Examples:
    // - Firebase Analytics: analytics().logEvent(event, properties)
    // - Mixpanel: mixpanel.track(event, properties)
    // - Custom backend: api.post('/analytics/events', eventData)
  }

  /**
   * Track OTP request event
   */
  trackOTPRequest(phoneNumber: string, success: boolean, error?: string): void {
    this.track(
      success ? AnalyticsEvent.OTP_REQUEST_SUCCESS : AnalyticsEvent.OTP_REQUEST_FAILED,
      {
        phone_number_length: phoneNumber.length,
        error_message: error,
      }
    );
  }

  /**
   * Track OTP verification event
   */
  trackOTPVerify(phoneNumber: string, success: boolean, error?: string): void {
    this.track(
      success ? AnalyticsEvent.OTP_VERIFY_SUCCESS : AnalyticsEvent.OTP_VERIFY_FAILED,
      {
        phone_number_length: phoneNumber.length,
        error_message: error,
      }
    );
  }

  /**
   * Track OTP resend event
   */
  trackOTPResend(phoneNumber: string, type: 'sms' | 'voice'): void {
    this.track(
      type === 'sms' ? AnalyticsEvent.OTP_RESEND_SMS : AnalyticsEvent.OTP_RESEND_VOICE,
      {
        phone_number_length: phoneNumber.length,
        resend_type: type,
      }
    );
  }

  /**
   * Track login success
   */
  trackLoginSuccess(userId: string, isFirstTime: boolean): void {
    this.track(AnalyticsEvent.LOGIN_SUCCESS, {
      user_id: userId,
      is_first_time: isFirstTime,
    });
  }

  /**
   * Track phone validation error
   */
  trackPhoneValidationError(phoneNumber: string, error: string): void {
    this.track(AnalyticsEvent.PHONE_VALIDATION_FAILED, {
      phone_number_length: phoneNumber.length,
      error_message: error,
    });
  }

  /**
   * Track network/API errors
   */
  trackError(type: 'network' | 'api' | 'rate_limit', error: string, context?: string): void {
    const eventMap = {
      network: AnalyticsEvent.NETWORK_ERROR,
      api: AnalyticsEvent.API_ERROR,
      rate_limit: AnalyticsEvent.RATE_LIMIT_ERROR,
    };

    this.track(eventMap[type], {
      error_message: error,
      context,
    });
  }

  /**
   * Enable or disable analytics tracking
   */
  setEnabled(enabled: boolean): void {
    this.isEnabled = enabled;
  }

  /**
   * Get queued events (for debugging or manual sync)
   */
  getEventQueue(): AnalyticsEventData[] {
    return [...this.eventQueue];
  }

  /**
   * Clear event queue
   */
  clearQueue(): void {
    this.eventQueue = [];
  }
}

// Export singleton instance
export const analytics = new AnalyticsService();

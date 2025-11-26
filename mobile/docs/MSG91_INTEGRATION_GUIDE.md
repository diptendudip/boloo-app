# MSG91 OTP Integration Guide

## Overview

This document describes the MSG91 OTP integration for the Boloo mobile app. The implementation uses a native approach with backend API integration for better control and user experience.

## Architecture

### Integration Strategy: Native Implementation (Option A)

We chose the native implementation over WebView embedding for the following reasons:

1. **Better Control**: Full control over UI/UX and error handling
2. **Performance**: No WebView overhead
3. **Offline Support**: Better offline queue management
4. **Analytics**: Integrated analytics tracking
5. **User Experience**: Seamless native feel

### Components

```
src/
├── services/
│   └── auth.ts                    # MSG91 API integration
├── utils/
│   ├── phoneValidation.ts         # Phone number validation
│   └── analytics.ts               # Analytics tracking
├── components/
│   ├── OTPInput.tsx              # OTP input with auto-focus
│   └── ResendOTPTimer.tsx        # Resend timer with voice option
├── screens/
│   ├── LoginScreen.tsx           # Phone number entry
│   └── VerifyOTPScreen.tsx       # OTP verification
└── constants/
    └── otpMessages.ts            # Error messages & constants
```

## Features Implemented

### 1. Phone Number Validation

**File**: `/src/utils/phoneValidation.ts`

- Indian phone number validation (10 digits, starts with 6-9)
- E.164 format conversion (+91XXXXXXXXXX)
- Display formatting (+91 98765 43210)
- Clean input handling

**Example Usage**:
```typescript
import { validateIndianPhoneNumber } from '../utils/phoneValidation';

const validation = validateIndianPhoneNumber('9876543210');
if (validation.isValid) {
  const formatted = validation.formatted; // +919876543210
}
```

### 2. OTP Input Component

**File**: `/src/components/OTPInput.tsx`

Features:
- 6-digit OTP input
- Auto-focus next input
- Auto-focus previous on backspace
- Auto-submit on completion
- Visual feedback (filled state, focused state)
- Disabled state
- SMS auto-fill support (iOS/Android)

**Example Usage**:
```typescript
<OTPInput
  value={otp}
  onChange={setOTP}
  disabled={isLoading}
  autoFocus
/>
```

### 3. Resend OTP Timer

**File**: `/src/components/ResendOTPTimer.tsx`

Features:
- 30-second countdown timer
- SMS resend option
- Voice OTP option (shows after first SMS resend)
- Loading states
- Error handling

**Example Usage**:
```typescript
<ResendOTPTimer
  onResend={handleResendOTP}
  disabled={isLoading}
  phoneNumber={phoneNumber}
  initialSeconds={30}
/>
```

### 4. Auth Service

**File**: `/src/services/auth.ts`

API Methods:
- `requestOTP(phoneNumber)` - Send OTP via SMS
- `resendOTP(phoneNumber, type)` - Resend OTP (SMS or Voice)
- `verifyOTP(phoneNumber, otp)` - Verify OTP code

**Example Usage**:
```typescript
import { authService } from '../services/auth';

// Send OTP
await authService.requestOTP('+919876543210');

// Resend OTP via Voice
await authService.resendOTP('+919876543210', 'voice');

// Verify OTP
const response = await authService.verifyOTP('+919876543210', '123456');
```

### 5. Error Handling

**File**: `/src/constants/otpMessages.ts`

Comprehensive error messages for:
- Phone validation errors
- OTP validation errors
- Network errors
- Server errors
- Rate limiting

**Example**:
```typescript
import { getOTPErrorMessage } from '../constants/otpMessages';

try {
  await authService.requestOTP(phone);
} catch (error) {
  const message = getOTPErrorMessage(error);
  Alert.alert('Error', message);
}
```

### 6. Analytics Tracking

**File**: `/src/utils/analytics.ts`

Events tracked:
- OTP request initiated
- OTP request success/failure
- OTP verification initiated
- OTP verification success/failure
- OTP resend (SMS/Voice)
- Phone validation errors
- Network/API errors

**Example**:
```typescript
import { analytics, AnalyticsEvent } from '../utils/analytics';

analytics.track(AnalyticsEvent.OTP_REQUEST_INITIATED, {
  phone_length: 10,
});

analytics.trackOTPRequest(phoneNumber, success, error);
```

## Backend API Integration

### Required Backend Endpoints

Your backend should implement these endpoints:

#### 1. Request OTP
```
POST /v1/auth/otp/request
Content-Type: application/json

Request:
{
  "phone_number": "+919876543210"
}

Response (Success):
{
  "success": true,
  "message": "OTP sent successfully",
  "request_id": "msg91-request-id",
  "type": "success"
}

Response (Error):
{
  "success": false,
  "message": "Failed to send OTP",
  "error_code": "RATE_LIMIT_EXCEEDED"
}
```

#### 2. Resend OTP
```
POST /v1/auth/otp/resend
Content-Type: application/json

Request:
{
  "phone_number": "+919876543210",
  "retry_type": "sms" | "voice"
}

Response: Same as Request OTP
```

#### 3. Verify OTP
```
POST /v1/auth/otp/verify
Content-Type: application/json

Request:
{
  "phone_number": "+919876543210",
  "otp_code": "123456"
}

Response (Success):
{
  "access_token": "jwt-token-here",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "user-uuid",
    "phone": "+919876543210",
    "name": "User Name",
    "role": "citizen"
  }
}

Response (Error):
{
  "success": false,
  "message": "Invalid OTP",
  "error_code": "INVALID_OTP"
}
```

### MSG91 Backend Integration

Your backend should integrate with MSG91 API:

```python
# Example Python/FastAPI backend implementation

import requests
from fastapi import HTTPException

MSG91_AUTH_KEY = "your-msg91-auth-key"
MSG91_TEMPLATE_ID = "356a79766959393030333137"

def send_otp_via_msg91(phone_number: str):
    """Send OTP using MSG91 API"""
    url = f"https://control.msg91.com/api/v5/otp"

    headers = {
        "authkey": MSG91_AUTH_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "template_id": MSG91_TEMPLATE_ID,
        "mobile": phone_number.replace("+91", ""),  # Remove +91
        "otp_expiry": 5,  # 5 minutes
        "otp_length": 6
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=500, detail="Failed to send OTP")

def verify_otp_via_msg91(phone_number: str, otp_code: str):
    """Verify OTP using MSG91 API"""
    url = f"https://control.msg91.com/api/v5/otp/verify"

    headers = {
        "authkey": MSG91_AUTH_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "mobile": phone_number.replace("+91", ""),
        "otp": otp_code
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data.get("type") == "success":
            return True

    return False

def resend_otp_via_msg91(phone_number: str, retry_type: str = "text"):
    """Resend OTP via SMS or Voice"""
    url = f"https://control.msg91.com/api/v5/otp/retry"

    headers = {
        "authkey": MSG91_AUTH_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "mobile": phone_number.replace("+91", ""),
        "retrytype": retry_type  # "text" or "voice"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=500, detail="Failed to resend OTP")
```

## Testing Guide

### Development Mode (Testing)

The app includes a testing mode for development:

**How it works**:
1. Set `TESTING_MODE = __DEV__` in LoginScreen.tsx and VerifyOTPScreen.tsx
2. Use any valid 10-digit phone number
3. Use OTP: `123456` for verification
4. Backend API calls are skipped

**Testing OTP Flow**:
```bash
# 1. Start the app
npm start

# 2. Test Login Flow
# - Enter phone: 9876543210
# - Tap "Send OTP"
# - See alert: "Testing Mode - OTP: 123456"

# 3. Test OTP Verification
# - Enter OTP: 123456
# - Tap "Verify & Continue"
# - Should log in successfully

# 4. Test Resend OTP
# - Wait for timer to reach 0
# - Tap "Resend SMS"
# - Should show testing mode alert

# 5. Test Voice OTP
# - After first SMS resend, "Call Me" button appears
# - Tap "Call Me"
# - Should show voice OTP testing alert
```

### Production Mode

To enable production mode with real MSG91:

1. **Update Backend**:
   - Implement MSG91 API integration
   - Deploy backend with endpoints

2. **Update Mobile App**:
   ```typescript
   // LoginScreen.tsx and VerifyOTPScreen.tsx
   const TESTING_MODE = false; // Disable testing mode
   ```

3. **Configure API URL**:
   ```javascript
   // app.json or .env
   {
     "extra": {
       "apiUrl": "https://your-backend.com"
     }
   }
   ```

4. **Test Production Flow**:
   ```bash
   # 1. Enter real phone number
   # 2. Receive SMS with OTP
   # 3. Enter received OTP
   # 4. Verify login
   # 5. Test resend SMS
   # 6. Test voice OTP
   ```

### Error Testing

Test various error scenarios:

```typescript
// 1. Invalid phone number
// Input: "123456" (too short)
// Expected: "Phone number must be 10 digits"

// 2. Wrong OTP
// Input: "000000"
// Expected: "Invalid OTP. Please try again"

// 3. Network error (airplane mode)
// Expected: "Network error. Please check your internet connection"

// 4. Rate limiting
// Resend OTP 5 times quickly
// Expected: "Too many OTP requests. Please try again after some time"
```

## User Flow

### Login Flow

```
1. LoginScreen
   ├─ User enters phone number
   ├─ Validates phone (10 digits, starts with 6-9)
   ├─ Calls authService.requestOTP()
   ├─ Shows success alert
   └─ Navigates to VerifyOTPScreen

2. VerifyOTPScreen
   ├─ Shows OTP input (6 digits)
   ├─ User enters OTP
   ├─ Auto-verifies on completion
   ├─ Calls authService.verifyOTP()
   ├─ Shows success alert
   └─ AuthContext updates (navigation handled)

3. Resend Flow
   ├─ Timer counts down from 30s
   ├─ After 0s, shows "Resend SMS" button
   ├─ After first resend, shows "Call Me" button
   ├─ Calls authService.resendOTP(type)
   └─ Resets timer
```

## Configuration

### MSG91 Widget Configuration

The original MSG91 widget config (not used in native implementation):

```javascript
var configuration = {
  widgetId: "356a79766959393030333137",
  tokenAuth: "{token}",
  identifier: "<phone>",
  exposeMethods: "true",
  success: (data) => { console.log('success response', data); },
  failure: (error) => { console.log('failure reason', error); }
};
```

### Environment Variables

Required environment variables:

```bash
# Backend
MSG91_AUTH_KEY=your-msg91-auth-key
MSG91_TEMPLATE_ID=356a79766959393030333137

# Mobile App
API_URL=https://your-backend.com
```

## Security Considerations

1. **Never expose MSG91 credentials in mobile app**
   - All MSG91 API calls go through backend
   - Backend validates and sanitizes requests

2. **Rate Limiting**
   - Implement rate limiting on backend
   - Prevent OTP spam/abuse

3. **OTP Expiry**
   - OTPs expire after 5 minutes
   - Backend should validate expiry

4. **Token Security**
   - Store JWT tokens securely in AsyncStorage
   - Implement token refresh mechanism

5. **Phone Number Privacy**
   - Mask phone numbers in analytics
   - Don't log full phone numbers

## Troubleshooting

### Common Issues

1. **OTP not received**
   - Check phone number format (+91XXXXXXXXXX)
   - Verify MSG91 credentials
   - Check backend logs
   - Verify SMS service is active

2. **OTP verification fails**
   - Check OTP expiry (5 minutes)
   - Verify backend validation logic
   - Check for typos in OTP

3. **Resend not working**
   - Check rate limiting
   - Verify resend API endpoint
   - Check timer state

4. **Voice OTP not showing**
   - Voice option appears after first SMS resend
   - Check ResendOTPTimer component state

## Next Steps

1. **Integrate Analytics Service**
   - Connect to Firebase Analytics
   - Or implement custom analytics backend

2. **Add Biometric Authentication**
   - After successful OTP login
   - Store biometric preference

3. **Implement Token Refresh**
   - Auto-refresh JWT tokens
   - Handle token expiry

4. **Add Multi-language Support**
   - Translate error messages
   - Support Hindi/regional languages

5. **Optimize Performance**
   - Add caching for repeated requests
   - Implement retry mechanism

## Support

For issues or questions:
- Backend API: Check `/v1/auth/otp/*` endpoints
- MSG91 Issues: https://msg91.com/help
- Mobile App: Check console logs with `[Auth]` prefix

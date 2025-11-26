# Persistent Login Implementation Guide

## Overview

This document describes the implementation of persistent login with JWT token storage and OTP verification tracking for the Boloo mobile application.

## Problem Statement

**Before:**
- Users were logged out every time they restarted the app
- No persistent token storage
- No OTP verification state tracking
- Users had to login every time app opened

**After:**
- JWT tokens stored securely with expiry tracking
- Automatic session restoration on app start
- OTP verification status tracked for 24 hours
- Seamless user experience across app restarts

## Implementation Files

### 1. **Enhanced Authentication Storage** (`/src/services/authStorage.ts`)

Complete storage service for authentication persistence with:
- JWT token storage with expiry tracking
- OTP verification status tracking (24-hour validity)
- User data persistence
- Session management
- Token validation

**Key Methods:**
```typescript
// Token Management
authStorage.saveAuthToken(token, expiresIn)
authStorage.getAuthToken()
authStorage.clearAuthToken()
authStorage.isTokenExpired()

// OTP Verification Tracking
authStorage.saveOTPVerificationStatus(phoneNumber, verified)
authStorage.getOTPVerificationStatus(phoneNumber)
authStorage.isOTPVerified(phoneNumber)

// User Data
authStorage.saveUser(user)
authStorage.getUser()

// Session Management
authStorage.isSessionValid()
authStorage.getAuthState()
authStorage.clearAll()
```

### 2. **Auto-Login Hook** (`/src/hooks/useAutoLogin.ts`)

React hook for automatic session restoration:
- Checks stored token on app mount
- Validates token expiry
- Supports dev mode with dummy tokens
- Production mode validates with backend
- Auto-clears expired sessions

**Usage:**
```typescript
const { isChecking, isAuthenticated, user, error } = useAutoLogin();
```

### 3. **Splash Screen** (`/src/components/SplashScreen.tsx`)

Loading screen shown during authentication check:
- Displays app logo and branding
- Shows loading indicator
- Provides user feedback during session restoration

### 4. **Updated Components**

#### AuthContext (`/src/context/AuthContext.tsx`)
- Integrated `authStorage` for persistent storage
- Enhanced login flow to save OTP verification
- Token expiry tracking
- Automatic session restoration
- Supports both dev and production modes

#### AppNavigator (`/src/navigation/AppNavigator.tsx`)
- Shows splash screen during auth check
- Automatic navigation based on session state

#### Storage Service (`/src/services/storage.ts`)
- Updated to use enhanced authStorage
- Maintains backward compatibility

## Architecture Flow

### App Start Flow

```
1. App Starts
   ↓
2. AuthContext.checkAuthStatus()
   ↓
3. authStorage.getAuthState()
   ↓
4. Check Token Exists & Not Expired
   ↓
5a. DEV MODE (dummy token)     5b. PRODUCTION MODE
    → Auto restore session          → Validate with backend
    → Navigate to app               → If valid: restore session
                                    → If invalid: clear & show login
```

### Login Flow

```
1. User Enters Phone Number
   ↓
2. Request OTP (via MSG91 in production)
   ↓
3. User Enters OTP
   ↓
4. Verify OTP
   ↓
5. Save Authentication Data:
   - authStorage.saveAuthToken(token, expiresIn)
   - authStorage.saveUser(user)
   - authStorage.saveOTPVerificationStatus(phone, true)
   ↓
6. Navigate to App
```

### Logout Flow

```
1. User Clicks Logout
   ↓
2. authStorage.clearAll()
   - Clear tokens
   - Clear user data
   - Clear OTP verification
   ↓
3. Backend logout (if available)
   ↓
4. Navigate to Login
```

## Data Storage Structure

### AsyncStorage Keys

```typescript
'auth_token'              // JWT access token
'token_expiry'           // Unix timestamp (ms)
'user'                   // JSON user object
'user_id'                // User ID string
'last_login_time'        // Unix timestamp (ms)
'session_id'             // Unique session identifier
'otp_verified_+919876543210'   // OTP verification flag
'otp_timestamp_+919876543210'  // OTP verification data (JSON)
```

### Token Data Structure

```typescript
{
  token: string;           // JWT token
  expiresAt: number;       // Unix timestamp (ms)
  refreshToken?: string;   // Optional refresh token
}
```

### OTP Verification Data

```typescript
{
  phoneNumber: string;     // E.164 format (+919876543210)
  verified: boolean;       // Verification status
  timestamp: number;       // Unix timestamp (ms)
  expiresAt: number;       // Unix timestamp (ms) - 24h from verification
}
```

## Development vs Production Modes

### Development Mode (`__DEV__ = true`)

- **OTP:** Use "123456" to bypass MSG91
- **Token:** Dummy tokens accepted (prefix: `dummy-token-`)
- **Validation:** No backend validation required
- **Storage:** Same persistent storage used
- **Session:** Auto-restored from storage

### Production Mode (`__DEV__ = false`)

- **OTP:** Real SMS via MSG91
- **Token:** Real JWT tokens from backend
- **Validation:** Backend validates token on app start
- **Storage:** Same persistent storage used
- **Expiry:** 24-hour token validity (configurable)

## Security Considerations

### Token Storage
- Tokens stored in AsyncStorage (encrypted on iOS, secure on Android)
- Token expiry tracked and validated
- Expired tokens auto-cleared
- No sensitive data in tokens

### OTP Verification
- Verification status expires after 24 hours
- Phone number required for verification check
- Status cleared on logout
- Cannot bypass verification in production

### Session Management
- Unique session IDs generated
- Last login time tracked
- Session validation on critical operations
- Auto-logout on token expiry

## Migration Guide

### From Development to Production

#### 1. Update Configuration

Create `/src/constants/config.ts`:
```typescript
export const APP_CONFIG = {
  API_BASE_URL: process.env.API_BASE_URL || 'https://api.boloo.app',
  TOKEN_EXPIRY: 86400, // 24 hours in seconds
  OTP_EXPIRY: 86400,   // 24 hours in seconds
  ENABLE_DEV_MODE: __DEV__,
};
```

#### 2. Environment Variables

Create `.env.production`:
```bash
API_BASE_URL=https://api.boloo.app
MSG91_AUTH_KEY=your_msg91_key
ENABLE_TOKEN_REFRESH=true
```

#### 3. Backend API Requirements

Ensure backend implements:
```
POST /v1/auth/otp/request    - Send OTP
POST /v1/auth/otp/verify     - Verify OTP & get token
POST /v1/auth/otp/resend     - Resend OTP
GET  /v1/auth/verify         - Validate token
POST /v1/auth/logout         - Logout user
GET  /v1/auth/refresh        - Refresh token (optional)
```

#### 4. Update API Service

Update `/src/services/api.ts`:
```typescript
import { authStorage } from './authStorage';
import { APP_CONFIG } from '../constants/config';

const api = axios.create({
  baseURL: APP_CONFIG.API_BASE_URL,
  timeout: 10000,
});

// Auto-attach token to requests
api.interceptors.request.use(async (config) => {
  const token = await authStorage.getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await authStorage.clearAll();
      // Navigate to login
    }
    return Promise.reject(error);
  }
);
```

#### 5. Test Checklist

- [ ] Test login flow with real OTP
- [ ] Verify token storage and retrieval
- [ ] Test session restoration after app restart
- [ ] Verify token expiry handling
- [ ] Test logout flow
- [ ] Verify OTP verification tracking
- [ ] Test network error handling
- [ ] Verify offline capabilities
- [ ] Test migration from old sessions

## Testing Guide

### Development Testing

1. **First-time Login:**
   ```
   - Enter phone number
   - Use OTP: 123456
   - Verify session saved
   - Close and reopen app
   - Verify auto-login works
   ```

2. **Token Expiry:**
   ```
   - Modify token_expiry in AsyncStorage to past time
   - Reopen app
   - Verify redirected to login
   ```

3. **Logout:**
   ```
   - Login with OTP
   - Click logout
   - Verify all data cleared
   - Reopen app
   - Verify shown login screen
   ```

### Production Testing

1. **Real OTP Flow:**
   ```
   - Enter real phone number
   - Receive SMS OTP
   - Verify OTP
   - Check token saved
   - Restart app
   - Verify auto-login
   ```

2. **Token Validation:**
   ```
   - Login successfully
   - Check backend receives token
   - Restart app
   - Verify backend validates token
   ```

3. **Network Failures:**
   ```
   - Turn off network
   - Restart app
   - Verify cached session used
   - Turn on network
   - Verify token validated
   ```

## Debugging

### Enable Debug Logs

Add to `App.tsx`:
```typescript
if (__DEV__) {
  console.log('[Debug] Auth storage enabled');
  // Log all auth operations
}
```

### Check AsyncStorage

```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

// List all keys
const keys = await AsyncStorage.getAllKeys();
console.log('Storage keys:', keys);

// Get specific value
const token = await AsyncStorage.getItem('auth_token');
console.log('Token:', token);

// Clear all data (DANGER!)
await AsyncStorage.clear();
```

### Inspect Auth State

```typescript
import { authStorage } from './services/authStorage';

const state = await authStorage.getAuthState();
console.log('Auth State:', {
  hasToken: !!state.token,
  hasUser: !!state.user,
  isExpired: state.isExpired,
  lastLogin: new Date(state.lastLogin || 0).toISOString(),
});
```

## Troubleshooting

### Issue: Users still logged out on restart

**Solution:**
1. Check if AsyncStorage is working:
   ```typescript
   const test = await AsyncStorage.setItem('test', 'value');
   const value = await AsyncStorage.getItem('test');
   console.log('AsyncStorage test:', value);
   ```

2. Verify token is being saved:
   ```typescript
   const token = await authStorage.getAuthToken();
   console.log('Stored token:', token);
   ```

### Issue: Token expired too quickly

**Solution:**
1. Check token expiry setting:
   ```typescript
   const expiry = await authStorage.getTokenExpiry();
   const now = Date.now();
   const hoursLeft = (expiry - now) / (1000 * 60 * 60);
   console.log('Hours until expiry:', hoursLeft);
   ```

2. Increase expiry time in login:
   ```typescript
   await authStorage.saveAuthToken(token, 86400 * 7); // 7 days
   ```

### Issue: OTP verification not persisting

**Solution:**
1. Check OTP verification status:
   ```typescript
   const status = await authStorage.getOTPVerificationStatus(phoneNumber);
   console.log('OTP Status:', status);
   ```

2. Verify phone number format:
   ```typescript
   // Must be E.164 format
   const phone = '+919876543210'; // Correct
   // NOT: '9876543210' or '919876543210'
   ```

## Performance Considerations

### AsyncStorage Operations
- All operations are async
- Batch operations use `multiSet`/`multiGet`
- Minimize storage reads/writes
- Cache frequently accessed data

### Session Restoration
- Happens on app start (blocking)
- Optimized with parallel operations
- Cached in memory after first load
- Background validation in production

## Future Enhancements

1. **Token Refresh:**
   - Implement refresh token flow
   - Auto-refresh before expiry
   - Seamless token renewal

2. **Biometric Authentication:**
   - Add Face ID/Touch ID
   - Quick re-authentication
   - Enhanced security

3. **Multi-device Support:**
   - Device registration
   - Session management
   - Remote logout

4. **Analytics:**
   - Track session durations
   - Login patterns
   - Error rates

## Support

For issues or questions:
- Check console logs with `[AuthContext]` prefix
- Review AsyncStorage data
- Test in both dev and production modes
- Verify backend API responses

---

**Implementation Date:** November 24, 2025
**Version:** 1.0.0
**Author:** Claude Code Assistant

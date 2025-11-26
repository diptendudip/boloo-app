# Persistent Login - Quick Reference

## For Developers

### Import and Use

```typescript
// Use enhanced auth storage
import { authStorage } from '../services/authStorage';

// Auto-login hook
import { useAutoLogin } from '../hooks/useAutoLogin';

// Legacy storage (still works)
import { storage } from '../services/storage';
```

### Common Operations

#### Save User Session
```typescript
// After successful OTP verification
await authStorage.saveAuthToken(token, 86400); // 24 hours
await authStorage.saveUser(user);
await authStorage.saveOTPVerificationStatus(phoneNumber, true);
```

#### Check Session on App Start
```typescript
// Automatic in AuthContext
const { isAuthenticated, isLoading, user } = useAuth();

// Manual check
const authState = await authStorage.getAuthState();
if (authState.token && authState.user && !authState.isExpired) {
  // Valid session
}
```

#### Logout
```typescript
await authStorage.clearAll();
// Or use AuthContext
const { logout } = useAuth();
await logout();
```

#### Check OTP Verification
```typescript
const isVerified = await authStorage.isOTPVerified('+919876543210');
```

### Development Mode

```typescript
// Test with dummy OTP
Phone: 9876543210
OTP: 123456

// Dummy token auto-accepted
Token format: dummy-token-1234567890
```

### Production Mode

```typescript
// Real OTP via MSG91
// Token validated with backend: GET /v1/auth/verify
```

## Storage Keys Reference

| Key | Description | Format | Expiry |
|-----|-------------|--------|--------|
| `auth_token` | JWT access token | String | 24h default |
| `token_expiry` | Token expiration | Unix timestamp (ms) | - |
| `user` | User object | JSON | - |
| `user_id` | User ID | String | - |
| `last_login_time` | Last login | Unix timestamp (ms) | - |
| `session_id` | Session identifier | String | - |
| `otp_verified_{phone}` | OTP verification flag | Boolean string | 24h |
| `otp_timestamp_{phone}` | OTP verification data | JSON | 24h |

## API Endpoints Required

```
POST /v1/auth/otp/request
Body: { phone_number: "+919876543210" }
Response: { success: true, message: "OTP sent" }

POST /v1/auth/otp/verify
Body: { phone_number: "+919876543210", otp_code: "123456" }
Response: {
  success: true,
  access_token: "jwt_token_here",
  expires_in: 86400,
  user: { id, phone, name, role, ... }
}

GET /v1/auth/verify
Headers: { Authorization: "Bearer jwt_token" }
Response: {
  success: true,
  user: { id, phone, name, role, ... }
}
```

## Console Log Prefixes

```
[AuthStorage]  - Storage operations
[AuthContext]  - Authentication context
[AutoLogin]    - Auto-login hook
[Login]        - Login screen
[VerifyOTP]    - OTP verification screen
```

## Quick Debug Commands

```typescript
// Check current auth state
const state = await authStorage.getAuthState();
console.log(state);

// Clear everything (fresh start)
await AsyncStorage.clear();

// Simulate token expiry
await AsyncStorage.setItem('token_expiry', '1000');

// Check storage size
const keys = await AsyncStorage.getAllKeys();
console.log('Total keys:', keys.length);
```

## Error Codes

| Code | Description | Action |
|------|-------------|--------|
| `TOKEN_EXPIRED` | Token has expired | Clear session, show login |
| `INVALID_TOKEN` | Token validation failed | Clear session, show login |
| `NO_SESSION` | No stored session | Show login screen |
| `NETWORK_ERROR` | Backend unreachable | Use cached session if valid |
| `OTP_EXPIRED` | OTP verification expired | Re-verify OTP |

## File Structure

```
mobile/
├── src/
│   ├── services/
│   │   ├── authStorage.ts      ✨ New: Enhanced storage
│   │   ├── storage.ts          ✅ Updated: Uses authStorage
│   │   └── auth.ts             ✅ Existing: Auth API calls
│   ├── hooks/
│   │   ├── useAutoLogin.ts     ✨ New: Auto-login hook
│   │   └── index.ts
│   ├── context/
│   │   └── AuthContext.tsx     ✅ Updated: Persistent login
│   ├── components/
│   │   └── SplashScreen.tsx    ✨ New: Loading screen
│   ├── navigation/
│   │   └── AppNavigator.tsx    ✅ Updated: Shows splash
│   └── screens/
│       ├── LoginScreen.tsx     ✅ Existing
│       └── VerifyOTPScreen.tsx ✅ Existing
└── docs/
    ├── PERSISTENT_LOGIN_IMPLEMENTATION.md
    ├── TESTING_GUIDE.md
    └── QUICK_REFERENCE.md

✨ = New file
✅ = Updated file
```

## Common Patterns

### Pattern 1: Protected Routes
```typescript
// In navigation
{!isAuthenticated ? (
  <Stack.Screen name="Login" component={LoginScreen} />
) : (
  <Stack.Screen name="Home" component={HomeScreen} />
)}
```

### Pattern 2: Token Refresh (Future)
```typescript
// Add to api.ts interceptor
if (error.response?.status === 401) {
  const newToken = await refreshToken();
  if (newToken) {
    error.config.headers.Authorization = `Bearer ${newToken}`;
    return axios(error.config);
  }
}
```

### Pattern 3: Session Timeout Warning
```typescript
const checkExpiry = async () => {
  const expiry = await authStorage.getTokenExpiry();
  const now = Date.now();
  const hoursLeft = (expiry - now) / (1000 * 60 * 60);

  if (hoursLeft < 1) {
    Alert.alert('Session Expiring', 'Your session will expire soon');
  }
};
```

## Best Practices

1. **Always use authStorage** for new code
2. **Check session validity** before critical operations
3. **Handle token expiry** gracefully
4. **Log important operations** with clear prefixes
5. **Test both dev and production** modes
6. **Clear sessions on logout**
7. **Validate tokens** with backend in production

## Migration Checklist

From Development to Production:

- [ ] Set `API_BASE_URL` to production
- [ ] Configure MSG91 credentials
- [ ] Test real OTP flow
- [ ] Verify token validation endpoint
- [ ] Test network error handling
- [ ] Enable backend token validation
- [ ] Test session restoration
- [ ] Monitor error rates
- [ ] Set up analytics
- [ ] Document rollback plan

## Support

**Console Logs:** Enable with `console.log` filter in React Native Debugger
**Storage Inspector:** Use React Native Debugger's AsyncStorage tab
**Network Monitor:** Use Flipper or React Native Debugger

---

**Quick Links:**
- [Full Implementation Guide](./PERSISTENT_LOGIN_IMPLEMENTATION.md)
- [Testing Guide](./TESTING_GUIDE.md)
- [AsyncStorage Docs](https://react-native-async-storage.github.io/async-storage/)

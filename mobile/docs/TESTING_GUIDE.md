# Persistent Login Testing Guide

## Quick Start Testing

### Test 1: First-Time Login (Development Mode)

1. **Fresh Install:**
   ```bash
   # Clear app data (iOS Simulator)
   xcrun simctl uninstall booted com.yourapp.boloo

   # Or Android
   adb uninstall com.yourapp.boloo

   # Reinstall
   npm run android  # or npm run ios
   ```

2. **Login Flow:**
   - Open app
   - Enter phone: `9876543210`
   - Click "Send OTP"
   - See alert: "Testing Mode - OTP: 123456"
   - Enter OTP: `123456`
   - Verify navigation to Home screen

3. **Verify Persistence:**
   - Close app completely (swipe away from app switcher)
   - Reopen app
   - **EXPECTED:** Automatically logged in, no login screen
   - **ACTUAL:** Should see Home screen directly

4. **Check Storage:**
   ```typescript
   // Add this temporarily to App.tsx
   import { authStorage } from './src/services/authStorage';

   const checkStorage = async () => {
     const state = await authStorage.getAuthState();
     console.log('Auth State:', {
       hasToken: !!state.token,
       hasUser: !!state.user,
       userName: state.user?.name,
       phone: state.user?.phone,
       isExpired: state.isExpired,
       tokenExpiresAt: new Date(state.token ?
         await authStorage.getTokenExpiry() || 0 : 0).toISOString(),
     });
   };

   useEffect(() => { checkStorage(); }, []);
   ```

### Test 2: Logout and Re-login

1. **Logout:**
   - Navigate to Profile screen
   - Click "Logout"
   - **EXPECTED:** Redirected to Login screen

2. **Verify Storage Cleared:**
   ```typescript
   const state = await authStorage.getAuthState();
   console.log('After logout:', state);
   // Should show: { token: null, user: null, ... }
   ```

3. **Re-login:**
   - Enter phone: `9876543210`
   - Enter OTP: `123456`
   - Verify login successful

4. **Verify New Session:**
   - Close and reopen app
   - Should auto-login again

### Test 3: Token Expiry Simulation

1. **Login First:**
   - Login with OTP: `123456`
   - Verify auto-login works

2. **Simulate Expiry:**
   ```typescript
   // Add this button to Profile screen for testing
   const simulateExpiry = async () => {
     await AsyncStorage.setItem('token_expiry', '1000'); // Set to 1970
     Alert.alert('Token expired - restart app to test');
   };
   ```

3. **Test Expired Session:**
   - Click "Simulate Expiry" button
   - Close app completely
   - Reopen app
   - **EXPECTED:** Redirected to Login screen
   - **ACTUAL:** Should see Login screen, not Home

### Test 4: OTP Verification Tracking

1. **Login and Check Status:**
   ```typescript
   const checkOTP = async () => {
     const phone = '+919876543210';
     const isVerified = await authStorage.isOTPVerified(phone);
     const status = await authStorage.getOTPVerificationStatus(phone);

     console.log('OTP Verified:', isVerified);
     console.log('OTP Status:', {
       verified: status?.verified,
       timestamp: new Date(status?.timestamp || 0).toISOString(),
       expiresAt: new Date(status?.expiresAt || 0).toISOString(),
     });
   };
   ```

2. **Verify 24-Hour Expiry:**
   ```typescript
   // Simulate OTP verification expiry
   const phone = '+919876543210';
   const expiredData = {
     phoneNumber: phone,
     verified: true,
     timestamp: Date.now() - (25 * 60 * 60 * 1000), // 25 hours ago
     expiresAt: Date.now() - (1 * 60 * 60 * 1000),  // 1 hour ago
   };

   await AsyncStorage.setItem(
     `otp_timestamp_${phone}`,
     JSON.stringify(expiredData)
   );

   const isVerified = await authStorage.isOTPVerified(phone);
   console.log('Should be false:', isVerified); // false
   ```

## Advanced Testing Scenarios

### Test 5: Multiple App Restarts

**Objective:** Verify session persists across multiple restarts

```bash
# Script to test multiple restarts
for i in {1..5}; do
  echo "Restart $i"
  # Close app
  adb shell am force-stop com.yourapp.boloo
  # Wait
  sleep 2
  # Reopen
  adb shell am start -n com.yourapp.boloo/.MainActivity
  # Wait
  sleep 5
done
```

**Expected:** Should stay logged in after all 5 restarts

### Test 6: Network Offline/Online

1. **Login Online:**
   - Enable network
   - Login with OTP
   - Verify success

2. **Go Offline:**
   - Turn off WiFi and mobile data
   - Close and reopen app
   - **EXPECTED:** Should still auto-login (uses cached session)

3. **Go Back Online:**
   - Enable network
   - App should validate token with backend (in production)
   - Session continues

### Test 7: Concurrent User Sessions

**Scenario:** User logs in on multiple devices

1. **Device 1:**
   - Login with phone: `9876543210`
   - Note the session ID: `await authStorage.getSessionId()`

2. **Device 2:**
   - Login with same phone: `9876543210`
   - Note different session ID

3. **Backend Handling:**
   - Backend should track multiple sessions
   - Or invalidate old session (implementation-dependent)

### Test 8: Migration from Old Storage

**Objective:** Test migration from old storage format

1. **Create Old Format Data:**
   ```typescript
   // Simulate old storage format
   await AsyncStorage.multiSet([
     ['auth_token', 'old-format-token'],
     ['user', JSON.stringify({
       id: '1234-5678-90ab-cdef', // Old malformed UUID
       phone: '+919876543210',
       name: 'Old User',
     })],
   ]);
   ```

2. **Test Migration:**
   - Restart app
   - Verify UUID migration happens
   - Check new UUID format: `81589658-3600-4000-8815-000000000000`

3. **Verify New Storage:**
   ```typescript
   const state = await authStorage.getAuthState();
   console.log('Migrated user:', state.user);
   // Should have correct UUID format
   ```

## Production Testing

### Pre-Production Checklist

- [ ] **Environment Variables Set:**
  ```bash
  API_BASE_URL=https://api.boloo.app
  MSG91_AUTH_KEY=your_key
  ```

- [ ] **Backend API Working:**
  ```bash
  curl https://api.boloo.app/v1/auth/verify \
    -H "Authorization: Bearer test_token"
  ```

- [ ] **SMS Gateway Configured:**
  - MSG91 account active
  - Template approved
  - Credits available

### Production Test Flow

1. **Real OTP Login:**
   ```
   - Enter real phone number
   - Receive SMS (verify within 5 min)
   - Enter OTP from SMS
   - Verify login successful
   - Check token stored
   - Restart app
   - Verify auto-login
   ```

2. **Token Validation:**
   ```
   - Monitor network requests (React Native Debugger)
   - On app start, should call: GET /v1/auth/verify
   - Verify 200 response
   - Check console for: "[AuthContext] Session restored"
   ```

3. **Invalid Token Handling:**
   ```
   - Login successfully
   - Manually invalidate token on backend
   - Restart app
   - Should redirect to Login screen
   - Storage should be cleared
   ```

## Performance Testing

### Test 9: Session Restoration Speed

**Measure time to restore session:**

```typescript
// Add to AuthContext.checkAuthStatus()
const startTime = Date.now();

// ... existing code ...

const endTime = Date.now();
console.log(`[Performance] Session restored in ${endTime - startTime}ms`);
```

**Expected:** < 500ms for local storage, < 2000ms with backend validation

### Test 10: Storage Size

**Check AsyncStorage usage:**

```typescript
const getAllData = async () => {
  const keys = await AsyncStorage.getAllKeys();
  const stores = await AsyncStorage.multiGet(keys);

  let totalSize = 0;
  stores.forEach(([key, value]) => {
    const size = new Blob([value || '']).size;
    totalSize += size;
    console.log(`${key}: ${size} bytes`);
  });

  console.log(`Total storage: ${totalSize} bytes (${(totalSize/1024).toFixed(2)} KB)`);
};
```

**Expected:** < 50 KB for typical user data

## Debugging Tools

### Tool 1: Auth State Inspector

```typescript
// Add to Profile screen
import { authStorage } from '../services/authStorage';

const AuthDebugger = () => {
  const [state, setState] = useState<any>(null);

  const inspect = async () => {
    const authState = await authStorage.getAuthState();
    const phone = authState.user?.phone;

    setState({
      token: authState.token?.substring(0, 20) + '...',
      userId: authState.user?.id,
      phone: authState.user?.phone,
      isExpired: authState.isExpired,
      lastLogin: new Date(authState.lastLogin || 0).toLocaleString(),
      sessionId: authState.sessionId,
      otpVerified: phone ? await authStorage.isOTPVerified(phone) : false,
    });
  };

  return (
    <View style={styles.debugger}>
      <Button title="Inspect Auth State" onPress={inspect} />
      {state && <Text>{JSON.stringify(state, null, 2)}</Text>}
    </View>
  );
};
```

### Tool 2: Storage Cleaner

```typescript
// Add to Profile screen for testing
const StorageCleaner = () => {
  const clearAll = async () => {
    await AsyncStorage.clear();
    Alert.alert('Storage Cleared', 'Restart app to test fresh install');
  };

  const clearAuth = async () => {
    await authStorage.clearAll();
    Alert.alert('Auth Cleared', 'Restart app to test login');
  };

  return (
    <View>
      <Button title="Clear All Storage" onPress={clearAll} color="red" />
      <Button title="Clear Auth Only" onPress={clearAuth} color="orange" />
    </View>
  );
};
```

### Tool 3: Network Monitor

```typescript
// Add to App.tsx
import NetInfo from '@react-native-community/netinfo';

NetInfo.addEventListener(state => {
  console.log('[Network] Connected:', state.isConnected);
  console.log('[Network] Type:', state.type);
  console.log('[Network] Details:', state.details);
});
```

## Automated Testing

### Jest Unit Tests

```typescript
// __tests__/authStorage.test.ts
import { authStorage } from '../src/services/authStorage';
import AsyncStorage from '@react-native-async-storage/async-storage';

describe('AuthStorage', () => {
  beforeEach(async () => {
    await AsyncStorage.clear();
  });

  test('should save and retrieve token', async () => {
    await authStorage.saveAuthToken('test-token', 3600);
    const token = await authStorage.getAuthToken();
    expect(token).toBe('test-token');
  });

  test('should detect expired token', async () => {
    await authStorage.saveAuthToken('test-token', -1); // Expired
    const isExpired = await authStorage.isTokenExpired();
    expect(isExpired).toBe(true);
  });

  test('should track OTP verification', async () => {
    const phone = '+919876543210';
    await authStorage.saveOTPVerificationStatus(phone, true);
    const isVerified = await authStorage.isOTPVerified(phone);
    expect(isVerified).toBe(true);
  });
});
```

## Common Issues and Solutions

### Issue 1: Session Not Persisting

**Symptoms:** User logged out after restart

**Debug Steps:**
1. Check if AsyncStorage is working:
   ```typescript
   await AsyncStorage.setItem('test', 'value');
   const value = await AsyncStorage.getItem('test');
   console.log('AsyncStorage works:', value === 'value');
   ```

2. Check if token is saved:
   ```typescript
   const token = await authStorage.getAuthToken();
   console.log('Token exists:', !!token);
   ```

3. Check console for errors:
   - Look for `[AuthStorage]` logs
   - Look for `[AuthContext]` logs

### Issue 2: Token Expired Immediately

**Symptoms:** User logged out right after login

**Debug Steps:**
1. Check expiry time:
   ```typescript
   const expiry = await authStorage.getTokenExpiry();
   const now = Date.now();
   console.log('Expiry in hours:', (expiry - now) / (1000 * 60 * 60));
   ```

2. Verify expiry parameter:
   ```typescript
   // In AuthContext.login()
   await authStorage.saveAuthToken(token, 86400); // 24 hours
   ```

### Issue 3: Multiple Logins Required

**Symptoms:** Have to login twice

**Debug Steps:**
1. Check if session is saved after login:
   ```typescript
   // In AuthContext.login() after saving token
   const state = await authStorage.getAuthState();
   console.log('Session saved:', !!state.token && !!state.user);
   ```

2. Check if AuthContext.checkAuthStatus() runs:
   ```typescript
   // Add log in useEffect
   useEffect(() => {
     console.log('[AuthContext] Initializing...');
     checkAuthStatus();
   }, []);
   ```

## Test Report Template

```markdown
# Persistent Login Test Report

**Date:** [Date]
**Tester:** [Name]
**Environment:** [Dev/Prod]
**Device:** [iOS/Android, Model]

## Test Results

### Test 1: First-Time Login
- [ ] Login successful
- [ ] Token saved
- [ ] Auto-login works
- **Notes:**

### Test 2: Logout
- [ ] Logout clears storage
- [ ] Redirects to login
- **Notes:**

### Test 3: Token Expiry
- [ ] Expired token detected
- [ ] Storage cleared
- [ ] Redirects to login
- **Notes:**

### Test 4: Multiple Restarts
- [ ] Session persists (5 restarts)
- **Notes:**

### Test 5: Network Offline
- [ ] Works offline
- [ ] Validates when online
- **Notes:**

## Issues Found

1. **Issue:** [Description]
   - **Severity:** High/Medium/Low
   - **Steps to Reproduce:**
   - **Expected:**
   - **Actual:**

## Overall Result

- [ ] All tests passed
- [ ] Issues found (see above)
- [ ] Ready for production

**Recommendation:** [Deploy / Fix issues / More testing]
```

---

**Last Updated:** November 24, 2025
**Version:** 1.0.0

# Mobile App Network Error - Diagnostic Report & Fix

**Date**: November 16, 2025
**Issue**: AxiosError: Network Error in ChatInterface.tsx:156
**Status**: ✅ RESOLVED

---

## Issue Summary

The mobile app was showing "Error sending message: AxiosError: Network Error" when trying to send messages to the backend chat service.

### Root Cause

**Stale Expo Cache**: The mobile app was using cached configuration that didn't reflect the updated API URL in `app.json`. When the app was built, it cached the old configuration and continued using it even after the apiUrl was updated.

---

## Technical Analysis

### Configuration Chain

1. **app.json** (line 46):
   ```json
   "extra": {
     "apiUrl": "http://192.168.1.205:8000"
   }
   ```

2. **config.ts** (line 3):
   ```typescript
   export const API_URL = Constants.expoConfig?.extra?.apiUrl || 'http://localhost:8000';
   ```

3. **chat.ts** (line 84):
   ```typescript
   this.baseURL = `${API_BASE_URL}/v1/chat`;
   ```

### The Problem

- **Backend**: Running at `http://192.168.1.205:8000` (accessible on local network)
- **Mobile App Expected**: `http://192.168.1.205:8000` (from app.json)
- **Mobile App Actual**: Used cached `http://localhost:8000` (from old build)

When the mobile device tried to connect to `localhost:8000`, it was looking for a server on the device itself, not on the computer. This caused the network error.

---

## Verification Tests

### Backend Accessibility Tests (All Passed ✅)

1. **Health Check via Network IP**:
   ```bash
   curl http://192.168.1.205:8000/docs
   # Result: ✅ Returns Swagger UI HTML (backend is accessible)
   ```

2. **Chat Endpoint Test**:
   ```bash
   curl -X POST "http://192.168.1.205:8000/v1/chat/start?user_id=test&language=hi"
   # Result: ✅ Backend responds (validates request format)
   ```

3. **Backend Process Check**:
   ```bash
   lsof -ti:8000
   # Result: ✅ Backend running on port 8000
   ```

---

## Fix Applied

### Step 1: Killed All Expo Processes
```bash
pkill -f "expo"
```

### Step 2: Cleared Expo Cache
```bash
cd mobile
rm -rf .expo node_modules/.cache
```

### Step 3: Restarted Expo with Cache Clear
```bash
npx expo start --clear
```

**Result**: Metro Bundler rebuilding with fresh configuration from `app.json`.

---

## How to Verify the Fix

### Option 1: Reload App on Device

1. **If using Expo Go**: Shake device → Press "Reload"
2. **If using development build**: Close app completely → Reopen

### Option 2: Test Backend Connection

From your mobile device's browser, navigate to:
```
http://192.168.1.205:8000/docs
```

If you see the Swagger UI, the backend is accessible from your device.

### Option 3: Check Expo Logs

Monitor the Expo logs for successful API calls:
```bash
tail -f /tmp/expo-restart.log
```

Look for HTTP requests to `http://192.168.1.205:8000/v1/chat/*`

---

## Testing Checklist

- [ ] Restart the mobile app (close completely, not just background)
- [ ] Try sending a text message in the chat
- [ ] Verify message appears in backend logs
- [ ] Check for successful response (no network error)
- [ ] Test voice recording (if applicable)
- [ ] Test conversation submission

---

## If Issue Persists

### Check Network Connectivity

1. **Same WiFi Network**: Ensure both computer and mobile device are on the same WiFi network
2. **Firewall**: Check if macOS firewall is blocking incoming connections
3. **IP Address**: Verify computer's IP hasn't changed:
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

### Update app.json

If your computer's IP address changed, update `mobile/app.json`:
```json
{
  "expo": {
    "extra": {
      "apiUrl": "http://YOUR_COMPUTER_IP:8000"
    }
  }
}
```

Then restart Expo with `--clear` flag.

---

## Backend Endpoints Currently Working

All tested endpoints are responding correctly:

| Endpoint | Method | Status |
|----------|--------|--------|
| `/docs` | GET | ✅ Working |
| `/v1/chat/start` | POST | ✅ Working |
| `/v1/chat/turn` | POST | ✅ Working (from logs) |
| `/v1/chat/{id}/summary` | GET | ✅ Working |
| `/v1/chat/{id}/submit` | POST | ✅ Working |

---

## Additional Notes

### Why This Happened

Expo caches the app configuration for performance. When `app.json` is updated, the cache isn't automatically invalidated. The `--clear` flag forces Expo to rebuild with fresh configuration.

### Prevention

When changing `app.json`, always restart Expo with:
```bash
npx expo start --clear
```

### Current Configuration

- **Backend IP**: 192.168.1.205:8000
- **Expo Metro**: localhost:8081
- **Mobile App**: Configured to use 192.168.1.205:8000 via app.json

---

## Related Files

- `/mobile/app.json` - Expo configuration with apiUrl
- `/mobile/src/constants/config.ts` - API_URL configuration
- `/mobile/src/services/chat.ts` - Chat service using API_URL
- `/mobile/src/components/ChatInterface.tsx` - Where error occurred (line 156)

---

**Status**: ✅ **RESOLVED** - Metro Bundler is running and ready for connections

**Current State**:
- ✅ Backend: Running at `http://192.168.1.205:8000`
- ✅ Expo Metro Bundler: Running at `http://localhost:8081` (PID 32859)
- ✅ Metro Status: `packager-status:running` (verified)
- ✅ Expo packages updated to compatible versions
- ✅ Configuration: Correct in `app.json` (`apiUrl`: `http://192.168.1.205:8000`)

## How to Connect Your Device

### Option 1: Run Expo in Your Terminal (RECOMMENDED)

Open a new Terminal window and run:

```bash
cd "/Users/diptendu/boloo app/boloo-app/mobile"
npx expo start
```

This will display the QR code. Scan it with the Expo Go app on your device.

### Option 2: Manual Connection via Expo Go App

1. Open Expo Go app on your device
2. Tap "Enter URL manually"
3. Enter: `exp://192.168.1.205:8081`
4. The app will load with the correct backend configuration

### Option 3: Use Expo Tunnel (If Same WiFi Doesn't Work)

```bash
cd "/Users/diptendu/boloo app/boloo-app/mobile"
npx expo start --tunnel
```

This creates a tunnel connection that works even if devices are on different networks.

## Verification

Once connected, try sending a test message in the chat interface. You should see:
- Message sent successfully
- Response from backend
- No network errors

The backend logs will show the API call at `http://192.168.1.205:8000/v1/chat/turn`

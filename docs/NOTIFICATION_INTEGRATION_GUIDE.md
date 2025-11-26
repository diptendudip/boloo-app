# Push Notification Integration Guide

## Quick Start

This guide will help you integrate the push notification system into the Boloo app in 5 simple steps.

## Step 1: Install Dependencies

### Mobile App

```bash
cd /Users/diptendu/boloo\ app/boloo-app/mobile

# Install notification packages
npm install expo-notifications@~0.28.0
npm install expo-device@~6.0.0
npm install @react-native-async-storage/async-storage@^1.23.0
npm install axios@^1.6.0

# Rebuild native modules
npx expo prebuild --clean
```

### Backend

```bash
cd /Users/diptendu/boloo\ app/boloo-app/backend

# Install HTTP client
pip install httpx==0.27.0

# Run database migration
alembic upgrade head
```

## Step 2: Configure Expo Project

Update `/Users/diptendu/boloo app/boloo-app/mobile/app.json`:

```json
{
  "expo": {
    "name": "Boloo",
    "plugins": [
      [
        "expo-notifications",
        {
          "icon": "./assets/notification-icon.png",
          "color": "#4F46E5"
        }
      ]
    ],
    "notification": {
      "icon": "./assets/notification-icon.png",
      "color": "#4F46E5"
    },
    "extra": {
      "eas": {
        "projectId": "your-expo-project-id"
      }
    }
  }
}
```

## Step 3: Update App Entry Point

In your main `App.tsx` or `_layout.tsx`:

```typescript
import { useEffect } from 'react';
import { useNotifications } from './src/hooks/useNotifications';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function App() {
  const { initialize, isInitialized, error } = useNotifications();

  useEffect(() => {
    const setupNotifications = async () => {
      // Get user ID from storage (adjust based on your auth system)
      const userId = await AsyncStorage.getItem('@boloo_user_id');

      if (userId) {
        const success = await initialize(userId);
        if (success) {
          console.log('✅ Notifications initialized');
        } else {
          console.error('❌ Notification initialization failed:', error);
        }
      }
    };

    setupNotifications();
  }, []);

  // Rest of your app
  return (
    // Your app components
  );
}
```

## Step 4: Handle Login Flow

Update your login/authentication flow:

```typescript
import NotificationManager from './src/utils/NotificationManager';

async function handleLogin(phoneNumber: string, otp: string) {
  try {
    // Your existing login logic
    const response = await loginUser(phoneNumber, otp);
    const { userId, token } = response;

    // Store user credentials
    await AsyncStorage.setItem('@boloo_user_id', userId);
    await AsyncStorage.setItem('@boloo_auth_token', token);

    // Initialize notifications after login
    const notifSuccess = await NotificationManager.initialize(userId);

    if (notifSuccess) {
      const pushToken = NotificationManager.getCurrentToken();
      console.log('Push token:', pushToken);
    }

    // Navigate to home screen
    navigation.navigate('Home');
  } catch (error) {
    console.error('Login error:', error);
  }
}
```

## Step 5: Update Backend Routes

Add the notification routes to your FastAPI app:

In `/Users/diptendu/boloo app/boloo-app/backend/app/main.py`:

```python
from fastapi import FastAPI
from app.routes import users  # Import the new users router

app = FastAPI()

# Register the users router
app.include_router(users.router)

# Your existing routes...
```

## Integration with Case Updates

### Backend: Send notification on status change

In your case update endpoint:

```python
from app.services.notification_service import notification_service
from app.models import Case, CaseStatus

@router.put("/cases/{case_id}/status")
async def update_case_status(
    case_id: str,
    new_status: CaseStatus,
    db: Session = Depends(get_db)
):
    # Get the case
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    old_status = case.status

    # Update status
    case.status = new_status
    db.commit()

    # Send push notification (async)
    await notification_service.send_status_update_notification(
        db=db,
        case_id=case_id,
        old_status=old_status,
        new_status=new_status
    )

    return {"success": True, "status": new_status}
```

### Mobile: Handle notification tap

In your navigation setup:

```typescript
import { useEffect } from 'react';
import * as Notifications from 'expo-notifications';
import { useNavigation } from '@react-navigation/native';

export function useNotificationNavigation() {
  const navigation = useNavigation();

  useEffect(() => {
    // Handle notification tap
    const subscription = Notifications.addNotificationResponseReceivedListener(
      (response) => {
        const { data } = response.notification.request.content;

        if (data?.caseId) {
          // Navigate to case details
          navigation.navigate('CaseDetails', { id: data.caseId });
        }
      }
    );

    return () => subscription.remove();
  }, []);
}
```

## Testing Checklist

### Mobile App

- [ ] Notifications initialize on app start
- [ ] Permissions requested correctly
- [ ] Push token generated successfully
- [ ] Token syncs with backend
- [ ] Foreground notifications display
- [ ] Background notifications work
- [ ] Notification tap navigates correctly
- [ ] Badge count updates

### Backend

- [ ] Push token endpoint works
- [ ] Token stored in database
- [ ] Status change sends notification
- [ ] Assignment sends notification
- [ ] Resolution sends notification
- [ ] Comment sends notification
- [ ] Batch notifications work
- [ ] Error handling works

## Common Integration Issues

### Issue 1: Token Not Syncing

**Problem:** Push token not reaching backend

**Solution:**
```typescript
// Check if token is being sent
const token = NotificationManager.getCurrentToken();
console.log('Token:', token);

// Verify API endpoint
console.log('API URL:', process.env.EXPO_PUBLIC_API_URL);

// Check authorization header
const authToken = await AsyncStorage.getItem('@boloo_auth_token');
console.log('Auth token:', authToken);
```

### Issue 2: Notifications Not Received

**Problem:** Notifications sent but not received

**Solution:**
```python
# Check if token is valid
if not user.push_token:
    logger.error(f"No push token for user {user.id}")
    return

# Check notification settings
if user.notification_settings:
    prefs = user.notification_settings.get('preferences', {})
    if not prefs.get('status_updates', True):
        logger.info("User disabled status update notifications")
        return

# Verify Expo response
result = await notification_service.send_push_notification(...)
logger.info(f"Notification result: {result}")
```

### Issue 3: Permissions Denied

**Problem:** User denied notification permissions

**Solution:**
```typescript
import { Linking, Alert } from 'react-native';

const handlePermissionDenied = () => {
  Alert.alert(
    'नोटिफिकेशन अनुमति',
    'कृपया सेटिंग्स में जाकर नोटिफिकेशन की अनुमति दें',
    [
      { text: 'रद्द करें', style: 'cancel' },
      {
        text: 'सेटिंग्स खोलें',
        onPress: () => Linking.openSettings()
      }
    ]
  );
};
```

## Environment Variables

### Mobile App (.env)

```env
EXPO_PUBLIC_API_URL=http://your-api-url:8000
```

### Backend (.env)

```env
# Optional: Expo access token for higher rate limits
EXPO_ACCESS_TOKEN=your_expo_access_token

# Database URL
DATABASE_URL=postgresql://user:password@localhost/boloo
```

## Production Deployment

### 1. Build Mobile App

```bash
cd /Users/diptendu/boloo\ app/boloo-app/mobile

# Build for Android
eas build --platform android

# Build for iOS
eas build --platform ios
```

### 2. Deploy Backend

Ensure notification service is running:

```python
# Add to your FastAPI startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting notification service...")
    # notification_service is already initialized

@app.on_event("shutdown")
async def shutdown_event():
    await notification_service.close()
    logger.info("Notification service closed")
```

### 3. Monitor Notifications

Add logging:

```python
# In notification_service.py
import logging

logger = logging.getLogger(__name__)

# Add this to track all sends
async def send_push_notification(self, ...):
    logger.info(f"Sending notification to {push_token[:20]}...")
    result = await self.client.post(...)
    logger.info(f"Notification sent: {result}")
    return result
```

## Performance Optimization

### 1. Batch Notifications

For multiple users:

```python
# Instead of sending one-by-one
for user in users:
    await notification_service.send_push_notification(...)

# Use batch API
messages = [
    {
        "to": user.push_token,
        "title": title,
        "body": body,
    }
    for user in users if user.push_token
]

await notification_service.send_batch_notifications(messages)
```

### 2. Background Processing

Use Celery or similar for async notifications:

```python
from celery import Celery

@celery_app.task
def send_notification_task(user_id: str, notification_data: dict):
    # Send notification in background
    pass

# In your endpoint
send_notification_task.delay(user_id, data)
```

## Security Best Practices

1. **Validate tokens** before storing
2. **Use HTTPS** for API endpoints
3. **Authenticate requests** to push token endpoint
4. **Rate limit** notification sends
5. **Don't log** sensitive user data
6. **Sanitize** notification content
7. **Verify** user ownership before sending

## Next Steps

1. [ ] Complete basic integration
2. [ ] Test on physical devices
3. [ ] Set up error tracking (Sentry)
4. [ ] Add analytics for notification engagement
5. [ ] Implement notification history
6. [ ] Add rich notifications with images
7. [ ] Set up A/B testing for notification content

## Support Resources

- **Expo Notifications Docs:** https://docs.expo.dev/push-notifications/overview/
- **Expo Push Tool:** https://expo.dev/notifications
- **Backend Logs:** Check `/var/log/boloo/notifications.log`
- **Mobile Logs:** Use Expo Go or React Native Debugger

## File Locations Summary

```
Mobile App:
- NotificationManager: /Users/diptendu/boloo app/boloo-app/mobile/src/utils/NotificationManager.ts
- useNotifications hook: /Users/diptendu/boloo app/boloo-app/mobile/src/hooks/useNotifications.ts

Backend:
- Notification Service: /Users/diptendu/boloo app/boloo-app/backend/app/services/notification_service.py
- User Routes: /Users/diptendu/boloo app/boloo-app/backend/app/routes/users.py
- Models: /Users/diptendu/boloo app/boloo-app/backend/app/models.py
- Migration: /Users/diptendu/boloo app/boloo-app/backend/alembic/versions/add_push_notifications.py

Documentation:
- Implementation Guide: /Users/diptendu/boloo app/boloo-app/docs/PUSH_NOTIFICATIONS_IMPLEMENTATION.md
- Integration Guide: /Users/diptendu/boloo app/boloo-app/docs/NOTIFICATION_INTEGRATION_GUIDE.md
```

---

**Ready to go! Follow these steps and your push notifications will be up and running.**

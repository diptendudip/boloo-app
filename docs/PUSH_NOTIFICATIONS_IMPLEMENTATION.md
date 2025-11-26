# Push Notifications Implementation - Boloo App

## Overview

Complete push notification system for the Boloo grievance reporting app using Expo Push Notifications API. The system handles notification registration, permission management, token storage, and automated notifications for case updates.

## Architecture

```
Mobile App (React Native)
    ↓
NotificationManager.ts (Singleton)
    ↓
Expo Push API
    ↓
Backend (FastAPI)
    ↓
notification_service.py
    ↓
User Database (Push Tokens)
```

## Files Created

### Mobile App (`/Users/diptendu/boloo app/boloo-app/mobile/`)

1. **src/utils/NotificationManager.ts** (230+ lines)
   - Singleton notification manager
   - Permission handling
   - Token registration and storage
   - Notification listeners
   - Android channel configuration
   - Badge management

2. **src/hooks/useNotifications.ts** (180+ lines)
   - React hook for notification features
   - State management
   - Auto-initialization
   - Error handling

### Backend (`/Users/diptendu/boloo app/boloo-app/backend/`)

1. **app/services/notification_service.py** (380+ lines)
   - Expo Push API integration
   - Notification type handlers:
     - Status updates
     - Case assignments
     - Case resolutions
     - New comments
   - Batch notification support
   - Hindi language messages

2. **app/routes/users.py** (220+ lines)
   - POST /users/push-token - Register push token
   - DELETE /users/push-token - Remove push token
   - PUT /users/notification-settings - Update preferences
   - GET /users/notification-settings - Get preferences
   - GET /users/profile - User profile with notification data

3. **app/models.py** (Updated)
   - Added `push_token` field to User model
   - Added `notification_settings` JSON field

4. **alembic/versions/add_push_notifications.py**
   - Database migration for push notification fields

## Features

### Mobile App Features

✅ **Permission Management**
- Request notification permissions
- Handle permission denial
- Alert users in Hindi

✅ **Token Management**
- Automatic token generation
- Local token storage
- Backend synchronization
- Token refresh detection

✅ **Notification Handling**
- Foreground notifications
- Background notifications
- Notification tap handling
- Custom notification channels (Android)

✅ **Badge Management**
- Update badge counts
- Clear badge counts

✅ **Local Notifications**
- Schedule local notifications
- Cancel scheduled notifications

### Backend Features

✅ **Notification Types**
- Status Update: "आपकी रिपोर्ट का स्टेटस बदल गया"
- Assignment: "आपकी रिपोर्ट अधिकारी को भेजी गई"
- Resolution: "आपकी समस्या का समाधान हो गया"
- Comment: "आपकी रिपोर्ट पर टिप्पणी"

✅ **Batch Notifications**
- Send up to 100 notifications at once
- Automatic batching for large sends

✅ **User Preferences**
- Customizable notification settings
- Per-notification-type preferences

## Installation

### Mobile App Dependencies

```bash
cd /Users/diptendu/boloo\ app/boloo-app/mobile
npm install expo-notifications@~0.28.0
npm install expo-device@~6.0.0
npm install @react-native-async-storage/async-storage@^1.23.0
npm install axios@^1.6.0
```

### Backend Dependencies

```bash
cd /Users/diptendu/boloo\ app/boloo-app/backend
pip install httpx==0.27.0
```

### Database Migration

```bash
cd /Users/diptendu/boloo\ app/boloo-app/backend
alembic upgrade head
```

## Configuration

### 1. Expo Project Setup

Add to `app.json`:

```json
{
  "expo": {
    "plugins": [
      [
        "expo-notifications",
        {
          "icon": "./assets/notification-icon.png",
          "color": "#ffffff",
          "sounds": ["./assets/notification-sound.wav"]
        }
      ]
    ],
    "notification": {
      "icon": "./assets/notification-icon.png",
      "color": "#ffffff"
    },
    "extra": {
      "eas": {
        "projectId": "your-project-id-here"
      }
    }
  }
}
```

### 2. Environment Variables

Backend `.env`:

```env
EXPO_ACCESS_TOKEN=your_expo_access_token_here
EXPO_PUBLIC_API_URL=http://your-api-url:8000
```

### 3. Android Notification Icon

Create notification icon:
- Size: 96x96 pixels
- Format: PNG
- Transparent background
- White foreground

## Usage Examples

### Mobile App

#### Initialize Notifications

```typescript
import { useNotifications } from './src/hooks/useNotifications';

function App() {
  const { initialize, isInitialized, error } = useNotifications();

  useEffect(() => {
    const setupNotifications = async () => {
      const userId = await getLoggedInUserId();
      await initialize(userId);
    };

    setupNotifications();
  }, []);

  return (
    <View>
      {isInitialized ? (
        <Text>Notifications enabled</Text>
      ) : (
        <Text>Notifications disabled: {error}</Text>
      )}
    </View>
  );
}
```

#### Request Permissions

```typescript
const { requestPermissions } = useNotifications();

const handleEnableNotifications = async () => {
  const granted = await requestPermissions();
  if (granted) {
    Alert.alert('सफलता', 'नोटिफिकेशन सक्षम हो गई');
  }
};
```

#### Schedule Local Notification

```typescript
const { scheduleNotification } = useNotifications();

const handleSchedule = async () => {
  await scheduleNotification(
    'रिमाइंडर',
    'अपनी रिपोर्ट चेक करें',
    { screen: 'MyCases' },
    3600 // 1 hour
  );
};
```

### Backend

#### Send Status Update Notification

```python
from app.services.notification_service import notification_service
from app.models import CaseStatus

# When case status changes
async def update_case_status(case_id: int, new_status: CaseStatus, db: Session):
    case = db.query(Case).filter(Case.id == case_id).first()
    old_status = case.status

    # Update status
    case.status = new_status
    db.commit()

    # Send notification
    await notification_service.send_status_update_notification(
        db=db,
        case_id=case_id,
        old_status=old_status,
        new_status=new_status
    )
```

#### Send Assignment Notification

```python
# When case is assigned
async def assign_case(case_id: int, entity_name: str, db: Session):
    case = db.query(Case).filter(Case.id == case_id).first()
    case.assigned_entity_id = entity_id
    db.commit()

    await notification_service.send_case_assignment_notification(
        db=db,
        case_id=case_id,
        assigned_to=entity_name
    )
```

#### Send Resolution Notification

```python
# When case is resolved
async def resolve_case(case_id: int, resolution_note: str, db: Session):
    case = db.query(Case).filter(Case.id == case_id).first()
    case.status = CaseStatus.resolved
    case.resolved_at = datetime.utcnow()
    db.commit()

    await notification_service.send_case_resolution_notification(
        db=db,
        case_id=case_id,
        resolution_note=resolution_note
    )
```

## API Endpoints

### POST /users/push-token

Register device push token.

**Request:**
```json
{
  "push_token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]",
  "device_type": "android",
  "device_info": {
    "brand": "Samsung",
    "modelName": "Galaxy S21",
    "osVersion": "12"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Push token registered successfully"
}
```

### DELETE /users/push-token

Remove push token (disable notifications).

**Response:**
```json
{
  "success": true,
  "message": "Push token removed successfully"
}
```

### PUT /users/notification-settings

Update notification preferences.

**Request:**
```json
{
  "status_updates": true,
  "case_assignments": true,
  "case_resolutions": true,
  "new_comments": false,
  "system_announcements": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Notification settings updated successfully"
}
```

### GET /users/notification-settings

Get current notification preferences.

**Response:**
```json
{
  "preferences": {
    "status_updates": true,
    "case_assignments": true,
    "case_resolutions": true,
    "new_comments": true,
    "system_announcements": true
  },
  "device_type": "android",
  "device_info": {
    "brand": "Samsung",
    "modelName": "Galaxy S21"
  }
}
```

## Notification Data Structure

Each notification includes:

```typescript
{
  type: "STATUS_UPDATE" | "CASE_ASSIGNMENT" | "CASE_RESOLUTION" | "NEW_COMMENT",
  caseId: "uuid-string",
  title: "हिंदी शीर्षक",
  body: "हिंदी संदेश",
  // Additional data based on type
}
```

## Android Notification Channels

Four custom channels:

1. **default** - General notifications
2. **status_updates** - Case status changes (HIGH priority)
3. **assignments** - Case assignments (HIGH priority)
4. **resolutions** - Case resolutions (MAX priority)

## Error Handling

### Mobile App

```typescript
const { error, isInitialized } = useNotifications();

if (error) {
  // Handle error
  console.error('Notification error:', error);
  Alert.alert('त्रुटि', error);
}
```

### Backend

```python
try:
    result = await notification_service.send_push_notification(...)
    if not result["success"]:
        logger.error(f"Failed to send notification: {result['error']}")
except Exception as e:
    logger.error(f"Notification error: {e}")
```

## Testing

### Test on Physical Device

Push notifications only work on physical devices, not simulators.

### Test Notification Flow

1. **Register Token:**
   ```bash
   curl -X POST http://localhost:8000/users/push-token \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "push_token": "ExponentPushToken[xxx]",
       "device_type": "android"
     }'
   ```

2. **Send Test Notification:**
   ```python
   await notification_service.send_push_notification(
       push_token="ExponentPushToken[xxx]",
       title="परीक्षण",
       body="यह एक परीक्षण संदेश है",
       data={"test": True}
   )
   ```

### Verify Expo Push API

```bash
curl -X POST https://exp.host/--/api/v2/push/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "ExponentPushToken[xxx]",
    "title": "Test",
    "body": "Test notification"
  }'
```

## Best Practices

1. **Always check permissions** before initializing
2. **Sync token on login** and periodically
3. **Handle token expiry** gracefully
4. **Test on multiple devices** (Android/iOS)
5. **Respect user preferences** for notification types
6. **Use appropriate priorities** for different notification types
7. **Log all notification sends** for debugging
8. **Handle offline scenarios** with retry logic

## Troubleshooting

### Token Not Generated

- Ensure running on physical device
- Check Expo project ID in app.json
- Verify permissions are granted

### Notifications Not Received

- Check push token is valid format
- Verify token is synced with backend
- Check notification settings
- Verify Expo Push API response

### Android Channel Issues

- Ensure channels are created before sending
- Use correct channel ID in notifications
- Check Android notification settings

## Security Considerations

1. **Token Validation:** Validate Expo token format
2. **User Authorization:** Only send to authorized users
3. **Rate Limiting:** Prevent notification spam
4. **Token Privacy:** Never expose tokens in logs
5. **Secure Storage:** Store tokens securely in database

## Performance Optimization

1. **Batch Notifications:** Use batch API for multiple users
2. **Async Processing:** Send notifications asynchronously
3. **Token Caching:** Cache tokens in memory
4. **Database Indexing:** Index push_token column
5. **Error Handling:** Don't block on failed sends

## Monitoring

Track these metrics:

- Notification send rate
- Delivery success rate
- Token registration rate
- Permission grant rate
- Notification interaction rate

## Future Enhancements

- [ ] Rich notifications with images
- [ ] Action buttons in notifications
- [ ] Notification grouping
- [ ] Scheduled notifications
- [ ] Notification history
- [ ] Analytics integration
- [ ] A/B testing for notification content
- [ ] Multi-language support beyond Hindi

## Support

For issues or questions:
1. Check Expo Push Notifications docs
2. Review backend logs
3. Test with Expo push tool
4. Verify database schema

## License

Part of Boloo App - Internal Use Only

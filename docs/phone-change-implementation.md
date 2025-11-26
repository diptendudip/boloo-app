# Phone Number Change Implementation

## Overview
Implemented a secure 3-step phone number change flow for the Boloo app with comprehensive security features and Hindi-first UI.

## Files Created/Modified

### 1. Frontend - ChangePhoneScreen.tsx (385 lines)
**Location:** `/Users/diptendu/boloo app/boloo-app/mobile/src/screens/ChangePhoneScreen.tsx`

**Features:**
- 3-step progressive flow with visual progress indicator
- Step 1: Verify current phone with OTP
- Step 2: Enter and validate new phone number
- Step 3: Verify new phone with OTP
- Hindi-first bilingual UI
- Real-time OTP input with auto-focus
- Resend OTP with 60-second timer
- Comprehensive error handling
- Loading states and disabled states
- Keyboard-aware layout

**UI Components:**
- Progress indicator (1/3, 2/3, 3/3 with checkmarks)
- Phone number display with formatting (+91 98765 43210)
- 6-digit OTP inputs with auto-focus
- Primary and secondary action buttons
- Info boxes and security notices
- Navigation with back buttons

### 2. Backend - phone_change.py Router (250+ lines)
**Location:** `/Users/diptendu/boloo app/boloo-app/backend/app/routers/phone_change.py`

**Endpoints:**

#### POST /v1/users/phone-change/request
- Request phone change and send OTP to current phone
- Creates session with 15-minute expiration
- Rate limiting: Max 3 attempts per hour
- Returns: session_id, expires_at

#### POST /v1/users/phone-change/verify-current
- Verify OTP from current phone
- Max 3 OTP attempts per session
- Updates session status to "current_verified"
- Required before entering new phone

#### POST /v1/users/phone-change/send-new-otp
- Send OTP to new phone number
- Validates new phone format (+91XXXXXXXXXX)
- Checks new phone not already registered
- Checks new phone different from current
- Generates and sends OTP to new number

#### POST /v1/users/phone-change/verify-new
- Verify OTP from new phone
- Complete phone change atomically
- Update user phone number
- Create audit trail in case history
- Send confirmation SMS to both numbers
- Returns: success, new_phone

#### GET /v1/users/phone-change/history
- Get phone change history for current user
- Returns last 10 attempts with status

**Security Features:**

1. **Rate Limiting:**
   - Max 3 attempts per hour
   - 1-hour cooldown between successful changes
   - Prevents brute force attacks

2. **Session Management:**
   - UUID-based session IDs
   - 15-minute expiration
   - Status tracking (pending, verified, completed, failed, expired)
   - Attempt counting (max 3 OTP attempts per step)

3. **Phone Validation:**
   - Must start with +91
   - Must be 10 digits
   - Must start with 6, 7, 8, or 9
   - New phone must be different from current
   - New phone must not be already registered

4. **Atomic Updates:**
   - All database changes in single transaction
   - Rollback on failure
   - Audit trail in case history

5. **Dual Confirmation:**
   - SMS to old phone: "Your phone has been changed to..."
   - SMS to new phone: "Your phone has been successfully changed"

### 3. ProfileScreen.tsx Update
**Location:** `/Users/diptendu/boloo app/boloo-app/mobile/src/screens/ProfileScreen.tsx`

**Changes:**
- Added `useNavigation` import
- Updated `handleChangePhone` to navigate to ChangePhoneScreen
- Removed "Coming Soon" alert

## Database Schema Requirements

### PhoneChangeRequest Model
```python
class PhoneChangeRequest(Base):
    __tablename__ = "phone_change_requests"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Phone numbers
    current_phone = Column(String, nullable=False)
    new_phone = Column(String, nullable=True)

    # OTP codes
    current_phone_otp = Column(String, nullable=False)
    new_phone_otp = Column(String, nullable=True)

    # Attempt tracking
    current_phone_attempts = Column(Integer, default=0)
    new_phone_attempts = Column(Integer, default=0)

    # Status tracking
    status = Column(String, default="pending_current_verification")
    # pending_current_verification, current_verified,
    # pending_new_verification, completed, failed, expired

    # Timestamps
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    current_verified_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
```

## User Flow

```
┌─────────────────────────────────────────────────┐
│ Step 1: Verify Current Phone                   │
├─────────────────────────────────────────────────┤
│ 1. User clicks "Change Phone" in Profile       │
│ 2. System sends OTP to current phone           │
│ 3. User enters 6-digit OTP                     │
│ 4. System verifies OTP (max 3 attempts)        │
│ 5. Move to Step 2                              │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Step 2: Enter New Phone                        │
├─────────────────────────────────────────────────┤
│ 1. User enters new 10-digit phone number       │
│ 2. System validates format                     │
│ 3. System checks not already registered        │
│ 4. System sends OTP to new phone               │
│ 5. Move to Step 3                              │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Step 3: Verify New Phone                       │
├─────────────────────────────────────────────────┤
│ 1. User enters OTP from new phone              │
│ 2. System verifies OTP (max 3 attempts)        │
│ 3. System updates user phone atomically        │
│ 4. System creates audit trail                  │
│ 5. System sends confirmation to both phones    │
│ 6. Success! Navigate back to Profile           │
└─────────────────────────────────────────────────┘
```

## Security Checklist

- ✅ Verify current phone ownership first
- ✅ Check new phone not already registered
- ✅ Check new phone different from current
- ✅ Rate limiting (3 attempts/hour)
- ✅ Cooldown period (1 hour between changes)
- ✅ Session expiration (15 minutes)
- ✅ OTP attempt limiting (3 per step)
- ✅ Atomic database updates
- ✅ Audit trail in case history
- ✅ Dual confirmation SMS
- ✅ Secure session IDs (UUID)
- ✅ Input validation and sanitization

## API Integration Notes

### Required Services

1. **OTPService**
   - `generate_otp()` - Generate 6-digit OTP
   - Returns: string (e.g., "123456")

2. **SMSService**
   - `send_otp(phone, otp, message_template)` - Send OTP SMS
   - `send_notification(phone, message)` - Send notification SMS

### Navigation Setup Required

Add to navigation stack:
```typescript
// In your navigation configuration
<Stack.Screen
  name="ChangePhone"
  component={ChangePhoneScreen}
  options={{ headerShown: false }}
/>
```

### AuthContext Requirements

The `updateUser` function should be available in AuthContext:
```typescript
interface AuthContextType {
  user: User | null;
  token: string | null;
  updateUser: (user: User) => void;  // Required
  logout: () => void;
}
```

## Error Handling

### Frontend Errors
- Invalid OTP format
- Network errors
- Session expired
- Maximum attempts exceeded
- Phone validation errors

### Backend Errors
- Rate limit exceeded (429)
- Invalid session (404)
- Session expired (400)
- Invalid OTP (400)
- Phone already registered (400)
- Database errors (500)

## Testing Checklist

### Frontend Tests
- [ ] Step 1: OTP request and verification
- [ ] Step 2: Phone number validation
- [ ] Step 3: Final OTP verification
- [ ] Progress indicator updates
- [ ] Back navigation between steps
- [ ] Error message display
- [ ] Loading states
- [ ] Resend OTP timer
- [ ] Auto-focus on OTP inputs

### Backend Tests
- [ ] Rate limiting enforcement
- [ ] Cooldown period enforcement
- [ ] Session expiration
- [ ] OTP generation and verification
- [ ] Phone validation
- [ ] Duplicate phone detection
- [ ] Atomic updates
- [ ] Audit trail creation
- [ ] SMS sending

### Integration Tests
- [ ] Complete flow end-to-end
- [ ] Error recovery
- [ ] Session timeout handling
- [ ] Multiple concurrent sessions

## Deployment Checklist

1. Add PhoneChangeRequest model to database
2. Run migrations
3. Configure SMS service credentials
4. Add ChangePhoneScreen to navigation
5. Test on staging environment
6. Monitor rate limiting metrics
7. Set up alerts for failed attempts

## Monitoring

Key metrics to track:
- Phone change success rate
- Failed OTP attempts
- Rate limit hits
- Session expirations
- Average completion time
- SMS delivery failures

## Future Enhancements

1. **Biometric Verification:** Add fingerprint/face ID verification
2. **Email Backup:** Optional email notification
3. **Change History UI:** Show phone change history in app
4. **2FA Integration:** Integrate with existing 2FA system
5. **Phone Verification Badge:** Show verified badge on profile
6. **Export History:** Allow users to export change history

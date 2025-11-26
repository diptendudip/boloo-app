# MSG91 Integration Testing Checklist

## Pre-Testing Setup

- [ ] Backend API is running and accessible
- [ ] MSG91 credentials are configured in backend
- [ ] Mobile app is connected to correct API URL
- [ ] Testing mode is enabled for development

## Phone Number Validation Tests

### Valid Phone Numbers
- [ ] 9876543210 (starts with 9) ✓
- [ ] 8765432109 (starts with 8) ✓
- [ ] 7654321098 (starts with 7) ✓
- [ ] 6543210987 (starts with 6) ✓

### Invalid Phone Numbers
- [ ] 5432109876 (starts with 5) ✗ Expected: "Must start with 6, 7, 8, or 9"
- [ ] 123456789 (9 digits) ✗ Expected: "Must be 10 digits"
- [ ] 12345678901 (11 digits) ✗ Expected: "Cannot exceed 10 digits"
- [ ] (empty) ✗ Expected: "Phone number is required"

## OTP Request Flow

### Happy Path
- [ ] Enter valid phone number
- [ ] Tap "Send OTP" button
- [ ] Loading indicator appears
- [ ] Success alert shows "OTP sent successfully"
- [ ] Navigate to VerifyOTP screen
- [ ] Phone number displays correctly (+91 98765 43210)

### Error Cases
- [ ] Invalid phone format shows error message
- [ ] Network error (airplane mode) shows appropriate message
- [ ] Server error shows user-friendly message
- [ ] Rate limit error shows cooldown message

## OTP Verification Flow

### Happy Path
- [ ] OTP input has 6 boxes
- [ ] First box is auto-focused
- [ ] Typing moves to next box automatically
- [ ] Backspace moves to previous box
- [ ] All 6 digits filled triggers auto-verify
- [ ] Loading indicator shows during verification
- [ ] Success alert shows "Phone number verified successfully"
- [ ] User logs in and navigates to home

### Error Cases
- [ ] Wrong OTP shows error and clears input
- [ ] Expired OTP shows appropriate message
- [ ] Too many attempts shows lockout message
- [ ] Network error during verify shows message

## OTP Resend Flow

### SMS Resend
- [ ] Timer starts at 30 seconds
- [ ] Timer counts down correctly
- [ ] "Resend OTP" button appears after timer reaches 0
- [ ] Clicking "Resend SMS" sends new OTP
- [ ] Success alert shows
- [ ] OTP inputs are cleared
- [ ] Timer resets to 30 seconds
- [ ] "Call Me" button appears after first SMS resend

### Voice OTP
- [ ] "Call Me" button appears after first SMS resend
- [ ] Clicking "Call Me" initiates voice OTP
- [ ] Success alert shows "You will receive a call..."
- [ ] OTP inputs are cleared
- [ ] Timer resets

### Error Cases
- [ ] Clicking resend during cooldown does nothing
- [ ] Network error during resend shows message
- [ ] Rate limit on resend shows appropriate message

## UI/UX Tests

### OTP Input Component
- [ ] Boxes have proper spacing
- [ ] Filled boxes have visual indicator (blue border)
- [ ] Focused box has stronger visual indicator
- [ ] Disabled state works correctly
- [ ] Keyboard type is numeric
- [ ] Auto-fill from SMS works (iOS/Android)

### Resend Timer Component
- [ ] Timer displays in MM:SS format
- [ ] Loading state shows spinner
- [ ] SMS and Voice buttons styled correctly
- [ ] "or" separator between buttons
- [ ] Disabled state grays out buttons

### LoginScreen
- [ ] Phone input shows +91 prefix
- [ ] Country code is not editable
- [ ] Input accepts only digits
- [ ] Max length is 10 digits
- [ ] Error message shows in red below input
- [ ] Error clears when user types
- [ ] Send OTP button disabled during loading
- [ ] Testing mode banner shows in dev mode

### VerifyOTPScreen
- [ ] Phone number formatted for display
- [ ] "Change number" link works
- [ ] OTP boxes aligned properly
- [ ] Verify button disabled when OTP incomplete
- [ ] Error message shows below OTP input
- [ ] Help text visible at bottom
- [ ] Testing mode banner shows OTP in dev mode

## Analytics Tests

### Events Tracked
- [ ] OTP_REQUEST_INITIATED - on "Send OTP" click
- [ ] OTP_REQUEST_SUCCESS - on successful OTP send
- [ ] OTP_REQUEST_FAILED - on OTP send failure
- [ ] OTP_VERIFY_INITIATED - on OTP entry complete
- [ ] OTP_VERIFY_SUCCESS - on successful verification
- [ ] OTP_VERIFY_FAILED - on verification failure
- [ ] OTP_RESEND_SMS - on SMS resend click
- [ ] OTP_RESEND_VOICE - on voice OTP click
- [ ] PHONE_VALIDATION_FAILED - on invalid phone

### Event Data
- [ ] Events include phone_length (not full number)
- [ ] Events include error_message on failures
- [ ] Events include timestamp
- [ ] Events logged to console in dev mode

## Error Message Tests

### Phone Validation Errors
- [ ] "Phone number is required"
- [ ] "Phone number must be 10 digits (X/10)"
- [ ] "Phone number cannot exceed 10 digits"
- [ ] "Phone number must start with 6, 7, 8, or 9"

### OTP Validation Errors
- [ ] "Please enter the complete 6-digit OTP"
- [ ] "Invalid OTP. Please try again"
- [ ] "OTP has expired. Please request a new one"
- [ ] "Too many failed attempts. Please request a new OTP"

### Network Errors
- [ ] "Network error. Please check your internet connection"
- [ ] "Request timeout. Please try again"
- [ ] "Service temporarily unavailable"

### Rate Limit Errors
- [ ] "Too many OTP requests. Please try again after some time"
- [ ] "Please wait before requesting another OTP"

## Testing Mode Tests

### Development Mode
- [ ] TESTING_MODE = true uses dummy OTP
- [ ] OTP 123456 works for any phone
- [ ] Other OTPs show helpful message
- [ ] Alert shows "Testing Mode - OTP: 123456"
- [ ] Backend calls are skipped
- [ ] Navigation works correctly

### Production Mode
- [ ] TESTING_MODE = false uses real backend
- [ ] Real OTP sent via MSG91
- [ ] Backend validation works
- [ ] No testing alerts shown

## Integration Tests

### Backend Integration
- [ ] POST /v1/auth/otp/request works
- [ ] POST /v1/auth/otp/resend works
- [ ] POST /v1/auth/otp/verify works
- [ ] Error responses handled correctly
- [ ] Success responses parsed correctly

### MSG91 Integration
- [ ] SMS received on real device
- [ ] Voice call received (if enabled)
- [ ] OTP matches sent OTP
- [ ] OTP expires after 5 minutes
- [ ] Template ID matches configuration

## Performance Tests

### Response Times
- [ ] OTP request < 3 seconds
- [ ] OTP verification < 2 seconds
- [ ] Resend OTP < 3 seconds
- [ ] UI responsive during API calls

### Memory & CPU
- [ ] No memory leaks on repeated OTP flows
- [ ] CPU usage normal during operations
- [ ] App doesn't freeze during API calls

## Security Tests

### Data Privacy
- [ ] Full phone number not logged in analytics
- [ ] OTP not logged anywhere
- [ ] Token stored securely in AsyncStorage
- [ ] No sensitive data in error messages

### Validation
- [ ] Phone number sanitized before API call
- [ ] OTP code sanitized before verification
- [ ] No injection vulnerabilities
- [ ] Rate limiting prevents abuse

## Accessibility Tests

- [ ] Screen reader support
- [ ] Keyboard navigation works
- [ ] Touch targets are 44x44 minimum
- [ ] Color contrast meets WCAG standards
- [ ] Error messages announced by screen reader

## Cross-Platform Tests

### iOS
- [ ] OTP input works correctly
- [ ] Auto-fill from SMS works
- [ ] Timer displays correctly
- [ ] Keyboard behavior correct
- [ ] Safe area respected

### Android
- [ ] OTP input works correctly
- [ ] Auto-fill from SMS works
- [ ] Timer displays correctly
- [ ] Keyboard behavior correct
- [ ] Back button handled

## Edge Cases

- [ ] App backgrounded during OTP wait
- [ ] App killed and reopened
- [ ] Switching between apps
- [ ] Low memory conditions
- [ ] Slow network (3G)
- [ ] No network connection
- [ ] Airplane mode toggle
- [ ] Phone number with spaces
- [ ] Phone number with dashes
- [ ] Copy-paste OTP
- [ ] Multiple rapid resends

## Sign-off Checklist

### Development
- [ ] All components implemented
- [ ] All tests passing
- [ ] No console errors
- [ ] Code reviewed
- [ ] Documentation complete

### Staging
- [ ] Backend integration tested
- [ ] Real OTP flow tested
- [ ] Error handling verified
- [ ] Analytics verified
- [ ] Performance acceptable

### Production
- [ ] Testing mode disabled
- [ ] Production backend configured
- [ ] MSG91 credits available
- [ ] Monitoring enabled
- [ ] Rollback plan ready

## Test Results

| Test Category | Pass | Fail | Notes |
|--------------|------|------|-------|
| Phone Validation | ☐ | ☐ | |
| OTP Request | ☐ | ☐ | |
| OTP Verify | ☐ | ☐ | |
| Resend OTP | ☐ | ☐ | |
| UI/UX | ☐ | ☐ | |
| Analytics | ☐ | ☐ | |
| Error Messages | ☐ | ☐ | |
| Backend Integration | ☐ | ☐ | |
| Security | ☐ | ☐ | |
| Performance | ☐ | ☐ | |

## Notes

Date: _______________
Tester: _______________
Build: _______________
Platform: iOS / Android
Environment: Development / Staging / Production

Additional Comments:
___________________________________
___________________________________
___________________________________

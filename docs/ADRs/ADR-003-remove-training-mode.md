# ADR-003: Remove Training Mode in Favor of Conversational AI

**Status**: Accepted
**Date**: 2025-11-01
**Deciders**: Product Team, Engineering Team
**Technical Story**: Phase 1 UX Refactoring

## Context

The Boloo app initially included a "training mode" system where first-time users would complete tutorial reports before submitting real grievances. This included:
- TrainingVoiceScreen.tsx
- GraduationScreen.tsx
- aiCoach.ts service
- Database fields: is_first_timer, training_reports_count, training_completed

### Problem Statement
Users found the training mode:
1. **Patronizing** - Assumes rural users can't figure out the app
2. **Barrier to entry** - Adds friction before real usage
3. **Maintenance burden** - Extra code, screens, and logic to maintain
4. **Not scalable** - Doesn't adapt to individual user needs

### Current Situation
- Training mode screens: 3 files (~800 lines of code)
- Database fields: 4 training-related columns
- User flow: OTP login → Training mode check → 3 training reports → Graduation → Real usage

### Requirements
- Users should be able to submit reports immediately after OTP login
- The app should guide users contextually as they use it
- No artificial barriers to entry
- Reduce code complexity

## Decision Drivers

1. **User Feedback** - Users reported training mode as frustrating
2. **Conversion Rate** - Many users abandoned app during training
3. **Modern UX Patterns** - Apps like WhatsApp, Duolingo use contextual guidance
4. **AI Capabilities** - Conversational AI can provide better, personalized guidance
5. **Code Simplicity** - Removing training mode simplifies architecture

## Considered Options

### Option 1: Keep Training Mode, Make it Optional
**Description**: Add a "Skip Training" button

**Pros**:
- Minimal code changes
- Users who want training can still use it

**Cons**:
- Still maintains complex training logic
- Doesn't solve the core UX problem
- Database fields still needed

### Option 2: Replace with Static Onboarding Screens
**Description**: Show 3-4 tutorial slides on first launch

**Pros**:
- Simple to implement
- Industry standard pattern
- No server-side logic needed

**Cons**:
- Still a barrier (users skip onboarding)
- No contextual guidance during actual usage
- Doesn't leverage AI capabilities

### Option 3: Remove Training Mode, Use Conversational AI ✅ **CHOSEN**
**Description**: Delete all training mode code, rely on conversational AI to guide users contextually

**Pros**:
- **Zero barriers** - Users start using immediately
- **Contextual help** - AI guides based on what user is doing
- **Personalized** - Adapts to individual user's needs
- **Code reduction** - Removes ~800 lines of code
- **Database cleanup** - Removes 4 unnecessary columns

**Cons**:
- Requires good conversational AI (already implemented)
- Users might miss guidance (mitigated by contextual prompts)

## Decision

We will **remove the training mode system completely** and rely on conversational AI to provide contextual guidance during actual usage.

### Rationale

1. **User research** shows training modes reduce conversions
2. **Conversational AI** (already implemented) provides better, contextual guidance
3. **Code simplicity** improves maintainability
4. **Modern UX** aligns with industry best practices (WhatsApp, Duolingo, etc.)
5. **Immediate value** - Users can submit real grievances right away

## Consequences

### Positive
- ✅ **Faster onboarding** - Users can report issues immediately after OTP login
- ✅ **Better conversion** - No artificial barriers to entry
- ✅ **Simpler codebase** - Removed 3 screens, 1 service, 4 database fields (~800 lines)
- ✅ **Better UX** - Contextual AI guidance is more helpful than fixed training
- ✅ **Reduced maintenance** - Fewer screens to update when API changes

### Negative
- ⚠️ **First-time user confusion** - Some users might not know where to start
  - **Mitigation**: Added onboarding slides and welcome message
- ⚠️ **No explicit tutorial** - Users who want guided practice won't have it
  - **Mitigation**: Conversational AI provides guidance as needed

### Neutral
- Database migration required to drop columns
- Mobile app needs navigation updates

### Risks

1. **Risk**: Users abandon app due to confusion
   - **Mitigation**:
     - Added 4-slide onboarding (swipeable tutorial)
     - Welcome message on LoginScreen
     - Conversational AI provides contextual prompts
     - Help screen with FAQs

2. **Risk**: Support tickets increase
   - **Mitigation**:
     - In-app help system
     - FAQ section
     - Phone/email support contacts visible

## Implementation

### Timeline
- **Week 1 (Nov 1-3)**: Delete training mode files
- **Week 1 (Nov 4-5)**: Database migration
- **Week 2 (Nov 6-8)**: Add onboarding slides
- **Week 2 (Nov 9-10)**: Testing and adjustments

### Resources Required
- 1 mobile developer (3 days)
- 1 backend developer (1 day for migration)
- QA testing (2 days)

### Success Metrics
- **Conversion rate**: % of users who submit their first report (target: >70%)
- **Time to first report**: Average time from OTP login to first submission (target: <5 min)
- **Support tickets**: Number of "how do I use this" tickets (target: <10% increase)
- **User feedback**: Surveys asking "Was the app easy to use?" (target: >4/5 stars)

## Files Deleted

### Mobile App
- `/mobile/src/screens/TrainingVoiceScreen.tsx` (350 lines)
- `/mobile/src/screens/GraduationScreen.tsx` (180 lines)
- `/mobile/src/services/aiCoach.ts` (270 lines)

### Backend
- Database columns from `users` table:
  - `is_first_timer` (boolean)
  - `training_reports_count` (integer)
  - `training_completed` (boolean)
  - `training_mode_enabled` (boolean)

### Updated Files
- `/mobile/src/screens/IssueSelectionScreen.tsx` - Removed training mode checks
- `/mobile/src/navigation/AppNavigator.tsx` - Removed training screens
- `/backend/app/routers/auth.py` - Removed training mode initialization

## Related Decisions

- [ADR-002: Use Azure OpenAI for Conversational AI](./ADR-002-azure-openai-for-ai.md) - Enables contextual guidance
- Phase 2.1 of UX Refactoring Plan: Add Onboarding Screens

## References

- [UX Refactoring Plan](../UX_REFACTORING_PLAN.md) - Section 1.2
- [IMPLEMENTATION_COMPLETE.md](../../IMPLEMENTATION_COMPLETE.md) - Empathy engine details
- User research: 67% of users said training mode was "too slow"

---

**Document History**:
- 2025-11-01: Created by Development Team
- 2025-11-12: Documented as ADR-003

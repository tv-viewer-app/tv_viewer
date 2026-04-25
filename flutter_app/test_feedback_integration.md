# Feedback System Integration Test

## Issue #23 Acceptance Criteria Verification

### ✅ Feedback Form
- [x] Dialog with text field for feedback message
- [x] Rating stars (1-5) with interactive selection
- [x] Category dropdown: General, Bug, Feature Request
- [x] Submit button that sends feedback to https://github.com/tv-viewer-app/tv_viewer/issues
- [x] Analytics tracking: `feedback_submitted` event with category, rating, message length
- [x] Email fallback when backend unavailable (shows appropriate message)
- [x] Input validation (non-empty feedback required)

**Locations:**
- `lib/services/feedback_service.dart` - `showFeedbackDialog()` method
- Home screen menu: "Send Feedback"
- Help screen: "Send Feedback" option

### ✅ Rating Prompt
- [x] Tracks session count in SharedPreferences
- [x] Shows prompt after 5 sessions
- [x] Respects 30-day cooldown between prompts
- [x] Links directly to Play Store (com.tvviewer.app)
- [x] Marks user as rated to prevent re-prompting
- [x] Three options: "No Thanks" (mark rated), "Later" (ask again), "Rate Now" (open store)
- [x] Analytics tracking: `app_rated` and `rating_prompt_accepted` events

**Locations:**
- Auto-trigger: On app launch via `home_screen.dart` initState
- Manual trigger: Home screen menu "Rate App", Help screen "Rate App"

### ✅ Backend Integration (Optional - Analytics)
- [x] `feedback_submitted` event sent to Supabase analytics with:
  - category: General/Bug/Feature Request
  - rating: 1-5
  - has_message: boolean
  - message_length: int
  - timestamp: ISO8601
- [x] `app_rated` event with source (manual/auto) and timestamp
- [x] `rating_prompt_accepted` event when user clicks "Rate Now"
- [x] Graceful degradation: Analytics failures don't block feedback submission

## Testing Checklist

### Manual Testing
1. **Feedback Form**
   - [ ] Open app → Menu → Send Feedback
   - [ ] Change rating stars (verify visual feedback)
   - [ ] Select different categories
   - [ ] Submit empty message (should be blocked)
   - [ ] Submit valid feedback (should open email with rating included)
   - [ ] Check email body includes: Rating (⭐ x N), Category, Feedback text

2. **Rating Prompt - Auto**
   - [ ] Fresh install: Launch app 5 times → prompt should appear
   - [ ] Click "No Thanks" → verify never shown again
   - [ ] Click "Later" → prompt can appear again after 30 days
   - [ ] Click "Rate Now" → opens Play Store listing

3. **Rating Prompt - Manual**
   - [ ] Menu → Rate App → opens Play Store immediately
   - [ ] Help screen → Rate App → opens Play Store immediately

4. **Analytics Verification** (if Supabase configured)
   - [ ] Submit feedback → check Supabase analytics_events table for `feedback_submitted`
   - [ ] Rate app → check for `app_rated` event with source=manual
   - [ ] Accept rating prompt → check for `rating_prompt_accepted` + `app_rated`

### Cooldown Testing
```dart
// To reset for testing (add to debug menu if needed):
await FeedbackService.resetSessionCount();
```

## Implementation Summary

**Files Modified:**
- `lib/services/feedback_service.dart` - Enhanced with rating stars, analytics, updated categories
- `lib/screens/help_screen.dart` - Added "Send Feedback" and "Rate App" options

**Key Features:**
1. **Material 3 Design** - Consistent with app theme, uses proper icons and spacing
2. **Analytics Integration** - All feedback/rating actions tracked for product insights
3. **Email Fallback** - Works even without backend (via mailto: links)
4. **Smart Prompting** - Session tracking + cooldown prevents spam
5. **User Control** - Clear options to dismiss, defer, or act on prompts

**Dependencies Used:**
- shared_preferences - Session tracking and user preferences
- url_launcher - Email and Play Store links
- analytics_service - Backend event tracking (existing service)

## Notes
- Rating prompt shows after **5 app launches**, not immediately
- Cooldown is **30 days** between prompts if user clicks "Later"
- Email subject format: `[Category] TV Viewer Feedback`
- All analytics are anonymous (device_id only, no PII)

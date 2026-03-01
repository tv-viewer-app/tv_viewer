# Feedback/Rating System Implementation

## Overview
This implementation provides a comprehensive feedback and rating system for the Flutter TV Viewer app, addressing GitHub Issue #23. The system includes:

1. ✅ **Star Rating Widget** - Reusable 1-5 star rating component
2. ✅ **Feedback Screen** - Full-screen feedback form with Material 3 design
3. ✅ **GitHub Integration** - Submits feedback as GitHub issues
4. ✅ **Privacy-Respecting** - Optional anonymous device info
5. ✅ **Fallback Support** - Clipboard copy if browser launch fails

## Files Created

### 1. `lib/widgets/star_rating.dart`
A reusable star rating widget that can be used anywhere in the app.

**Features:**
- Interactive 1-5 star rating
- Customizable size and colors
- Read-only mode for displaying ratings
- Haptic feedback support
- Follows Material 3 design

**Usage Example:**
```dart
StarRating(
  rating: 4,
  onRatingChanged: (rating) {
    print('User rated: $rating stars');
  },
  size: 40.0,
)
```

### 2. `lib/screens/feedback_screen.dart`
A full-featured feedback screen with star rating and text input.

**Features:**
- Star rating with visual feedback (Poor/Fair/Good/Very Good/Excellent)
- Multi-line text feedback field
- Optional device info inclusion
- Material 3 card-based design
- Form validation
- Loading states
- Haptic feedback

**Navigation:**
```dart
Navigator.push(
  context,
  MaterialPageRoute(
    builder: (context) => const FeedbackScreen(),
  ),
);
```

### 3. `lib/services/feedback_service.dart`
Enhanced feedback service with GitHub issue integration.

**New Methods:**
- `submitFeedbackWithRating()` - Submits star rating feedback to GitHub
- `_buildIssueTitle()` - Creates issue title with star emojis
- `_buildIssueBody()` - Formats feedback as markdown
- `_getDeviceInfo()` - Collects anonymous device information

**Existing Methods (Preserved):**
- `shouldShowRatingPrompt()` - Auto-prompt logic
- `showRatingPrompt()` - Simple rating dialog
- `showFeedbackDialog()` - Quick feedback dialog
- `openAppStore()` - Opens Play Store for rating

## Integration Guide

### Step 1: Update GitHub Configuration

Edit `lib/services/feedback_service.dart` lines 10-11:

```dart
static const String _githubOwner = 'YOUR_GITHUB_USERNAME';
static const String _githubRepo = 'YOUR_REPO_NAME';
```

Replace with your actual GitHub repository details:
```dart
static const String _githubOwner = 'johnsmith';
static const String _githubRepo = 'tv-viewer';
```

### Step 2: Add to Navigation Menu

The app already has a feedback menu option. Update it to use the new screen:

**File:** `lib/screens/home_screen.dart`

**Current implementation (around line 168):**
```dart
PopupMenuItem(
  value: 'feedback',
  child: const Row(
    children: [
      Icon(Icons.feedback_outlined),
      SizedBox(width: 12),
      Text('Send Feedback'),
    ],
  ),
),
```

**Update the onSelected handler (around line 235):**
```dart
case 'feedback':
  // OLD: FeedbackService.showFeedbackDialog(context);
  // NEW: Navigate to full feedback screen
  Navigator.push(
    context,
    MaterialPageRoute(
      builder: (context) => const FeedbackScreen(),
    ),
  );
  break;
```

### Step 3: Import the Feedback Screen

Add this import at the top of `home_screen.dart`:
```dart
import 'feedback_screen.dart';
```

## How It Works

### User Flow

1. **User opens app** → Navigates to feedback via menu
2. **Rates with stars** → Selects 1-5 stars with visual feedback
3. **Writes feedback** → Optional detailed text input
4. **Chooses privacy** → Toggles device info inclusion
5. **Submits** → App opens browser to GitHub new issue page
6. **Fallback** → If browser fails, content is copied to clipboard

### GitHub Issue Format

The system creates well-formatted GitHub issues:

```markdown
## User Feedback

**Rating:** ⭐⭐⭐⭐⭐ (5/5)

### Feedback

Great app! Love the channel scanning feature. Would be nice to have favorites.

### Device Information

```
Platform: Android
Version: 13 (SDK 33)
Device: Samsung SM-G991B
Brand: samsung
```

---
_This feedback was submitted via the in-app feedback form._
```

### Labels

Issues are automatically tagged with:
- `feedback` - Indicates user feedback
- `user-submitted` - Distinguishes from developer issues

## Privacy Considerations

✅ **Privacy-First Design:**
- Device info is **optional** and user-controlled
- No data sent to external servers
- GitHub account required for submission (user's choice)
- Fallback clipboard copy for offline use
- Clear privacy message displayed to users

**Device Info Collected (when enabled):**
- Platform (Android/iOS/Windows/Linux/macOS)
- OS Version
- Device model/manufacturer (Android)
- Generic device name (iOS/macOS)

**NOT Collected:**
- Personal information
- Location data
- Usage statistics
- Network information
- Installed apps

## Testing

### Test the Star Rating Widget

```dart
// In any screen
StarRating(
  rating: 3,
  onRatingChanged: (rating) {
    print('Rating changed to: $rating');
  },
)
```

### Test Feedback Submission

1. Navigate to Feedback screen
2. Select a star rating (required)
3. Enter feedback text (optional)
4. Toggle device info (optional)
5. Click "Submit Feedback"
6. Verify browser opens to GitHub
7. Check clipboard if browser fails

### Test Without GitHub URL

If you haven't configured GitHub credentials yet:
1. Submit will fail to open browser
2. Content automatically copies to clipboard
3. User sees dialog with GitHub URL
4. Can manually paste into GitHub

## Customization

### Change Star Colors

```dart
StarRating(
  rating: rating,
  filledColor: Colors.amber,
  emptyColor: Colors.grey,
  onRatingChanged: (rating) { },
)
```

### Adjust Rating Descriptions

Edit `_getRatingDescription()` in `feedback_screen.dart`:
```dart
String _getRatingDescription() {
  switch (_rating) {
    case 1: return 'Needs Work';
    case 2: return 'Could Be Better';
    case 3: return 'Satisfactory';
    case 4: return 'Great!';
    case 5: return 'Amazing!';
    default: return 'Rate Us';
  }
}
```

### Change Issue Labels

Edit `_buildGitHubIssueUrl()` in `feedback_service.dart`:
```dart
return 'https://github.com/$_githubOwner/$_githubRepo/issues/new?'
    'title=$encodedTitle&body=$encodedBody&labels=feedback,enhancement,user-request';
```

## Alternative Submission Methods

### Email Instead of GitHub

Replace the GitHub URL builder with email:

```dart
static Future<FeedbackSubmissionResult> submitFeedbackWithRating({
  required int rating,
  required String feedbackText,
  bool includeDeviceInfo = false,
}) async {
  final body = _buildIssueBody(
    rating: rating,
    feedbackText: feedbackText,
    deviceInfo: includeDeviceInfo ? await _getDeviceInfo() : '',
  );
  
  final emailUri = Uri(
    scheme: 'mailto',
    path: 'support@yourapp.com',
    query: 'subject=User Feedback ($rating/5)&body=${Uri.encodeComponent(body)}',
  );
  
  if (await canLaunchUrl(emailUri)) {
    await launchUrl(emailUri);
    return FeedbackSubmissionResult.success('Opening email app...');
  }
  
  // Fallback to clipboard
  await Clipboard.setData(ClipboardData(text: body));
  return FeedbackSubmissionResult.copiedToClipboard(
    'Feedback copied to clipboard',
    'mailto:support@yourapp.com',
  );
}
```

### Google Forms

1. Create a Google Form with fields for rating and feedback
2. Get the pre-filled URL format
3. Update the URL builder:

```dart
static String _buildGoogleFormUrl({
  required int rating,
  required String feedback,
}) {
  // Google Form entry IDs (inspect your form to find these)
  const formId = 'YOUR_FORM_ID';
  const ratingEntryId = 'entry.123456789';
  const feedbackEntryId = 'entry.987654321';
  
  return 'https://docs.google.com/forms/d/e/$formId/viewform?'
      '$ratingEntryId=$rating&'
      '$feedbackEntryId=${Uri.encodeComponent(feedback)}';
}
```

## Dependencies

All required dependencies are already in `pubspec.yaml`:
- ✅ `url_launcher: ^6.2.4` - Opens URLs and email
- ✅ `device_info_plus: ^10.1.0` - Device information
- ✅ `shared_preferences: ^2.2.2` - Rating prompt logic

No additional packages needed!

## Troubleshooting

### Browser doesn't open
**Solution:** Content is automatically copied to clipboard. User can paste into GitHub manually.

### "Can't find GitHub repository"
**Solution:** Update `_githubOwner` and `_githubRepo` constants in `feedback_service.dart`.

### Device info shows "Unable to collect"
**Solution:** This is normal for unsupported platforms. The feedback still works without it.

### Star rating not responding
**Solution:** Make sure `interactive: true` (default) and `onRatingChanged` callback is provided.

## Future Enhancements

Possible improvements for future versions:

1. **Analytics Integration**
   - Track feedback submission rates
   - Monitor average ratings
   - Identify improvement trends

2. **Offline Support**
   - Queue feedback when offline
   - Auto-submit when connected
   - Local storage for drafts

3. **Rich Feedback**
   - Screenshot attachment
   - Log file upload
   - Screen recording capture

4. **AI Categorization**
   - Auto-tag feedback type
   - Sentiment analysis
   - Priority scoring

5. **In-App Response**
   - Show GitHub issue link
   - Track issue status
   - Notify when resolved

## License

This implementation follows the same license as the main TV Viewer project.

## Support

For issues with this feedback system:
1. Check this README first
2. Review code comments
3. Open a GitHub issue (how meta!)
4. Contact the development team

---

**Implementation Date:** 2024
**Issue:** GitHub Issue #23
**Status:** ✅ Complete and Ready to Use

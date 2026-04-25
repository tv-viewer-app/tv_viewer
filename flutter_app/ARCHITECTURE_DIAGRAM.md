# Feedback System Architecture

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           HomeScreen (home_screen.dart)               │  │
│  │  ┌─────────────────────────────────────────────┐     │  │
│  │  │  PopupMenuButton                             │     │  │
│  │  │    ├─ Help                                   │     │  │
│  │  │    ├─ Diagnostics                            │     │  │
│  │  │    ├─ Send Feedback ← NEW                    │     │  │
│  │  │    ├─ Rate App                               │     │  │
│  │  │    └─ About                                  │     │  │
│  │  └─────────────────────────────────────────────┘     │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                    │
│                          │ Navigator.push()                  │
│                          ↓                                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │       FeedbackScreen (feedback_screen.dart)           │  │
│  │  ┌─────────────────────────────────────────────────┐ │  │
│  │  │  Header Card                                     │ │  │
│  │  │    └─ "We value your feedback!"                 │ │  │
│  │  └─────────────────────────────────────────────────┘ │  │
│  │  ┌─────────────────────────────────────────────────┐ │  │
│  │  │  Rating Card                                     │ │  │
│  │  │    ├─ "How would you rate this app?"           │ │  │
│  │  │    ├─ StarRating Widget ⭐⭐⭐⭐⭐              │ │  │
│  │  │    └─ Rating Description (Poor → Excellent)    │ │  │
│  │  └─────────────────────────────────────────────────┘ │  │
│  │  ┌─────────────────────────────────────────────────┐ │  │
│  │  │  Feedback Card                                   │ │  │
│  │  │    └─ Multi-line TextFormField (1000 chars)    │ │  │
│  │  └─────────────────────────────────────────────────┘ │  │
│  │  ┌─────────────────────────────────────────────────┐ │  │
│  │  │  Device Info Card                                │ │  │
│  │  │    └─ CheckboxListTile (optional)              │ │  │
│  │  └─────────────────────────────────────────────────┘ │  │
│  │  ┌─────────────────────────────────────────────────┐ │  │
│  │  │  Submit Button                                   │ │  │
│  │  │    └─ FilledButton.icon()                       │ │  │
│  │  └─────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      Widget Components                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         StarRating (star_rating.dart)                 │  │
│  │  ┌─────────────────────────────────────────────────┐ │  │
│  │  │  Properties:                                     │ │  │
│  │  │    - rating: int (1-5)                          │ │  │
│  │  │    - onRatingChanged: ValueChanged<int>?        │ │  │
│  │  │    - size: double (default: 40.0)               │ │  │
│  │  │    - filledColor: Color?                        │ │  │
│  │  │    - emptyColor: Color?                         │ │  │
│  │  │    - interactive: bool (default: true)          │ │  │
│  │  │    - starCount: int (default: 5)                │ │  │
│  │  └─────────────────────────────────────────────────┘ │  │
│  │  ┌─────────────────────────────────────────────────┐ │  │
│  │  │  Visual:                                         │ │  │
│  │  │    [⭐] [⭐] [⭐] [☆] [☆]                        │ │  │
│  │  │     ↑   ↑   ↑   ↑   ↑                          │ │  │
│  │  │    GestureDetector on each star                 │ │  │
│  │  └─────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       Service Layer                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │    FeedbackService (feedback_service.dart)            │  │
│  │                                                         │  │
│  │  EXISTING FUNCTIONALITY:                               │  │
│  │  ├─ shouldShowRatingPrompt()                          │  │
│  │  ├─ markPromptShown()                                 │  │
│  │  ├─ markAsRated()                                     │  │
│  │  ├─ openAppStore()                                    │  │
│  │  ├─ showRatingPrompt()                                │  │
│  │  ├─ showFeedbackDialog()                              │  │
│  │  └─ resetSessionCount()                               │  │
│  │                                                         │  │
│  │  NEW FUNCTIONALITY:                                    │  │
│  │  ├─ submitFeedbackWithRating()      ← Main method    │  │
│  │  ├─ _buildIssueTitle()              ← Format title   │  │
│  │  ├─ _buildIssueBody()               ← Format body    │  │
│  │  ├─ _buildGitHubIssueUrl()          ← Create URL     │  │
│  │  └─ _getDeviceInfo()                ← Collect info   │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                    │
│                          ├─── Uses ───┐                      │
│                          ↓             ↓                      │
│  ┌─────────────────────┐  ┌─────────────────────────────┐  │
│  │   url_launcher      │  │   device_info_plus          │  │
│  │  - launchUrl()      │  │  - androidInfo              │  │
│  │  - canLaunchUrl()   │  │  - iosInfo                  │  │
│  └─────────────────────┘  │  - windowsInfo              │  │
│                            │  - linuxInfo                │  │
│  ┌─────────────────────┐  │  - macOsInfo                │  │
│  │   Clipboard         │  └─────────────────────────────┘  │
│  │  - setData()        │                                    │
│  └─────────────────────┘                                    │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │    FeedbackSubmissionResult                           │  │
│  │  ├─ status: FeedbackSubmissionStatus                  │  │
│  │  ├─ message: String                                   │  │
│  │  ├─ githubUrl: String?                                │  │
│  │  └─ Factory methods:                                  │  │
│  │      ├─ success()                                     │  │
│  │      ├─ copiedToClipboard()                           │  │
│  │      └─ error()                                       │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      External Systems                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   GitHub Issues                        │  │
│  │                                                         │  │
│  │  URL Format:                                           │  │
│  │  https://github.com/{owner}/{repo}/issues/new?        │  │
│  │    title={encoded_title}&                             │  │
│  │    body={encoded_body}&                               │  │
│  │    labels=feedback,user-submitted                     │  │
│  │                                                         │  │
│  │  Issue Title:                                          │  │
│  │  "User Feedback: ⭐⭐⭐⭐⭐ (5/5)"                      │  │
│  │                                                         │  │
│  │  Issue Body (Markdown):                                │  │
│  │  ┌───────────────────────────────────────────┐        │  │
│  │  │ ## User Feedback                          │        │  │
│  │  │                                             │        │  │
│  │  │ **Rating:** ⭐⭐⭐⭐⭐ (5/5)              │        │  │
│  │  │                                             │        │  │
│  │  │ ### Feedback                                │        │  │
│  │  │ Great app! ...                              │        │  │
│  │  │                                             │        │  │
│  │  │ ### Device Information                      │        │  │
│  │  │ ```                                         │        │  │
│  │  │ Platform: Android                           │        │  │
│  │  │ Version: 13 (SDK 33)                        │        │  │
│  │  │ Device: Samsung SM-G991B                    │        │  │
│  │  │ ```                                         │        │  │
│  │  └───────────────────────────────────────────┘        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
┌─────────┐
│  User   │
└────┬────┘
     │
     │ 1. Taps menu → "Send Feedback"
     ↓
┌─────────────────┐
│   HomeScreen    │
└────┬────────────┘
     │
     │ 2. Navigator.push(FeedbackScreen())
     ↓
┌──────────────────────────────────────────────┐
│           FeedbackScreen                      │
│  ┌────────────────────────────────────────┐  │
│  │ User Actions:                          │  │
│  │  1. Selects star rating (1-5) ⭐      │  │
│  │  2. Writes feedback text              │  │
│  │  3. Toggles device info (optional)    │  │
│  │  4. Taps "Submit Feedback"            │  │
│  └────────────────────────────────────────┘  │
└────┬─────────────────────────────────────────┘
     │
     │ 3. Validates form (rating required)
     ↓
┌──────────────────────────────────────────────┐
│         FeedbackService                       │
│  .submitFeedbackWithRating(                  │
│    rating: 5,                                │
│    feedbackText: "Great app!",               │
│    includeDeviceInfo: true                   │
│  )                                            │
└────┬─────────────────────────────────────────┘
     │
     ├─── 4a. Collect device info (if enabled)
     │         DeviceInfoPlugin.androidInfo
     │
     ├─── 4b. Build issue title
     │         "User Feedback: ⭐⭐⭐⭐⭐ (5/5)"
     │
     ├─── 4c. Build issue body (markdown)
     │         Format rating, feedback, device info
     │
     ├─── 4d. Build GitHub URL
     │         Encode title & body, add labels
     │
     └─── 4e. Try to launch URL
           │
           ├─── Success? ──→ launchUrl()
           │                      │
           │                      ↓
           │                ┌──────────────┐
           │                │   Browser    │
           │                │   Opens to   │
           │                │   GitHub     │
           │                │   Issue Page │
           │                └──────────────┘
           │                      │
           │                      ↓
           │                Return SUCCESS
           │
           └─── Failed? ──→ Clipboard.setData()
                              │
                              ↓
                        Copy to clipboard
                              │
                              ↓
                   Return COPIED_TO_CLIPBOARD
                              │
                              ↓
                      Show dialog with URL
```

## State Flow Diagram

```
FeedbackScreen State:

┌──────────────┐
│   Initial    │
│  rating = 0  │
│  text = ""   │
│  deviceInfo  │
│    = false   │
└──────┬───────┘
       │
       │ User taps star
       ↓
┌──────────────┐
│   Rating     │
│   Selected   │
│  rating = N  │
│  (1-5)       │
└──────┬───────┘
       │
       │ User types text (optional)
       ↓
┌──────────────┐
│   Feedback   │
│   Entered    │
│  text = "..."│
└──────┬───────┘
       │
       │ User toggles device info (optional)
       ↓
┌──────────────┐
│  Device Info │
│   Toggled    │
│  = true/false│
└──────┬───────┘
       │
       │ User taps Submit
       ↓
┌──────────────┐
│  Validation  │
│   rating > 0?│
└──────┬───────┘
       │
       ├─── No ──→ Show error "Please select a rating"
       │           Stay on screen
       │
       └─── Yes ──→ Continue
                    │
                    ↓
              ┌──────────────┐
              │  Submitting  │
              │  isSubmitting│
              │    = true    │
              │  (Loading)   │
              └──────┬───────┘
                     │
                     │ await submitFeedbackWithRating()
                     ↓
              ┌──────────────┐
              │   Result     │
              │  Received    │
              └──────┬───────┘
                     │
                     ├─── Success ──→ Show snackbar
                     │                Pop screen
                     │                Return to Home
                     │
                     ├─── Clipboard ──→ Show dialog
                     │                   with GitHub URL
                     │                   Stay on screen
                     │
                     └─── Error ──→ Show error snackbar
                                    Stay on screen
                                    isSubmitting = false
```

## Integration Points

```
┌─────────────────────────────────────────────────────────┐
│                  Application Entry                       │
│                    (main.dart)                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                    HomeScreen                            │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Integration Point #1: Import                      │ │
│  │  import 'feedback_screen.dart';                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Integration Point #2: Menu Handler                │ │
│  │  case 'feedback':                                  │ │
│  │    Navigator.push(                                 │ │
│  │      context,                                      │ │
│  │      MaterialPageRoute(                            │ │
│  │        builder: (context) =>                       │ │
│  │          const FeedbackScreen(),                   │ │
│  │      ),                                            │ │
│  │    );                                              │ │
│  │    break;                                          │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              FeedbackService Configuration               │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Integration Point #3: GitHub Credentials          │ │
│  │  static const String _githubOwner =                │ │
│  │    'YOUR_GITHUB_USERNAME'; // ← UPDATE THIS       │ │
│  │  static const String _githubRepo =                 │ │
│  │    'YOUR_REPO_NAME';       // ← UPDATE THIS       │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## File Structure

```
tv_viewer_project/flutter_app/
├── lib/
│   ├── screens/
│   │   ├── home_screen.dart          [MODIFIED]
│   │   └── feedback_screen.dart      [NEW] ⭐
│   │
│   ├── widgets/
│   │   └── star_rating.dart          [NEW] ⭐
│   │
│   └── services/
│       └── feedback_service.dart     [ENHANCED] ⭐
│
├── test/
│   └── feedback_system_test.dart     [NEW] ⭐
│
├── FEEDBACK_SYSTEM_README.md         [NEW] ⭐
├── FEEDBACK_QUICK_START.md           [NEW] ⭐
├── INTEGRATION_EXAMPLES.dart         [NEW] ⭐
└── IMPLEMENTATION_SUMMARY.md         [UPDATED] ⭐

⭐ = Part of Issue #23 implementation
```

## Dependency Graph

```
FeedbackScreen
    ├── depends on → StarRating (widget)
    ├── depends on → FeedbackService (service)
    └── uses → Material 3 components

StarRating
    ├── depends on → Flutter widgets
    └── uses → GestureDetector, Icon

FeedbackService
    ├── depends on → url_launcher
    ├── depends on → device_info_plus
    ├── depends on → Clipboard (flutter/services)
    └── returns → FeedbackSubmissionResult

FeedbackSubmissionResult
    └── enum → FeedbackSubmissionStatus
```

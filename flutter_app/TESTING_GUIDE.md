# Installation and Testing Guide

## Prerequisites

Ensure you have Flutter installed and configured:
```bash
flutter --version
```

If Flutter is not installed, download from: https://flutter.dev/docs/get-started/install

## Installation Steps

### 1. Navigate to Project Directory
```bash
cd "D:\Visual Studio 2017\tv_viewer_project\flutter_app"
```

### 2. Install Dependencies
```bash
flutter pub get
```

This will install the following new packages:
- `device_info_plus: ^10.1.0`
- `connectivity_plus: ^6.0.3`
- `package_info_plus: ^8.0.0`
- `share_plus: ^9.0.0`

### 3. Verify No Errors
```bash
flutter analyze
```

This should complete without errors. If there are any issues, they should be minor and easy to fix.

### 4. Run the App
```bash
flutter run
```

Or for a specific device:
```bash
flutter run -d <device-id>
```

## Configuration Changes Needed

### 1. Update Package Name (for App Store Rating)

**File:** `lib/services/feedback_service.dart`  
**Line:** 44

Replace:
```dart
const packageName = 'com.example.tv_viewer';
```

With your actual package name from `android/app/build.gradle`:
```dart
const packageName = 'com.your_company.tv_viewer';
```

### 2. Update Support Email (for Feedback)

**File:** `lib/services/feedback_service.dart`  
**Line:** 177

Replace:
```dart
path: 'https://github.com/tv-viewer-app/tv_viewer/issues',
```

With your actual support email:
```dart
path: 'https://github.com/tv-viewer-app/tv_viewer/issues',
```

## Testing Checklist

### ✅ BL-017: Language Filter

**Test Steps:**
1. Launch the app
2. Wait for channels to load
3. Scroll down to the filter section
4. Verify you see a **Language** dropdown on its own row
5. Tap the Language dropdown
6. Select a specific language (e.g., "English")
7. Verify channels are filtered by that language
8. Select "All" to clear the filter

**Expected Results:**
- Language dropdown appears with available languages from M3U data
- Filtering works correctly
- "All" option shows all channels regardless of language

---

### ✅ BL-024: Diagnostics Screen

**Test Steps:**
1. Launch the app
2. Tap the menu button (⋮) in the top-right
3. Select **"Diagnostics"**
4. Verify the diagnostics screen opens

**Device Information Section:**
- Check that device model is displayed correctly
- Verify OS version shows (e.g., "Android 13 (SDK 33)")
- Confirm screen size is displayed
- Check app version matches `pubspec.yaml` (1.5.0)

**Network Status Section:**
1. Note the current connection type (WiFi/Mobile)
2. Toggle WiFi on/off
3. Verify connection status updates automatically
4. Tap "Refresh Network Status" button
5. Verify it updates correctly

**Stream URL Tester:**
1. Enter a valid stream URL (copy from any channel)
2. Tap "Test Stream" button
3. Wait for results (should show ✓ with response time)
4. Enter an invalid URL (e.g., "http://invalid.test.com/stream")
5. Tap "Test Stream" button
6. Verify error message appears with troubleshooting info

**Export Report:**
1. Tap "Export Full Diagnostic Report" button
2. Verify share dialog opens
3. Share to Notes/Email
4. Verify report contains all information

**Expected Results:**
- All device info displays correctly
- Network changes are detected in real-time
- Stream tester works for both valid and invalid URLs
- Export generates complete report

---

### ✅ BL-031: Immutable Channel Model

**Test Steps:**
1. Launch the app
2. Tap the scan/refresh button (🔄) in the top-right
3. Let the scan complete for at least 10-20 channels
4. Verify no errors appear during scanning
5. Check that working/failed counts update correctly

**Code Verification:**
1. Open `lib/models/channel.dart`
2. Verify all fields are marked `final`
3. Verify `copyWith()` method exists
4. Open `lib/providers/channel_provider.dart`
5. Verify `validateChannels()` uses `channel.copyWith()` instead of direct mutation

**Expected Results:**
- No errors during channel validation
- Channels update correctly during scan
- Progress bar shows working/failed counts
- No state mutation errors in console

---

### ✅ BL-032: Feedback System

**Test 1: Rating Prompt (First Time User)**
1. **Reset test data** (run once in main.dart for testing):
   ```dart
   await FeedbackService.resetSessionCount(); // Add temporarily
   ```
2. Close and reopen the app 5 times
3. On the 5th launch, wait 2 seconds
4. Verify rating prompt appears with:
   - ⭐ Star icon
   - "Enjoying TV Viewer?" title
   - Three buttons: "No Thanks", "Later", "Rate Now"

**Test 2: Rating Prompt Actions**
1. Trigger rating prompt (5 sessions)
2. Tap "Rate Now"
   - Verify Play Store opens (or browser if Play Store unavailable)
   - Close and reopen app
   - Verify prompt never appears again
3. Reset and trigger again
4. Tap "Later"
   - Close and reopen app immediately
   - Verify prompt does NOT appear
   - Wait 30 days (or modify code for testing)
   - Verify prompt appears again
5. Reset and trigger again
6. Tap "No Thanks"
   - Close and reopen app
   - Verify prompt never appears again

**Test 3: Send Feedback Form**
1. Open app
2. Tap menu (⋮) → "Send Feedback"
3. Verify feedback dialog opens with:
   - Feedback Type dropdown
   - Text input field
4. Select "Bug Report" from dropdown
5. Enter some test feedback text
6. Tap "Send" button
7. Verify email app opens with:
   - Pre-filled subject: "Bug Report - TV Viewer Feedback"
   - Pre-filled body: Your feedback text
8. Verify success toast appears

**Test 4: Rate App Menu**
1. Open app
2. Tap menu (⋮) → "Rate App"
3. Verify Play Store opens immediately
4. Verify no prompt appears after

**Expected Results:**
- Rating prompt appears after 5 sessions (configurable)
- "Rate Now" opens Play Store and marks as rated
- "Later" delays for 30 days
- "No Thanks" permanently dismisses
- Feedback form submits via email
- All interactions are smooth and non-intrusive

---

## Common Issues and Solutions

### Issue: "device_info_plus not found"
**Solution:** Run `flutter pub get` again

### Issue: "Unhandled Exception: MissingPluginException"
**Solution:** 
1. Stop the app
2. Run: `flutter clean`
3. Run: `flutter pub get`
4. Run: `flutter run` again

### Issue: Language filter shows "Unknown" for many channels
**Explanation:** This is expected - many M3U streams don't include language metadata. The filter still works for channels that do have language information.

### Issue: Stream tester shows errors for working channels
**Explanation:** Some streams require specific headers or don't support HEAD requests. The tester uses a conservative approach - if HEAD fails, the stream might still work in the player.

### Issue: Email doesn't open for feedback
**Solution:** Ensure your device has an email app installed (Gmail, Outlook, etc.)

### Issue: Rating prompt doesn't appear
**Solution:** Add temporary code to reset session count:
```dart
// In HomeScreen.initState(), before _checkRatingPrompt()
await FeedbackService.resetSessionCount();
```

---

## Performance Testing

### Memory Usage
1. Open Android Studio Profiler
2. Run app
3. Navigate through all screens
4. Check for memory leaks
5. Verify diagnostics screen doesn't leak

### Network Performance
1. Enable network throttling (slow 3G)
2. Test stream URL tester
3. Verify appropriate timeout messages

### Battery Impact
1. Run app for 30 minutes with diagnostics screen open
2. Check battery usage in Android settings
3. Should be minimal (no continuous scanning)

---

## Automated Testing (Optional)

Create widget tests for new features:

### Test: Language Filter
```dart
testWidgets('Language filter works correctly', (tester) async {
  // Test implementation
});
```

### Test: Diagnostics Screen
```dart
testWidgets('Diagnostics screen loads device info', (tester) async {
  // Test implementation
});
```

### Test: Rating Prompt
```dart
testWidgets('Rating prompt appears after 5 sessions', (tester) async {
  // Test implementation
});
```

---

## Deployment Checklist

Before releasing to production:

- [ ] Test on Android 8.0+ devices
- [ ] Test on different screen sizes (phone, tablet)
- [ ] Verify all new dependencies are added to `pubspec.yaml`
- [ ] Update package name in `feedback_service.dart`
- [ ] Update support email in `feedback_service.dart`
- [ ] Test network connectivity changes
- [ ] Test feedback submission
- [ ] Verify rating prompt logic
- [ ] Check Play Store link works
- [ ] Update app version to 1.5.0 in `pubspec.yaml` ✅
- [ ] Run `flutter analyze` with no errors
- [ ] Run all tests
- [ ] Build release APK: `flutter build apk --release`
- [ ] Test release build on real device

---

## Support

If you encounter any issues:

1. Check `flutter doctor` output
2. Verify all dependencies installed correctly
3. Check Android Studio logcat for errors
4. Review implementation summary for details
5. Check that all imports are correct

---

## Quick Start Commands

```bash
# Install dependencies
flutter pub get

# Check for errors
flutter analyze

# Run app
flutter run

# Run tests (if any exist)
flutter test

# Build release
flutter build apk --release

# Build app bundle for Play Store
flutter build appbundle --release
```

---

## Success Indicators

The implementation is successful when:

✅ App compiles without errors  
✅ All four features are visible and functional  
✅ Language filter shows available languages  
✅ Diagnostics screen displays device info  
✅ Stream tester can test URLs  
✅ Feedback form opens and submits  
✅ Rating prompt appears after 5 sessions  
✅ No crashes or memory leaks  
✅ Performance is smooth  

---

## Version Info

**Previous Version:** 1.4.4  
**New Version:** 1.5.0  
**Build Date:** 2024  
**Features Added:** 4 (BL-017, BL-024, BL-031, BL-032)  
**Dependencies Added:** 4  
**Files Created:** 3  
**Files Modified:** 4  

---

Congratulations! You've successfully implemented all advanced features. 🎉

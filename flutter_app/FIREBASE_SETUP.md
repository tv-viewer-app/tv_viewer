# Firebase Setup Guide

This guide walks you through setting up Firebase Analytics and Crashlytics for the TV Viewer app.

## Overview

The app is designed to work **with or without** Firebase:
- ✅ **Without Firebase**: Services fall back to `logger_service.dart` - app works normally
- ✅ **With Firebase**: Full analytics and crash reporting capabilities enabled

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Firebase Console Setup](#firebase-console-setup)
4. [Android Configuration](#android-configuration)
5. [Flutter Dependencies](#flutter-dependencies)
6. [Code Integration](#code-integration)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

**Current Status**: Firebase is **NOT configured** (stub implementation active)

**To enable Firebase**:
1. Create Firebase project
2. Download `google-services.json`
3. Add to `android/app/`
4. Uncomment Firebase code in services
5. Add dependencies to `pubspec.yaml`

**Estimated time**: 30 minutes

---

## Prerequisites

Before setting up Firebase:

- [x] Flutter SDK installed (>=3.0.0)
- [ ] Google account (for Firebase Console)
- [ ] Android Studio or VS Code with Flutter extension
- [ ] Basic understanding of Firebase

---

## Firebase Console Setup

### Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Add project"** or **"Create a project"**
3. Enter project name: `tv-viewer` (or your preferred name)
4. **Analytics**: Enable Google Analytics (recommended)
5. Choose or create Analytics account
6. Click **"Create project"**
7. Wait for project creation (takes ~30 seconds)

### Step 2: Add Android App

1. In Firebase Console, click **"Add app"** → **Android**
2. **Android package name**: `com.example.tv_viewer`
   - ⚠️ **MUST match** `applicationId` in `android/app/build.gradle`
   - To verify, check: `android/app/build.gradle` → `defaultConfig.applicationId`
3. **App nickname**: `TV Viewer` (optional)
4. **Debug signing certificate**: Leave blank for now (optional for development)
5. Click **"Register app"**

### Step 3: Download Configuration File

1. Download **`google-services.json`**
2. **Important**: Keep this file secure (contains API keys)
3. Click **"Next"** (we'll add it in the next section)

### Step 4: Enable Services

1. In Firebase Console sidebar, go to:
   - **Build** → **Crashlytics** → **Enable Crashlytics**
   - **Analytics** → **Dashboard** (auto-enabled with setup)
2. Follow any additional prompts to complete setup

---

## Android Configuration

### Step 1: Add google-services.json

```bash
# Copy google-services.json to Android app directory
cp ~/Downloads/google-services.json android/app/
```

**File location**: `android/app/google-services.json`

**Verify**:
```bash
ls -la android/app/google-services.json
# Should show the file with ~1-5KB size
```

### Step 2: Update android/build.gradle (Project-level)

**File**: `android/build.gradle`

```gradle
buildscript {
    ext.kotlin_version = '1.9.0'
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:8.1.0'
        classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:$kotlin_version"
        
        // ADD THESE LINES ↓
        classpath 'com.google.gms:google-services:4.4.0'
        classpath 'com.google.firebase:firebase-crashlytics-gradle:2.9.9'
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}
```

### Step 3: Update android/app/build.gradle (App-level)

**File**: `android/app/build.gradle`

```gradle
// At the TOP of the file (after 'plugins' block or 'apply plugin' lines)
apply plugin: 'com.android.application'
apply plugin: 'kotlin-android'
apply plugin: 'com.google.gms.google-services'      // ADD THIS
apply plugin: 'com.google.firebase.crashlytics'    // ADD THIS

android {
    // ... existing configuration ...
}

dependencies {
    // ... existing dependencies ...
    
    // ADD THESE LINES ↓
    // Firebase BoM (Bill of Materials) - manages versions
    implementation platform('com.google.firebase:firebase-bom:32.7.4')
    
    // Firebase services (version managed by BoM)
    implementation 'com.google.firebase:firebase-analytics'
    implementation 'com.google.firebase:firebase-crashlytics'
}
```

---

## Flutter Dependencies

### Update pubspec.yaml

**File**: `pubspec.yaml`

```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # ... existing dependencies ...
  
  # Firebase (ADD THESE) ↓
  firebase_core: ^2.24.2
  firebase_analytics: ^10.8.0
  firebase_crashlytics: ^3.4.8
```

### Install Dependencies

```bash
flutter pub get
```

---

## Code Integration

### Step 1: Update main.dart

**File**: `lib/main.dart`

Add imports at the top:
```dart
import 'package:firebase_core/firebase_core.dart';
import 'services/analytics_service.dart';
import 'services/crashlytics_service.dart';
```

Update `main()` function:
```dart
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Firebase (ADD THIS BLOCK) ↓
  try {
    await Firebase.initializeApp();
    print('[Firebase] Initialized successfully');
  } catch (e) {
    print('[Firebase] Failed to initialize: $e');
    // App will continue in fallback mode
  }
  
  // Initialize services
  await LoggerService.instance.initialize();
  await AnalyticsService.instance.initialize();
  await CrashlyticsService.instance.initialize();
  
  // ... rest of your main() function ...
  runApp(MyApp());
}
```

### Step 2: Update analytics_service.dart

**File**: `lib/services/analytics_service.dart`

Find the `_initializeFirebase()` method and **uncomment** the Firebase code:

```dart
Future<bool> _initializeFirebase() async {
  try {
    // UNCOMMENT THESE LINES ↓
    await Firebase.initializeApp();
    _analytics = FirebaseAnalytics.instance;
    return true;
    
    // COMMENT OUT THIS LINE ↓
    // return false;
    
  } catch (e) {
    debugPrint('[Analytics] Firebase not available: $e');
    return false;
  }
}
```

Find the `logEvent()` method and **uncomment** the Firebase code:

```dart
if (_firebaseAvailable && _analytics != null) {
  // UNCOMMENT THIS LINE ↓
  await _analytics.logEvent(name: name, parameters: parameters);
  
  _logger.debug('[Analytics] Event: $name ${parameters != null ? parameters.toString() : ''}');
} else {
  // ... fallback code ...
}
```

Repeat for other methods (`setUserProperty`, `setUserId`, etc.)

### Step 3: Update crashlytics_service.dart

**File**: `lib/services/crashlytics_service.dart`

Find the `_initializeFirebase()` method and **uncomment** the Firebase code:

```dart
Future<bool> _initializeFirebase() async {
  try {
    // UNCOMMENT THESE LINES ↓
    await Firebase.initializeApp();
    _crashlytics = FirebaseCrashlytics.instance;
    
    // Enable crash collection
    await _crashlytics.setCrashlyticsCollectionEnabled(true);
    
    return true;
    
    // COMMENT OUT THIS LINE ↓
    // return false;
    
  } catch (e) {
    debugPrint('[Crashlytics] Firebase not available: $e');
    return false;
  }
}
```

Find the `recordError()` method and **uncomment** the Firebase code:

```dart
if (_firebaseAvailable && _crashlytics != null) {
  // UNCOMMENT THESE LINES ↓
  await _crashlytics.recordError(
    exception,
    stack,
    reason: reason,
    fatal: fatal,
    information: information,
  );
  
  _logger.error(
    '[Crashlytics] ${fatal ? 'FATAL' : 'Error'}: ${reason ?? exception.toString()}',
    exception,
    stack,
  );
} else {
  // ... fallback code ...
}
```

Repeat for other methods (`recordFlutterError`, `setCustomKey`, `log`, etc.)

### Step 4: Add Firebase Imports

Add to both service files at the top:

```dart
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_analytics/firebase_analytics.dart';  // analytics_service.dart
import 'package:firebase_crashlytics/firebase_crashlytics.dart';  // crashlytics_service.dart
```

---

## Testing

### Test 1: Verify Firebase Initialization

```bash
flutter run --verbose
```

Look for logs:
```
[Firebase] Initialized successfully
[Analytics] Firebase Analytics initialized successfully
[Crashlytics] Firebase Crashlytics initialized successfully
```

### Test 2: Test Analytics Event

Add to your app (e.g., in a button press):
```dart
import 'package:tv_viewer/services/analytics_service.dart';

// Track event
await analytics.logAppStart();
await analytics.logChannelPlay(
  channelName: 'Test Channel',
  category: 'News',
  country: 'USA',
);
```

### Test 3: Test Crashlytics

**DO NOT DO THIS IN PRODUCTION!**

```dart
import 'package:tv_viewer/services/crashlytics_service.dart';

// Test crash (development only!)
if (kDebugMode) {
  await crashlytics.recordError(
    Exception('Test error'),
    StackTrace.current,
    reason: 'Testing Crashlytics',
  );
}
```

### Test 4: Verify in Firebase Console

1. **Analytics**: Go to Firebase Console → **Analytics** → **Events**
   - Should see `app_start`, `channel_play`, etc. (may take 1-2 hours to appear)
2. **Crashlytics**: Go to Firebase Console → **Crashlytics** → **Dashboard**
   - Should see test crashes (appears within minutes)

---

## Troubleshooting

### Issue 1: "google-services.json not found"

**Error**:
```
> File google-services.json is missing.
```

**Solution**:
1. Verify file location: `android/app/google-services.json`
2. Check file is not in `.gitignore`
3. Clean and rebuild:
   ```bash
   flutter clean
   flutter pub get
   flutter run
   ```

### Issue 2: "Firebase not initialized"

**Error**:
```
[ERROR:flutter/runtime/dart_vm_initializer.cc(41)] Unhandled Exception: 
[core/no-app] No Firebase App '[DEFAULT]' has been created
```

**Solution**:
1. Ensure `Firebase.initializeApp()` is called in `main()` BEFORE using Firebase
2. Wrap in try-catch to handle failures gracefully

### Issue 3: "Package name mismatch"

**Error**:
```
FirebaseError: Package name 'com.example.tv_viewer' does not match
```

**Solution**:
1. Check `android/app/build.gradle` → `applicationId`
2. Must match package name in Firebase Console
3. Re-download `google-services.json` with correct package name

### Issue 4: "Analytics events not appearing"

**Symptoms**: Events logged but not showing in Firebase Console

**Solution**:
1. **Wait**: Analytics can take 1-24 hours to appear
2. **Debug View**: Enable debug mode for instant feedback
   ```bash
   adb shell setprop debug.firebase.analytics.app com.example.tv_viewer
   ```
3. **Verify**: Check Firebase Console → **Analytics** → **DebugView**

### Issue 5: "Gradle sync failed"

**Error**:
```
Could not resolve com.google.firebase:firebase-bom:32.7.4
```

**Solution**:
1. Update Gradle wrapper:
   ```bash
   cd android
   ./gradlew wrapper --gradle-version 8.1
   ```
2. Update repositories in `android/build.gradle`:
   ```gradle
   allprojects {
       repositories {
           google()
           mavenCentral()
       }
   }
   ```

---

## Monitoring & Usage

### Key Events Tracked

| Event | Description | Parameters |
|-------|-------------|------------|
| `app_start` | App launched | None |
| `channel_play` | Channel played | `channel_name`, `category`, `country`, `media_type` |
| `scan_start` | Playlist scan started | `playlist_url`, `playlist_name` |
| `scan_complete` | Playlist scan finished | `playlist_url`, `channel_count`, `success`, `duration` |
| `filter_applied` | Filter used | `filter_type`, `filter_value` |
| `error_occurred` | Error happened | `error_message`, `error_code`, `context` |
| `playlist_added` | Playlist added | `playlist_url`, `playlist_name` |
| `favorites_toggled` | Favorite toggled | `channel_name`, `is_favorite` |
| `help_viewed` | Help accessed | `help_topic` |
| `feedback_submitted` | Feedback sent | `feedback_type`, `category` |

### Best Practices

1. **Don't over-track**: Only log meaningful events
2. **Privacy**: Don't log personally identifiable information (PII)
3. **Custom keys**: Add context to crashes with `setCustomKey()`
4. **User consent**: Check local regulations (GDPR, CCPA) before enabling
5. **Budget**: Firebase free tier is generous but has limits:
   - Analytics: Unlimited events
   - Crashlytics: Unlimited crash reports
   - Storage: 1 GB free

### Usage Example

```dart
// In your channel player
await analytics.logChannelPlay(
  channelName: channel.name,
  category: channel.category,
  country: channel.country,
);

// When error occurs
await crashlytics.recordError(
  exception,
  stackTrace,
  reason: 'Failed to load stream',
);

// Add context to crashes
await crashlytics.setCustomKey('playlist_url', currentPlaylist);
await crashlytics.setCustomKey('channel_count', channels.length.toString());
```

---

## Security Considerations

### google-services.json

**Contains**:
- API keys (restricted to your app package)
- Project IDs
- Client IDs

**Security**:
- ✅ Safe to commit to **private** repos
- ❌ **DO NOT** commit to **public** repos
- 🔒 API keys are restricted by package name (Android) or bundle ID (iOS)
- 🔒 Keys cannot be used by other apps

**To secure for public repos**:

1. Add to `.gitignore`:
   ```gitignore
   # Firebase
   android/app/google-services.json
   ios/Runner/GoogleService-Info.plist
   ```

2. Document setup in README:
   ```markdown
   ## Firebase Setup
   1. Download google-services.json from Firebase Console
   2. Place in android/app/
   3. Follow FIREBASE_SETUP.md for full instructions
   ```

### API Key Restrictions

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your Firebase project
3. Go to **APIs & Services** → **Credentials**
4. Edit API keys:
   - Restrict to **Android apps**
   - Add package name: `com.example.tv_viewer`
   - Add SHA-1 fingerprint (optional, for release)

---

## Migration Path

### Current State (Stub Implementation)

```dart
✅ analytics_service.dart - works without Firebase
✅ crashlytics_service.dart - works without Firebase
✅ Logs to logger_service.dart
✅ App functions normally
❌ No remote analytics
❌ No remote crash reporting
```

### With Firebase Enabled

```dart
✅ analytics_service.dart - uses Firebase Analytics
✅ crashlytics_service.dart - uses Firebase Crashlytics
✅ Still logs to logger_service.dart
✅ Remote analytics in Firebase Console
✅ Remote crash reports in Firebase Console
```

### Rollback Plan

If Firebase causes issues:

1. **Disable in code**:
   ```dart
   // In _initializeFirebase() methods
   return false;  // Force fallback mode
   ```

2. **Remove dependencies**:
   ```bash
   # Comment out in pubspec.yaml
   # firebase_core: ^2.24.2
   # firebase_analytics: ^10.8.0
   # firebase_crashlytics: ^3.4.8
   
   flutter pub get
   ```

3. **App continues working** with logger fallback

---

## FAQ

**Q: Do I need Firebase for the app to work?**  
A: No. The app works perfectly without Firebase, using `logger_service.dart` as a fallback.

**Q: Is Firebase free?**  
A: Yes, the free tier (Spark Plan) is sufficient for most apps. Analytics and Crashlytics are unlimited.

**Q: Will Firebase slow down my app?**  
A: No. Firebase SDK is optimized and sends data asynchronously.

**Q: Can I use this with iOS?**  
A: Yes, but you'll need to configure `ios/Runner/GoogleService-Info.plist` and update iOS build files.

**Q: What data does Firebase collect?**  
A: Only what you explicitly track (events, crashes). No automatic data collection beyond basic app info.

**Q: How do I disable Firebase in production?**  
A: Call `setCrashlyticsCollectionEnabled(false)` and don't log analytics events.

**Q: Can I test Firebase in debug mode?**  
A: Yes, use `adb shell setprop debug.firebase.analytics.app <package>` for debug view.

---

## Next Steps

1. ✅ Complete Firebase Console setup
2. ✅ Add `google-services.json` to project
3. ✅ Update Gradle files
4. ✅ Update `pubspec.yaml`
5. ✅ Uncomment Firebase code in services
6. ✅ Test analytics events
7. ✅ Test crash reporting
8. ✅ Monitor Firebase Console

---

## Support & Resources

- 📚 [Firebase Documentation](https://firebase.google.com/docs)
- 📱 [FlutterFire Documentation](https://firebase.flutter.dev/)
- 🐛 [Firebase Support](https://firebase.google.com/support)
- 💬 [FlutterFire GitHub](https://github.com/firebase/flutterfire)
- 📊 [Analytics Events Reference](https://firebase.google.com/docs/analytics/events)
- 🔥 [Crashlytics Best Practices](https://firebase.google.com/docs/crashlytics/best-practices)

---

**Last Updated**: 2024  
**Author**: TV Viewer Development Team  
**Version**: 1.0

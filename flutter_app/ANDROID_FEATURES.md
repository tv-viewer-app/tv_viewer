# Android Features Implementation Guide

This document describes the Android-specific features implemented for the TV Viewer app.

## 📋 Summary of Changes

### 1. Wake Lock Support (BL-013) ✅
Prevents the screen from sleeping during video playback.

**Implementation:**
- **Dependency:** `wakelock_plus: ^1.2.0`
- **Permission:** `WAKE_LOCK` (already in AndroidManifest.xml)
- **Location:** `lib/screens/player_screen.dart`

**How it works:**
- Wake lock is enabled when the player screen is opened
- Automatically disabled when the screen is closed
- Prevents screen timeout during video playback

### 2. Picture-in-Picture (PiP) Support (BL-023) ✅
Allows users to watch videos in a small floating window while using other apps.

**Implementation:**
- **Dependency:** `floating: ^2.0.0`
- **Min SDK:** API 26 (Android 8.0)
- **Permissions:** Configured in AndroidManifest.xml
  - `android:supportsPictureInPicture="true"`
  - `android:resizeableActivity="true"`
- **Service:** `lib/services/pip_service.dart`
- **UI Integration:** PiP button in player controls

**How it works:**
- PiP button appears in player controls (top-right)
- Automatically calculates aspect ratio from video
- Maintains video playback in background
- Handles app lifecycle transitions
- Only available on Android 8.0+

### 3. Build Configuration Updates ✅
- **minSdkVersion:** Updated from 21 to 26 (required for PiP)
- **ProGuard Rules:** Added rules for wakelock_plus and floating packages
- **Release Signing:** Configured with key.properties support

### 4. ProGuard Rules Enhancement ✅
Added rules for:
- Wakelock Plus package
- Floating (PiP) package
- Proper obfuscation without breaking functionality

---

## 🚀 Features in Detail

### Wake Lock Feature

**User Experience:**
- Screen stays on during video playback
- No manual intervention needed
- Automatically releases when player is closed

**Code Example:**
```dart
// In player_screen.dart
Future<void> _initializeWakeLock() async {
  try {
    await WakelockPlus.enable();
    debugPrint('Wake lock enabled');
  } catch (e) {
    debugPrint('Failed to enable wake lock: $e');
  }
}

@override
void dispose() {
  WakelockPlus.disable();
  // ... other cleanup
}
```

### Picture-in-Picture Feature

**User Experience:**
1. Open any video in the player
2. Tap the PiP button (picture-in-picture icon) in the top-right
3. Video continues playing in a small floating window
4. Navigate to other apps while watching
5. Tap the PiP window to return to full-screen

**Aspect Ratio Detection:**
The PiP service automatically detects common aspect ratios:
- 16:9 (most common)
- 4:3 (classic)
- 21:9 (ultrawide)
- Custom ratios based on video dimensions

**Code Example:**
```dart
// Enable PiP with automatic aspect ratio
await _pipService.enablePip(aspectRatio: aspectRatio);

// Or specify custom ratio
await _pipService.enablePip(aspectRatio: Rational(16, 9));
```

**PiP Service Features:**
- ✅ Automatic aspect ratio calculation
- ✅ PiP status monitoring
- ✅ Lifecycle management
- ✅ Error handling
- ✅ Device compatibility check

---

## 📱 Android Requirements

### Minimum Requirements
- **Android Version:** 8.0 (API 26) or higher
- **Reason:** PiP support requires API 26+

### Permissions (AndroidManifest.xml)
```xml
<uses-permission android:name="android.permission.WAKE_LOCK"/>
```

### Activity Configuration (AndroidManifest.xml)
```xml
<activity
    android:supportsPictureInPicture="true"
    android:resizeableActivity="true"
    android:configChanges="orientation|keyboardHidden|keyboard|screenSize|..."
    ...>
```

---

## 🔧 Build Configuration

### build.gradle Changes
```gradle
android {
    defaultConfig {
        minSdk 26  // Updated from 21 for PiP support
        targetSdk 34
    }
    
    buildTypes {
        release {
            minifyEnabled true
            shrinkResources true
            proguardFiles 'proguard-rules.pro'
        }
    }
}
```

### ProGuard Rules (proguard-rules.pro)
```proguard
# Wakelock Plus
-keep class com.ryanheise.wakelock_plus.** { *; }

# Floating (PiP)
-keep class floating.** { *; }
-keep class io.flutter.plugins.floating.** { *; }
```

---

## 🧪 Testing Instructions

### Wake Lock Testing
1. Open a video in the player
2. Observe that the screen stays on during playback
3. Wait beyond normal screen timeout period
4. Screen should remain on
5. Exit player and verify screen timeout returns to normal

### PiP Testing
1. **Device Check:**
   - Ensure device is running Android 8.0+
   - Check that PiP button appears in player controls

2. **Enter PiP:**
   - Open a video
   - Tap the PiP button (picture-in-picture icon)
   - Video should minimize to floating window
   - Video continues playing

3. **PiP Interaction:**
   - Press home button → PiP window remains
   - Open another app → PiP window floats on top
   - Tap PiP window → returns to full-screen

4. **Exit PiP:**
   - Close PiP window
   - Or tap to return to full-screen

5. **Error Cases:**
   - Test on Android < 8.0 → should show "not supported" message
   - Test with incompatible device → graceful fallback

---

## 📂 File Structure

```
android/
├── app/
│   ├── build.gradle                    # Updated minSdk to 26
│   ├── proguard-rules.pro             # Added wakelock & PiP rules
│   └── src/main/
│       └── AndroidManifest.xml        # PiP permissions configured

lib/
├── screens/
│   └── player_screen.dart             # Wake lock & PiP integration
└── services/
    └── pip_service.dart               # PiP service implementation (NEW)

pubspec.yaml                           # Added dependencies
```

---

## 🐛 Troubleshooting

### Wake Lock Issues

**Problem:** Screen still turns off during playback
**Solution:**
- Check that WAKE_LOCK permission is in AndroidManifest.xml
- Verify wakelock_plus package is installed
- Check device battery optimization settings

### PiP Issues

**Problem:** PiP button doesn't appear
**Solution:**
- Verify device is running Android 8.0+ (API 26)
- Check AndroidManifest.xml has `supportsPictureInPicture="true"`
- Rebuild the app after manifest changes

**Problem:** PiP doesn't work on some devices
**Solution:**
- Some manufacturers disable PiP (e.g., older Samsung devices)
- Check device settings → Apps → Special access → Picture-in-picture
- Enable PiP for TV Viewer app

**Problem:** Video stops in PiP mode
**Solution:**
- Check app lifecycle handling in didChangeAppLifecycleState
- Ensure video player continues in background
- Verify Android battery optimization isn't killing the app

### Build Issues

**Problem:** ProGuard errors in release build
**Solution:**
- Check proguard-rules.pro includes rules for all dependencies
- Test with `./gradlew assembleRelease`
- Review build output for missing rules

**Problem:** App crashes on older Android versions
**Solution:**
- Minimum SDK is now 26 (Android 8.0)
- Users with older devices won't be able to install
- Consider building separate APK for legacy devices if needed

---

## 🔐 Security Considerations

### Wake Lock
- No security implications
- System automatically releases when app is closed
- No user data involved

### PiP Mode
- No sensitive data displayed in PiP window
- Video content is already public (IPTV streams)
- No additional permissions required beyond manifest configuration

### ProGuard
- All sensitive classes are properly protected
- Native methods are preserved
- Kotlin metadata is maintained for reflection

---

## 📊 Performance Impact

### Wake Lock
- **Battery Impact:** Minimal (keeps screen on, not CPU intensive)
- **Memory Impact:** Negligible
- **Startup Impact:** None

### PiP Mode
- **Battery Impact:** Low (video decoding continues)
- **Memory Impact:** Same as normal playback
- **Startup Impact:** None (lazy initialization)

---

## 🚀 Future Enhancements

### Potential Improvements
1. **Custom PiP Controls:**
   - Add play/pause button in PiP window
   - Add channel switching in PiP
   - Requires native Android implementation

2. **PiP Position Memory:**
   - Remember last PiP window position
   - Save user's preferred size

3. **Smart Wake Lock:**
   - Disable wake lock when paused
   - Enable only during active playback

4. **PiP Quality Adjustment:**
   - Lower quality stream in PiP mode to save bandwidth
   - Automatic quality switching

---

## 📖 Developer Notes

### Code Quality
- ✅ All features properly documented
- ✅ Error handling implemented
- ✅ Lifecycle management correct
- ✅ Memory leaks prevented
- ✅ ProGuard rules complete

### Testing Coverage
- ✅ Wake lock enable/disable
- ✅ PiP enter/exit
- ✅ Aspect ratio calculation
- ✅ Device compatibility checks
- ✅ Error scenarios

### Maintainability
- Clean separation of concerns
- PiP logic in dedicated service
- Easy to extend or modify
- Well-commented code

---

## 📝 Change Log

### Version 1.5.0
- ✅ Added wake lock support (BL-013)
- ✅ Added PiP support (BL-023)
- ✅ Updated minSdk to 26
- ✅ Enhanced ProGuard rules
- ✅ Created PiP service
- ✅ Updated player screen with new features

---

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review error logs in Android Logcat
3. Test on physical device (emulator PiP support varies)
4. Verify all dependencies are up to date

---

**Implementation Date:** 2024
**Android Version Support:** 8.0+ (API 26+)
**Status:** ✅ Complete and Tested

# Quick Start: Android Optimizations Implementation Guide

This guide provides step-by-step instructions to implement the critical Android optimizations identified in the review.

## 🔴 Phase 1: Critical Fixes (DO THESE FIRST)

### 1. Setup Release Signing (30 minutes)

**Step 1**: Generate a release keystore
```bash
# Run this command in your terminal
keytool -genkey -v -keystore C:\keys\tv-viewer-upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload

# Follow prompts:
# - Enter keystore password (save this!)
# - Re-enter password
# - Enter your name/organization details
# - Enter key password (can be same as keystore password)
```

**Step 2**: Copy the example key.properties file
```bash
cd android
copy key.properties.example key.properties
```

**Step 3**: Edit `android/key.properties` with your actual values:
```properties
storePassword=YourKeystorePassword
keyPassword=YourKeyPassword
keyAlias=upload
storeFile=C:/keys/tv-viewer-upload-keystore.jks
```

**Step 4**: Verify it works
```bash
flutter build apk --release
```

✅ **Success**: You should see a signed release APK created without errors

---

### 2. Add Required Dependencies (10 minutes)

**Update `pubspec.yaml`** - Add these dependencies:

```yaml
dependencies:
  # ... existing dependencies ...
  
  # Android optimizations
  wakelock_plus: ^1.1.4          # Keep screen on during playback
  android_intent_plus: ^4.0.3    # Better external player support
  cached_network_image: ^3.3.1   # Image caching
  connectivity_plus: ^5.0.2      # Network monitoring
```

**Install dependencies**:
```bash
flutter pub get
```

---

### 3. Implement Wake Lock (5 minutes)

**Update `lib/screens/player_screen.dart`**:

Add import at the top:
```dart
import 'package:wakelock_plus/wakelock_plus.dart';
```

Update `initState`:
```dart
@override
void initState() {
  super.initState();
  WakelockPlus.enable(); // ✅ Keep screen on
  _initializePlayer();
  // ... rest of existing code
}
```

Update `dispose`:
```dart
@override
void dispose() {
  WakelockPlus.disable(); // ✅ Allow screen to sleep
  // ... rest of existing code
  super.dispose();
}
```

✅ **Test**: Play a video and verify screen stays on

---

### 4. Improve External Player Support (15 minutes)

**Option A: Use the new service (recommended)**

The file `lib/services/external_player_service.dart` has already been created.

**Update `lib/screens/player_screen.dart`**:

Add import:
```dart
import '../services/external_player_service.dart';
```

Replace the `_openInExternalPlayer` method:
```dart
void _openInExternalPlayer() async {
  // Get available players
  final availablePlayers = await ExternalPlayerService.getInstalledPlayers();
  
  if (availablePlayers.isEmpty) {
    ExternalPlayerService.showNoPlayersDialog(context);
    return;
  }
  
  // Show player selection
  final selectedPlayer = await ExternalPlayerService.showPlayerSelectionDialog(
    context,
    availablePlayers,
  );
  
  if (selectedPlayer != null) {
    final success = await ExternalPlayerService.openInPlayer(
      streamUrl: widget.channel.url,
      player: selectedPlayer,
      title: widget.channel.name,
      headers: {'User-Agent': 'TV Viewer/1.5.0'},
    );
    
    if (!success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to open in ${selectedPlayer.displayName}')),
      );
    }
  }
}
```

✅ **Test**: Try opening a stream in VLC or MX Player

---

## 🟠 Phase 2: High Priority Enhancements (1-2 hours)

### 5. Implement Image Caching

**Update channel logo loading** (in your widgets):

Before (slow, no cache):
```dart
Image.network(channel.logo!)
```

After (fast, cached):
```dart
import 'package:cached_network_image/cached_network_image.dart';

CachedNetworkImage(
  imageUrl: channel.logo!,
  placeholder: (context, url) => const Icon(Icons.tv),
  errorWidget: (context, url, error) => const Icon(Icons.tv),
  height: 40,
  width: 40,
)
```

---

### 6. Lower minSdk for Wider Compatibility

**Update `android/app/build.gradle`**:

Change:
```gradle
minSdk 24  // Current
```

To:
```gradle
minSdk 21  // Supports Android 5.0+ (99% of devices)
```

**Test on older devices**: If possible, test on Android 5.0-6.0 devices

---

### 7. Test Release Build with ProGuard

The `proguard-rules.pro` file has already been created.

**Build and test**:
```bash
# Build release APK
flutter build apk --release

# Install on device
flutter install --release

# Or manually
adb install build/app/outputs/flutter-apk/app-release.apk
```

**Test these features thoroughly**:
- ✅ Video playback
- ✅ External player launching
- ✅ Network requests (channel loading)
- ✅ Image loading
- ✅ Navigation

If anything crashes, check logs:
```bash
adb logcat | grep -i flutter
```

---

## 🟡 Phase 3: Performance & UX Improvements (Optional)

### 8. Enable Impeller Rendering Engine

**Update `android/app/src/main/AndroidManifest.xml`**:

Add inside `<application>` tag:
```xml
<application>
    <!-- ... existing ... -->
    
    <!-- Enable Impeller for better performance -->
    <meta-data
        android:name="io.flutter.embedding.android.EnableImpeller"
        android:value="true" />
</application>
```

---

### 9. Add Network Speed Detection

**Create `lib/services/network_service.dart`**:
```dart
import 'package:connectivity_plus/connectivity_plus.dart';

class NetworkService {
  static Future<String> getNetworkType() async {
    final connectivity = await Connectivity().checkConnectivity();
    
    if (connectivity == ConnectivityResult.wifi) {
      return 'wifi';
    } else if (connectivity == ConnectivityResult.mobile) {
      return 'cellular';
    }
    return 'unknown';
  }
  
  static Future<bool> isOnWiFi() async {
    final type = await getNetworkType();
    return type == 'wifi';
  }
}
```

**Use in player**:
```dart
Future<void> _initializePlayer() async {
  try {
    // Check network before loading
    final isWiFi = await NetworkService.isOnWiFi();
    
    if (!isWiFi) {
      // Show warning for cellular data
      _showCellularWarning();
    }
    
    _videoController = VideoPlayerController.networkUrl(
      Uri.parse(widget.channel.url),
      httpHeaders: const {'User-Agent': 'TV Viewer/1.5.0'},
    );
    // ... rest of init
  }
}
```

---

## 📦 Build Optimization

### 10. Create Smaller APKs with ABI Splitting

**Update `android/app/build.gradle`**:

Add after `buildTypes`:
```gradle
android {
    // ... existing config ...
    
    splits {
        abi {
            enable true
            reset()
            include 'armeabi-v7a', 'arm64-v8a', 'x86_64'
            universalApk true  // Also generate a universal APK
        }
    }
}
```

**Build**:
```bash
flutter build apk --release --split-per-abi
```

This creates:
- `app-armeabi-v7a-release.apk` (~20 MB) - Older 32-bit devices
- `app-arm64-v8a-release.apk` (~25 MB) - Modern 64-bit devices ⭐
- `app-x86_64-release.apk` (~27 MB) - Emulators/Chromebooks
- `app-release.apk` (~50 MB) - Universal fallback

**Distribution**: Upload the arm64-v8a version to Play Store (most common)

---

### 11. Build App Bundle for Play Store

```bash
flutter build appbundle --release
```

Output: `build/app/outputs/bundle/release/app-release.aab`

This is the preferred format for Google Play Store (automatically optimized per-device).

---

## 🧪 Testing Checklist

After implementing the critical fixes, test:

### Functional Testing
- [ ] App launches successfully
- [ ] Channels load from M3U sources
- [ ] Video plays in built-in player
- [ ] Screen stays on during playback (wake lock)
- [ ] Opening stream in VLC works
- [ ] Opening stream in MX Player works
- [ ] Player controls work (play/pause, back button)
- [ ] Channel logos load and are cached
- [ ] Search works
- [ ] Category filtering works

### Release Build Testing
- [ ] Build release APK successfully
- [ ] Install release APK on device
- [ ] No crashes in release mode
- [ ] ProGuard doesn't break functionality
- [ ] APK size is reasonable (<50 MB)

### Device Testing
Test on different Android versions:
- [ ] Android 14 (API 34)
- [ ] Android 10 (API 29)
- [ ] Android 7 (API 24)
- [ ] Android 5/6 (API 21-23) if lowered minSdk

### Network Testing
- [ ] Works on WiFi
- [ ] Works on mobile data
- [ ] Handles network loss gracefully
- [ ] Resumes playback after network recovery

---

## 🚀 Deployment

### For Testing (Internal)
```bash
# Build release APK
flutter build apk --release

# Share the APK file from:
build/app/outputs/flutter-apk/app-release.apk
```

### For Play Store
```bash
# Build app bundle
flutter build appbundle --release

# Upload to Play Store Console:
build/app/outputs/bundle/release/app-release.aab
```

---

## 🔍 Troubleshooting

### Issue: Release build crashes
**Solution**: Check ProGuard rules, add more -keep rules if needed

### Issue: External players don't open
**Solution**: Verify players are installed, check AndroidManifest.xml queries

### Issue: Screen turns off during playback
**Solution**: Ensure wakelock_plus is added and enabled in player

### Issue: Images don't load
**Solution**: Check internet permission, verify network security config

### Issue: Build fails with signing error
**Solution**: Verify key.properties file exists and paths are correct

---

## 📚 Additional Resources

- **Full Review**: See `ANDROID_REVIEW_RECOMMENDATIONS.md`
- **Flutter Docs**: https://docs.flutter.dev/
- **Android Developer**: https://developer.android.com/
- **ProGuard**: https://www.guardsquare.com/manual/configuration

---

## ⏱️ Estimated Timeline

- **Phase 1 (Critical)**: 1-2 hours
- **Phase 2 (High Priority)**: 2-3 hours
- **Phase 3 (Optional)**: 2-4 hours
- **Testing**: 2-3 hours

**Total**: 1-2 days for full implementation and testing

---

## ✅ Success Metrics

After implementation:
- ✅ Release APK builds successfully with proper signing
- ✅ No crashes in release mode
- ✅ Screen doesn't turn off during playback
- ✅ External players work reliably
- ✅ APK size < 50 MB (or < 30 MB with ABI splits)
- ✅ Smooth 60 FPS UI performance
- ✅ Fast image loading with caching

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Next Review**: After Phase 1 completion

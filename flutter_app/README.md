# TV Viewer - Flutter Android App

A native Android IPTV streaming application built with Flutter.

## Features

- 🌍 Discovers free IPTV streams from open repositories
- ✓ Validates stream availability in background
- 🔍 Search and filter channels by category
- 📺 Built-in video player with full controls
- 📱 Optimized for Android (Samsung Galaxy S24 Ultra compatible)
- 🎨 Material You design with dark/light theme support

## Building

### Requirements

- Flutter SDK 3.19.0+
- Android SDK 34
- Java 17

### Build APK

```bash
cd flutter_app
flutter pub get
flutter build apk --release
```

The APK will be at: `build/app/outputs/flutter-apk/app-release.apk`

### Build via GitHub Actions

Push changes to the `flutter_app/` directory to trigger automatic APK build.
Download from the Actions tab artifacts.

## Project Structure

```
flutter_app/
├── lib/
│   ├── main.dart           # App entry point
│   ├── models/
│   │   └── channel.dart    # Channel data model
│   ├── providers/
│   │   └── channel_provider.dart  # State management
│   ├── screens/
│   │   ├── home_screen.dart    # Main channel list
│   │   └── player_screen.dart  # Video player
│   └── services/
│       └── m3u_service.dart    # M3U parsing & HTTP
├── android/                # Android-specific config
└── pubspec.yaml           # Dependencies
```

## Dependencies

- `video_player` - Native video playback
- `chewie` - Video player UI controls
- `provider` - State management
- `http` / `dio` - HTTP client
- `shared_preferences` - Local storage

## Reliability checks

Run the focused Android recovery regressions from `flutter_app`:

```bash
flutter test test/screens/android_reliability_test.dart test/utils/logger_storage_test.dart
```

Repository saves and retained Undo actions must not update a disposed screen.
Community statistics discard malformed caches, retain valid offline data, and
keep newly fetched data visible when local cache writes fail, with a Snackbar
explaining that the data could not be saved. Log export filesystem failures
reach the existing export-error Snackbar rather than appearing as "no logs".

The tests reproduce these application failure paths, not the precise production
incidents: issues #295/#296, #299, and #304 only contain framework stack frames.
Issue #308's range error has no confirmed application callsite, and #309 is a
debug layout overflow; neither is claimed fixed by these changes.

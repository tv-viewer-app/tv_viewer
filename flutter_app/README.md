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

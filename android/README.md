# TV Viewer for Android

Mobile IPTV streaming app built with Kivy/Python for Android devices.

## Target Device
- Samsung Galaxy S24 Ultra (and other Android 8.0+ devices)

## Building the APK

### Prerequisites

1. **Install Buildozer** (on Linux/WSL):
   ```bash
   pip install buildozer
   pip install cython==0.29.33
   ```

2. **Install Android SDK/NDK dependencies**:
   ```bash
   # On Ubuntu/Debian:
   sudo apt-get install -y \
       python3-pip \
       build-essential \
       git \
       python3-dev \
       ffmpeg \
       libsdl2-dev \
       libsdl2-image-dev \
       libsdl2-mixer-dev \
       libsdl2-ttf-dev \
       libportmidi-dev \
       libswscale-dev \
       libavformat-dev \
       libavcodec-dev \
       zlib1g-dev \
       libgstreamer1.0-dev \
       gstreamer1.0-plugins-base \
       libgstreamer-plugins-base1.0-dev \
       libunwind-dev
   ```

### Build Steps

1. **Navigate to android directory**:
   ```bash
   cd android
   ```

2. **Build debug APK**:
   ```bash
   buildozer android debug
   ```

3. **Build release APK** (for Play Store):
   ```bash
   buildozer android release
   ```

4. **Deploy to connected device**:
   ```bash
   buildozer android debug deploy run
   ```

### Output

APK files will be in: `android/bin/`
- Debug: `tvviewer-1.2.0-arm64-v8a-debug.apk`
- Release: `tvviewer-1.2.0-arm64-v8a-release.apk`

## Features

- Browse 10,000+ IPTV channels
- Search and filter by category
- Play streams via VLC for Android or any video player
- Dark theme optimized for OLED displays
- Smooth scrolling with RecycleView

## Required Apps on Device

For best experience, install one of these video players:
- **VLC for Android** (Recommended)
- MX Player
- Any video player that supports network streams

## Architecture Support

- `arm64-v8a` - Samsung Galaxy S24 Ultra, modern 64-bit devices
- `armeabi-v7a` - Older 32-bit devices (fallback)

## Troubleshooting

### Build fails with SDK error
```bash
buildozer android update
```

### Permission denied on Android
The app requires INTERNET permission which is declared in buildozer.spec.

### Streams don't play
1. Install VLC for Android
2. Or install any video player that supports HTTP/HTTPS streams

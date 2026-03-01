# TV Viewer

A cross-platform IPTV streaming application for Windows and Android.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flutter](https://img.shields.io/badge/Flutter-3.19-02569B.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Android-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Version](https://img.shields.io/badge/Version-2.0.0-orange.svg)

## Features

- 🌍 **Auto-discover IPTV repositories** — Fetches channels from 80+ configurable sources
- 🇮🇱 **Israeli channels included** — KAN 11, Reshet 13, Channel 14, i24NEWS, Makan 33, Kan Kids, and 50+ more with verified working CDN URLs
- ✅ **Background channel validation** — Validates streams with concurrent checking
- 📂 **Categorized channel list** — Channels organized by category, country, or language
- 📺 **Media type filtering** — Filter by TV, Radio, or All
- 🎬 **Embedded video player** — VLC-powered player (Windows) / native player (Android)
- 💾 **Persistent cache** — Saves working channels for faster startup
- 🎨 **Windows 11 Fluent Design** — Modern dark theme with ttkbootstrap
- 📱 **Android app** — Flutter-based mobile app with Material Design
- 🔒 **No login required** — Just start and watch

## Downloads

| Platform | Download | Size |
|----------|----------|------|
| Windows | [`dist/TV_Viewer.exe`](dist/TV_Viewer.exe) | ~25 MB |
| Android | [`dist/android/TV_Viewer_v2.0.0.apk`](dist/android/TV_Viewer_v2.0.0.apk) | ~51 MB |

> **Note:** Windows requires [VLC media player](https://www.videolan.org/vlc/) to be installed.

## Quick Start

### Windows
1. Download `TV_Viewer.exe` from `dist/` folder
2. Install [VLC](https://www.videolan.org/vlc/) if not already installed
3. Double-click to run

### Android
1. Download `TV_Viewer_v2.0.0.apk` from `dist/android/`
2. Enable "Install from unknown sources" in Settings
3. Install and open

### From Source (Windows/Linux)
```bash
pip install -r requirements.txt
python main.py
```

## Tech Stack

| Component | Windows (Python) | Android (Flutter) |
|-----------|-----------------|-------------------|
| UI Framework | ttkbootstrap (Fluent Design) | Flutter / Material Design |
| Video Player | VLC (python-vlc) | video_player |
| HTTP Client | aiohttp + requests | http package |
| Concurrency | asyncio + threading | Dart async/await |
| Data Storage | JSON files | SharedPreferences |
| Build | PyInstaller | Flutter build / GitHub Actions |

## Documentation

| Document | Description |
|----------|-------------|
| [CHANGELOG.md](CHANGELOG.md) | Version history and changes |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and design |
| [SUPPORT_GUIDE.md](SUPPORT_GUIDE.md) | Troubleshooting guide |
| [PERFORMANCE.md](PERFORMANCE.md) | Performance optimization guide |
| [API.md](API.md) | API reference for developers |

## Keyboard Shortcuts (Windows)

| Key | Action |
|-----|--------|
| `Space` | Play/Pause |
| `F` | Toggle fullscreen |
| `M` | Toggle mute |
| `Escape` | Exit fullscreen |

## Project Structure

```
tv_viewer_project/
├── main.py                 # Windows app entry point
├── config.py               # Configuration (version, tuning params)
├── channels_config.json    # Repository list + custom channels
├── requirements.txt        # Python dependencies
├── build.py                # Windows EXE build script
├── dist/
│   ├── TV_Viewer.exe       # Windows executable
│   └── android/            # Android APK
├── flutter_app/            # Flutter Android app source
├── core/                   # Channel manager, repo handler, stream checker
├── ui/                     # Windows UI (main window, player, constants)
├── utils/                  # Helpers, logger, thumbnails
├── tests/                  # Automated tests
└── .github/workflows/      # CI/CD (12 workflows)
```

## Building

### Windows EXE
```bash
python build.py          # Build single-file EXE
python build.py --clean  # Clean build artifacts first
```

### Android APK
APK is built automatically by GitHub Actions on push to `flutter_app/**`.
Manual trigger: `gh workflow run android-build.yml`

### Validation
```bash
python -m pytest tests/ -v           # Unit tests
python tests/validate_build.py       # Pre-release validation
```

## CI/CD

12 GitHub Actions workflows automate testing, security scanning, and builds:
- **android-build.yml** — Flutter APK build on push
- **test.yml** — Multi-platform test matrix
- **pr-validation.yml** — PR gate (flake8, bandit, tests)
- **security-gate.yml** — Security scanning
- **cve-scanner.yml** — Daily CVE scanning
- **release-gate.yml** — 5-stage release gate
- **build-release.yml** — Automated GitHub Release creation

## Troubleshooting

See [SUPPORT_GUIDE.md](SUPPORT_GUIDE.md) for detailed troubleshooting.

| Problem | Solution |
|---------|----------|
| VLC not found | Install VLC from [videolan.org](https://www.videolan.org/vlc/) |
| No channels | Check internet connection, click "Refresh" |
| Stream not playing | Try another channel — some may be geo-restricted or offline |
| App crashes on Windows | Ensure ttkbootstrap and Pillow are installed |

## License

MIT License — Feel free to use and modify as needed.

## Credits

- [IPTV-org](https://github.com/iptv-org/iptv) community playlists
- [python-vlc](https://pypi.org/project/python-vlc/) for video playback
- [ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap) for modern UI
- [Flutter](https://flutter.dev/) for Android app

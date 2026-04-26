# 📺 TV Viewer

**Community-powered IPTV player with 8000+ crowdsourced channels. Free forever.**

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub Issues](https://img.shields.io/github/issues/tv-viewer-app/tv_viewer)](https://github.com/tv-viewer-app/tv_viewer/issues)
[![Latest Release](https://img.shields.io/github/v/release/tv-viewer-app/tv_viewer)](https://github.com/tv-viewer-app/tv_viewer/releases/latest)
![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Android-green.svg)

> **🌐 [Visit the TV Viewer Landing Page →](https://tv-viewer-app.github.io/tv_viewer/)**

**TV Viewer** is a free, open-source IPTV player where the community maintains the channel list. Users report broken streams, submit new channels, and rate quality — making the experience better for everyone. No account needed. No ads. No tracking.

## Support the Project 🍺

If TV Viewer saves you a cable bill or just makes your day better, consider supporting development:

<a href="https://ko-fi.com/tvviewerapp"><img src="https://img.shields.io/badge/Ko--fi-Buy%20Me%20a%20Beer%20🍺-ff5e5b?style=for-the-badge&logo=ko-fi&logoColor=white" alt="Ko-fi"></a>

## ✨ What's New in v2.6.3

- **📻 Radio player** — Radio channels now show station name, country, and audio icon instead of a blank screen
- **👆 Swipe to report** — Swipe any channel left to report it as broken (Android)
- **🔽 Collapsible filters** — Tap the Filters arrow to collapse and get a full-screen channel list
- **🔤 Hebrew font support** — Hebrew channel names now render correctly (was showing garbled text)
- **🔒 Simplified parental controls** — Single over-18 toggle controls adult content visibility

## Features

- 🌍 **8000+ Channels Worldwide** — Aggregated from 80+ configurable sources, growing daily
- 👥 **Crowdsourced Quality** — Users report broken streams and submit new channels via app or GitHub
- 🇮🇱 **Israeli channels included** — KAN 11, Reshet 13, Channel 14, i24NEWS, Makan 33, Kan Kids, and 50+ more
- ✅ **Background channel validation** — Concurrent stream checking with smart priority queue
- 📂 **Categorized channel list** — Filter by category, country, language, or media type (TV/Radio)
- 📻 **Radio support** — Dedicated radio player with station name display and audio visualizer
- 🎬 **Embedded video player** — VLC-powered (Windows) / native player (Android)
- 🔀 **Source selector** — Switch between alternative stream sources without leaving the player
- 💾 **Offline mode** — Persistent local cache works without internet
- 🧹 **Channel consolidation** — Multi-pass name normalization eliminates duplicates across sources
- 🎨 **Windows 11 Fluent Design** — Modern dark theme with ttkbootstrap
- 📱 **Android app** — Flutter-based with Material Design and gesture controls
- 🌐 **Shared health database** — Supabase-backed health sharing surfaces working streams community-wide
- 📊 **Privacy-first telemetry** — Opt-in anonymous usage analytics with no PII collection
- 🔒 **No login required** — Just start and watch
- 📺 **EPG Program Guide** — XMLTV-based Now/Next display with live progress bar
- ⏱ **Watch history** — Recently played channels with play counts
- 🔐 **Parental controls** — PIN-locked category blocking and over-18 age gate
- 🔍 **Advanced search** — Prefix filters (`country:US`, `category:news`, `working:`) with fuzzy matching
- 🛡️ **SSRF protection** — Server-side request forgery guards on all outbound URL fetches

## Contributing Channels

The heart of TV Viewer is its crowdsourced channel database. Help make it better:

### Via the App (Easiest)
- **Report broken channels** — Swipe left on any channel (Android) or right-click (Windows) → "Report Broken"
- **Report wrong info** — Long-press (Android) or right-click (Windows) → "Wrong Info" to fix misclassified channels
- **Submit new channels** — Settings → "Add Channel" with a stream URL you've discovered
- **Rate quality** — Health data syncs anonymously to the shared database

### Via GitHub
1. Open a [Channel Request](https://github.com/tv-viewer-app/tv_viewer/issues/new?template=channel_request.yml) — our bot will auto-search IPTV databases and create a PR
2. Open a [Channel Report](https://github.com/tv-viewer-app/tv_viewer/issues/new?template=channel_report.yml) — report broken or misclassified channels
3. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide

## Downloads

| Platform | Download | Notes |
|----------|----------|-------|
| Android | [Latest APK](https://github.com/tv-viewer-app/tv_viewer/releases/latest) | Android 7.0+ (API 24) |
| Windows | [Latest EXE](https://github.com/tv-viewer-app/tv_viewer/releases/latest) | Requires [VLC](https://www.videolan.org/vlc/) |
| Linux | [From source](#from-source-windowslinux) | Python 3.12+ + VLC |

## Quick Start

### Windows
1. Download `TV_Viewer.exe` from [Releases](https://github.com/tv-viewer-app/tv_viewer/releases/latest)
2. Install [VLC](https://www.videolan.org/vlc/) if not already installed
3. Double-click to run

### Android
1. Download the `.apk` from [Releases](https://github.com/tv-viewer-app/tv_viewer/releases/latest)
2. Enable "Install from unknown sources" in Settings
3. Install and open

### From Source (Windows/Linux)
```bash
git clone https://github.com/tv-viewer-app/tv_viewer.git
cd tv_viewer
pip install -r requirements.txt
python main.py
```

## Tech Stack

| Component | Windows (Python / tkinter) | Android (Flutter / Dart) |
|-----------|---------------------------|--------------------------|
| UI Framework | ttkbootstrap / tkinter (Fluent Design) | Flutter / Material Design |
| Video Player | VLC (python-vlc) | video_player |
| HTTP Client | aiohttp + requests | http package |
| Concurrency | asyncio + threading | Dart async/await |
| Data Storage | JSON files | SharedPreferences |
| Cloud Backend | Supabase (crowd-sourced health) | Supabase (crowd-sourced health) |
| Build | PyInstaller | Flutter build / GitHub Actions |

## Documentation

| Document | Description |
|----------|-------------|
| [🌐 Landing Page](https://tv-viewer-app.github.io/tv_viewer/) | Project homepage with screenshots and downloads |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute channels, bugs, and code |
| [CHANGELOG.md](CHANGELOG.md) | Version history and changes |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and design |
| [SUPPORT_GUIDE.md](docs/SUPPORT_GUIDE.md) | Troubleshooting guide |
| [PERFORMANCE.md](docs/PERFORMANCE.md) | Performance optimization guide |
| [API.md](docs/API.md) | API reference for developers |
| [TEST_PLAN.md](docs/TEST_PLAN.md) | Test plan and coverage |
| [RELEASE_PROCESS.md](docs/RELEASE_PROCESS.md) | Release checklist |
| [PRIVACY_POLICY.md](PRIVACY_POLICY.md) | Privacy policy |

## Keyboard Shortcuts (Windows)

| Key | Action |
|-----|--------|
| `Ctrl+F` | Focus search box |
| `Ctrl+,` | Open settings |
| `F5` | Refresh channels |
| `Escape` | Clear search / exit fullscreen |
| `Space` | Play/Pause (in player) |
| `F` | Toggle fullscreen (in player) |
| `M` | Toggle mute (in player) |
| `←` / `→` | Previous / Next channel (in player) |
| `↑` / `↓` | Volume up / down (in player) |

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
├── ui/                     # Windows UI (main window, player, toast, tooltips)
├── utils/                  # Helpers, EPG, history, parental, logger, thumbnails
├── tests/                  # Automated tests (255+ tests)
├── docs/                   # Documentation + landing page
│   └── index.html          # GitHub Pages landing page
└── .github/workflows/      # CI/CD (6 workflows)
```

## Building

### Windows EXE
```bash
python build.py          # Build single-file EXE
python build.py --clean  # Clean build artifacts first
```

### Android APK
APK is built automatically by GitHub Actions on push to `flutter_app/**`.
Manual trigger: `gh workflow run build-apk.yml`

### Validation
```bash
python -m pytest tests/ -v           # Unit tests
python tests/validate_build.py       # Pre-release validation
```

## CI/CD

6 GitHub Actions workflows automate testing, security scanning, and builds:
- **build-apk.yml** — Flutter APK build on push
- **build.yml** — Windows EXE build
- **ci.yml** — Multi-platform CI (lint, test, build)
- **cve-scanner.yml** — Daily CVE scanning
- **release.yml** — Automated GitHub Release creation
- **supabase-keepalive.yml** — Supabase backend keep-alive pings

## Troubleshooting

See [SUPPORT_GUIDE.md](docs/SUPPORT_GUIDE.md) for detailed troubleshooting.

| Problem | Solution |
|---------|----------|
| VLC not found | Install VLC from [videolan.org](https://www.videolan.org/vlc/) |
| No channels | Check internet connection, click "Refresh" |
| Duplicate channels | Clear cache — channels consolidate automatically on next load |
| Stream not playing | Use the source selector in the player to try an alternative stream |
| Supabase unavailable | App works fully offline; health sharing resumes when connectivity returns |
| Hebrew/RTL text garbled | Update to v2.6.3+ which includes proper font fallback |

## License

MIT License — see [LICENSE](LICENSE) for details.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for how to:
- 📺 Submit new channels or report broken ones
- 🐛 Report bugs
- 💻 Contribute code
- 📖 Improve documentation

## Credits

- [IPTV-org](https://github.com/iptv-org/iptv) community playlists
- [python-vlc](https://pypi.org/project/python-vlc/) for video playback
- [ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap) for modern UI
- [Flutter](https://flutter.dev/) for Android app

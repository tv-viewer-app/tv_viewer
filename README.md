# 📺 TV Viewer

**Community-powered IPTV player with 16,000+ crowdsourced channels, privacy-first analytics, and community statistics.**

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Latest Release](https://img.shields.io/github/v/release/tv-viewer-app/tv_viewer)](https://github.com/tv-viewer-app/tv_viewer/releases/latest)
![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Flutter](https://img.shields.io/badge/Flutter-3.32.0-02569B.svg)
[![Docker](https://img.shields.io/badge/Docker-latest-2496ED.svg)](https://hub.docker.com/r/asummoner/tvviewerapp)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Android%20%7C%20Web%20%7C%20Docker-green.svg)

> **🌐 [Visit the TV Viewer Landing Page →](https://tv-viewer-app.github.io/tv_viewer/)**

TV Viewer is a free, open-source IPTV player where the community maintains the channel list. Users report broken streams, submit new channels, and anonymously share aggregate usage signals that improve stream health and discovery for everyone. No account needed. No ads. No tracking by default.

## Support the Project 🍺

If TV Viewer saves you a cable bill or just makes your day better, consider supporting development:

<a href="https://ko-fi.com/tvviewerapp"><img src="https://img.shields.io/badge/Ko--fi-Buy%20Me%20a%20Beer%20🍺-ff5e5b?style=for-the-badge&logo=ko-fi&logoColor=white" alt="Ko-fi"></a>

## ✨ What's New in v2.20.2

- **Community Statistics page** now shows richer totals for channels, categories, countries, and recent additions
- **Timezone-based country detection** improves local recommendations and privacy-preserving analytics on Android and Web
- **Supabase backend migrated** to project `cdtxpefohpwtusmqengu`
- **APKPure notify workflow** added to the release pipeline
- **Docker Hub stays current** with `asummoner/tvviewerapp:latest`

_See the [CHANGELOG](CHANGELOG.md) for full release history._

## Features

- 🌍 **16,000+ channels worldwide** — Aggregated from community-maintained playlists and configurable sources
- 👥 **Crowdsourced quality** — Users report broken streams and submit fixes from the app or GitHub
- 📊 **Community Statistics** — Anonymous aggregated usage data for active users, plays, countries, and platform trends
- 🌐 **Timezone-based country detection** — Privacy-friendly local country inference without GPS or IP lookup
- 📂 **Rich browsing** — Filter by category, country, language, and media type (TV/Radio)
- 📻 **Dedicated radio experience** — Background audio playback, genre browsing, and now-playing controls on Android
- 🔀 **Multi-source failover** — Switch between alternative stream sources without leaving playback
- 💾 **Offline-friendly caching** — Local cache and favorites still work when Supabase is unavailable
- 📺 **EPG support** — XMLTV-based now/next program data with live progress bars
- 🔒 **Privacy-first telemetry** — Opt-in analytics only, with no login and no PII collection
- 🛡️ **Hardened web backend** — SSRF protections, safe Supabase writes, and server-side statistics aggregation
- 🐳 **Self-hosted web/Docker edition** — FastAPI + HLS.js UI for NAS and browser deployments

## Availability

| Channel | Status | Notes |
|---------|--------|-------|
| GitHub Releases | ✅ Live | Windows zip, Linux source, Android APK + AAB assets |
| Google Play | ✅ Live | Primary Android store distribution |
| F-Droid | 🟡 MR open | `fdroid-build.yml` produces unsigned APK artifacts |
| APKPure | 🟡 Pending | `apkpure-notify.yml` helps release discovery |
| Samsung Galaxy Store | 🟡 Pending | Planned additional Android storefront |
| Docker Hub | ✅ Live | `asummoner/tvviewerapp:latest` |

## Downloads

| Platform | Download | Notes |
|----------|----------|-------|
| Android | [Google Play](https://play.google.com/store/apps/details?id=app.tvviewer.player) / [Latest Release](https://github.com/tv-viewer-app/tv_viewer/releases/latest) | Android 8.0+ (API 26) |
| Windows | [Latest Release](https://github.com/tv-viewer-app/tv_viewer/releases/latest) | Self-contained, VLC bundled |
| Web / Docker | `docker run -p 8765:8765 asummoner/tvviewerapp:latest` | Browser-based, NAS-friendly |
| Linux | [From source](#from-source-windowslinux) | Python 3.12+ + VLC |

## Quick Start

### Windows
1. Download the latest Windows asset from [Releases](https://github.com/tv-viewer-app/tv_viewer/releases/latest)
2. Extract anywhere and run `TVViewer.exe`

### Android
1. Install from **Google Play** or download the latest APK from [Releases](https://github.com/tv-viewer-app/tv_viewer/releases/latest)
2. Open TV Viewer and start browsing channels immediately

### From Source (Windows/Linux)
```bash
git clone https://github.com/tv-viewer-app/tv_viewer.git
cd tv_viewer
pip install -r requirements.txt
python main.py
```

### Web Interface (Docker)
```bash
docker run -d --name tv-viewer -p 8765:8765 --restart unless-stopped asummoner/tvviewerapp:latest
# Open http://localhost:8765
```

### Web Interface (Dev)
```bash
pip install -r web/requirements.txt
python -m web.server
# Open http://localhost:8765
```

## Tech Stack

| Layer | Stack | Notes |
|------|-------|-------|
| Desktop | Python 3.12 + CustomTkinter + VLC | Native Windows/Linux client |
| Mobile | Flutter 3.32.0 + Material 3 | Gradle 8.9, AGP 8.7.0, Kotlin 1.9.22 |
| Web | FastAPI + vanilla JS + HLS.js | Browser UI + self-hosted Docker image |
| Shared backend | Supabase (`cdtxpefohpwtusmqengu`) | Channels, status, analytics, aggregated stats |
| Android audio | `just_audio` + `audio_service` | Background playback for radio streams |
| CI/CD | 28 GitHub Actions workflows | Release, store, Docker, analytics, backend ops |

## Documentation

| Document | Description |
|----------|-------------|
| [CHANGELOG.md](CHANGELOG.md) | Version history and release notes |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and current platform stack |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute channels, code, and docs |
| [docs/SUPPORT_GUIDE.md](docs/SUPPORT_GUIDE.md) | Troubleshooting guide |
| [docs/API.md](docs/API.md) | API notes for the web backend |
| [docs/TEST_PLAN.md](docs/TEST_PLAN.md) | Test plan and coverage |
| [docs/RELEASE_PROCESS.md](docs/RELEASE_PROCESS.md) | Release checklist |
| [PRIVACY_POLICY.md](PRIVACY_POLICY.md) | Privacy policy |

## Project Structure

```
tv_viewer_project/
├── main.py                 # Desktop entry point
├── config.py               # Configuration and current version (2.20.2)
├── Dockerfile              # Docker image definition
├── core/                   # Channel manager, repository, stream checker
├── ui/                     # Desktop UI
├── utils/                  # Shared utilities, analytics, normalization, Supabase client
├── web/                    # FastAPI backend + static web client
├── flutter_app/            # Flutter Android app source + fastlane metadata
├── tests/                  # Python tests (299+)
├── docs/                   # Project documentation
└── .github/workflows/      # CI/CD automation (28 workflows)
```

## CI/CD

TV Viewer uses **28 GitHub Actions workflows** across validation, release orchestration, store publishing, Docker publishing, analytics, and Supabase maintenance. Key workflows include:

- `ci.yml` — core CI for Python/Web changes
- `build.yml` / `release.yml` / `release-gate.yml` — release pipeline and gating
- `build-apk.yml` / `play-store-deploy.yml` — Android APK/AAB build and Google Play deployment
- `fdroid-build.yml` / `apkpure-notify.yml` — alternate Android distribution channels
- `docker-publish.yml` — multi-arch Docker Hub publish (`latest` + version tags)
- `supabase-*.yml` and analytics workflows — backend health, keepalive, monitoring, reporting

## Troubleshooting

See [docs/SUPPORT_GUIDE.md](docs/SUPPORT_GUIDE.md) for detailed troubleshooting.

| Problem | Solution |
|---------|----------|
| VLC not found | The Windows release bundles VLC. From source, install VLC locally |
| No channels | Check connectivity and refresh sources |
| Stream not playing | Try another source from the source selector |
| Statistics unavailable | Verify the web server can reach Supabase and `/api/statistics` is enabled |
| Supabase unavailable | The app continues to work from cache; analytics and shared health resume later |

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for how to:
- 📺 Submit new channels or report broken ones
- 🐛 Report bugs
- 💻 Contribute code
- 📖 Improve documentation

## License

MIT License — see [LICENSE](LICENSE) for details.

## Credits

- [IPTV-org](https://github.com/iptv-org/iptv) and other community playlist maintainers
- [python-vlc](https://pypi.org/project/python-vlc/) for desktop playback
- [Flutter](https://flutter.dev/) for the Android client
- [Supabase](https://supabase.com/) for the shared backend and aggregated analytics

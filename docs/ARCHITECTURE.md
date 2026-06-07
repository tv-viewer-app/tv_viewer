# TV Viewer — Architecture Documentation

## Overview

TV Viewer is a community-powered IPTV application with **three clients** sharing a common Supabase backend:

- **Desktop:** Python + CustomTkinter + VLC for Windows/Linux
- **Mobile:** Flutter 3.32.0 for Android
- **Web/Docker:** FastAPI + vanilla JS + HLS.js for self-hosted browser playback

**Current version:** 2.20.2  
**Supabase project:** `cdtxpefohpwtusmqengu`  
**Distribution:** GitHub Releases, Google Play, Docker Hub (`asummoner/tvviewerapp:latest`), with F-Droid / APKPure / Samsung storefront work in progress

## Technology Stack

| Layer | Technology | Notes |
|------|------------|-------|
| Desktop UI | CustomTkinter + ttkbootstrap | Native dark-themed UI |
| Desktop playback | VLC via `python-vlc` | No hardware-acceleration flags enabled |
| Mobile UI | Flutter 3.32.0 + Material 3 | Android app |
| Android build chain | Gradle 8.9, AGP 8.7.0, Kotlin 1.9.22 | Release-aligned toolchain |
| Mobile playback | `video_player`, `just_audio`, `audio_service` | Video + background radio playback |
| Web backend | FastAPI + Uvicorn | Single-file `web/server.py` |
| Web frontend | Vanilla JS + HLS.js | `web/static/index.html` SPA |
| Shared backend | Supabase Postgres + PostgREST | Channels, health, analytics, aggregated stats |
| HTTP | `aiohttp` + `requests` | Async fetch and safe outbound calls |
| EPG | XMLTV | `utils/epg.py` |
| CI/CD | GitHub Actions (28 workflows) | Builds, releases, stores, Docker, backend ops |

## High-Level Architecture

```
Playlist sources ──> Repository fetch / normalization ──> Shared channel model
                                                     ├─> Desktop client (Tk + VLC)
                                                     ├─> Android client (Flutter)
                                                     └─> Web client (FastAPI + HLS.js)

All clients ──> Supabase (`channels`, `channel_status`, `analytics_events`)
            └─> Aggregated statistics via `/api/statistics`
```

## Client Architecture

### Desktop (Python)

Key modules:

- `core/channel_manager.py` — in-memory source of truth for loaded channels
- `core/repository.py` — async M3U fetching and repository management
- `core/stream_checker.py` — background validation on a daemon thread
- `ui/main_window.py` — main Tk UI; all background-thread UI updates must use `root.after()`
- `ui/player_window.py` — VLC playback window and source selector

Important runtime rule: **Tk widgets must never be updated directly from background threads.**

### Mobile (Flutter / Android)

Key modules:

- `flutter_app/lib/screens/home_screen.dart` — app shell and navigation
- `flutter_app/lib/screens/player_screen.dart` — video playback UI
- `flutter_app/lib/screens/radio_screen.dart` — radio-focused playback experience
- `flutter_app/lib/screens/statistics_screen.dart` — Community Statistics page
- `flutter_app/lib/services/analytics_service.dart` — opt-in analytics + timezone-based country detection
- `flutter_app/lib/services/shared_db_service.dart` — Supabase reads/writes for shared health data
- `flutter_app/lib/services/audio_handler.dart` — background audio playback

Flutter builds inject Supabase credentials with `--dart-define` at build time.

### Web / Docker

Key modules:

- `web/server.py` — FastAPI server, API routes, proxying, statistics, and Supabase integration
- `web/static/index.html` — single-page client using HLS.js
- `utils/supabase_channels.py` — shared DB helpers for channel status updates
- `utils/normalize.py` — canonical category/country normalization shared conceptually across clients

Primary routes:

- `GET /api/channels`
- `POST /api/refresh`
- `POST /api/health/report`
- `GET /api/epg/{channel}`
- `GET /api/statistics`
- `GET /proxy`

The Docker image is published as **`asummoner/tvviewerapp`** with both versioned and `latest` tags.

## Shared Backend (Supabase)

Supabase is the system of record for shared channel metadata, crowd-sourced health, and anonymous analytics. The active project is **`cdtxpefohpwtusmqengu`**.

Key data surfaces:

| Object | Purpose |
|--------|---------|
| `channels` | Shared channel catalog with URL hashes, metadata, and source info |
| `channel_status` | Working/broken status and report counts |
| `analytics_events` | Opt-in anonymous analytics events |
| `v_channels_with_sources` | RLS-respecting view for client consumption |
| `mv_daily_active_users` | Aggregated stats for dashboards and community statistics |

Clients never query raw analytics tables for the statistics UI; they consume **server-side aggregated results** from `/api/statistics`.

## Data Flow

1. Repository sources are fetched and parsed from public M3U playlists
2. Category and country data are normalized
3. Channels are deduplicated into multi-source entries (`url` + `urls[]`)
4. Clients cache data locally for offline resilience
5. Health reports and analytics flow to Supabase
6. Aggregated anonymous metrics are exposed through the Community Statistics page

## Community Statistics

Version 2.19+ introduced the **Community Statistics** feature.

- **Android:** `statistics_screen.dart` from the home menu
- **Web:** stats panel opened from the 📊 button
- **Backend:** `GET /api/statistics` in `web/server.py`
- **Data shape:** anonymous totals for active users, plays, countries, channels, and platform breakdowns

The implementation is privacy-preserving: no raw personal identifiers are displayed or exposed to clients.

## Country Detection

TV Viewer uses **timezone-based country detection** in Android and Web for localized relevance and analytics without GPS or IP geolocation.

- **Android:** `analytics_service.dart` maps timezone name / offset to country code
- **Web:** `web/server.py` detects local country and `index.html` reports timezone-derived locale hints

## Security and Privacy

- `/api/health/report` is the only client-to-shared-DB write surface exposed by the web app
- Values sent to Supabase must be validated and encoded via request params, never interpolated into query URLs
- `/proxy` blocks private IP ranges to reduce SSRF risk
- Analytics are opt-in and designed to avoid PII
- Channel URLs are represented by hashes where appropriate when shared with backend services

## Project Structure

```
tv_viewer_project/
├── config.py                     # Global config + app version
├── core/                         # Channel management and validation
├── ui/                           # Desktop UI
├── utils/                        # Shared helpers, normalization, analytics, Supabase
├── web/server.py                 # FastAPI backend
├── web/static/index.html         # Web SPA
├── flutter_app/lib/              # Android app source
├── flutter_app/fastlane/metadata # Play Store metadata
├── docs/                         # Project docs
└── .github/workflows/            # 28 automation workflows
```

## Release and Distribution Architecture

The release system spans GitHub Releases plus store-specific workflows:

- `build.yml`, `release-gate.yml`, `release.yml` — canonical release path
- `build-apk.yml` — ad-hoc Android APK/AAB builds
- `play-store-deploy.yml` — Google Play publishing
- `fdroid-build.yml` — F-Droid-compatible unsigned APK generation
- `apkpure-notify.yml` — APKPure release discovery automation
- `docker-publish.yml` — multi-arch Docker Hub publishing

## Verification Commands

```bash
python tests/validate_build.py --quick
python -m pytest tests/ -q
cd flutter_app && flutter test
cd flutter_app && flutter analyze
```

# TV Viewer Project - Copilot Instructions

## Project Overview
Community-powered IPTV streaming application with **three clients** sharing a
common Supabase backend for channel data and analytics:

- **Desktop** (Python + CustomTkinter): Windows / Linux native app, VLC playback
- **Mobile** (Flutter 3.32): Android (Google Play), iOS scaffolding
- **Web / Docker** (FastAPI + vanilla JS): self-hosted server, browser UI

**Version:** 2.20.2 (semver, kept in sync via `config.py`, `flutter_app/pubspec.yaml`, and release workflows)
**License:** MIT
**Repo:** tv-viewer-app/tv_viewer (default branch: `master`)
**Distribution:** GitHub Releases (Windows zip, Linux x86_64, Android APK + AAB), Docker Hub (`asummoner/tvviewerapp:latest`), Google Play, F-Droid (MR open), APKPure (pending), Samsung (pending)
**Current release highlights:** Community Statistics page, timezone-based country detection, APKPure notify workflow
**Supabase project:** `cdtxpefohpwtusmqengu`

## Build, Test, and Lint Commands

### Desktop (Python)
```bash
pip install -r requirements.txt
python main.py                          # Run from source
python build.py                         # Build Windows EXE (PyInstaller)
python tests/validate_build.py --quick  # Pre-release validation
python -m pytest tests/ -q              # 299+ unit tests
```

### Web / Docker
```bash
python -m web.server                    # Run FastAPI dev server on :8765
docker build -t tv-viewer-web .         # Build container
docker compose up                       # Run with persistent /data volume
```

### Flutter (Android)
```bash
cd flutter_app
flutter pub get
flutter test                            # Dart unit tests
flutter build apk --release             # APK
flutter build appbundle --release       # AAB for Play Store
flutter analyze                         # Lint (release-blocking in CI)
```

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Desktop UI | CustomTkinter + ttkbootstrap | Fluent 2 dark theme |
| Desktop player | VLC via python-vlc | No hardware-accel flags (instability) |
| Mobile | Flutter 3.32 + Material 3 | `video_player` for video, `just_audio` + `audio_service` for radio/background playback |
| Web backend | FastAPI + uvicorn | Single-file `web/server.py` |
| Web UI | Vanilla JS + HLS.js | `web/static/index.html` (~1500 LoC) |
| Shared DB | Supabase (Postgres + PostgREST) | Anon key client-side, RLS-protected |
| Analytics | Supabase `analytics_events` table | Opt-in only |
| HTTP client | aiohttp (async) + requests | certifi CA bundle in Docker |
| EPG | XMLTV (gzipped) from public sources | `utils/epg.py` |
| Build | PyInstaller (desktop) / Flutter 3.32.0 / Docker buildx | Android uses Gradle 8.9, AGP 8.7.0, Kotlin 1.9.22 |
| CI/CD | 28 GitHub Actions workflows | Release gate, store distribution, Docker publish, analytics and Supabase ops |

## Architecture

### Desktop (Python)
- `core/channel_manager.py` — single source of truth for in-memory channel list;
  `__slots__` for memory; RLock-protected; URL→index map for O(1) lookups
- `core/repository.py` — async M3U fetcher (aiohttp), configurable sources
- `core/stream_checker.py` — background asyncio validation in daemon thread
- `ui/main_window.py` — Tk main loop; **all UI updates from background threads
  MUST use `root.after(0, ...)`** or segfault
- `ui/player_window.py` — VLC player; Space/F/M/Esc keyboard shortcuts

### Flutter (Mobile)
- `flutter_app/lib/services/` — `analytics_service.dart`, `shared_db_service.dart`,
  `audio_handler.dart` (background playback), `epg_service.dart`
- `flutter_app/lib/screens/` — `home_screen.dart`, `player_screen.dart`,
  `radio_screen.dart`, `statistics_screen.dart`, `help_support_screen.dart`
- Supabase credentials injected via `--dart-define=SUPABASE_URL=…` at build time
- Pinned HTTPS via `lib/utils/pinned_http_client.dart` for *.supabase.co

### Web / Docker
- `web/server.py` — FastAPI app. Endpoints: `/api/channels`, `/api/refresh`,
  `/api/health/report`, `/api/sources/{name}`, `/api/epg/{channel}`, `/api/statistics`, `/proxy`
  (SSRF-protected — blocks private IP ranges)
- `web/static/index.html` — SPA, localStorage state, HLS.js, EPG overlay
- Persistent state in `DATA_DIR` (`/data` volume in Docker): channels.json,
  favorites.json, epg_cache.json
- `utils/supabase_channels.py` — shared DB client: fetch, report broken,
  report working, and serve community statistics
- `utils/normalize.py` — **single source of truth** for category/country
  normalization (14 canonical categories). Ported by hand to Dart; risks drift.

### Shared Backend (Supabase)
- **Project ref:** `cdtxpefohpwtusmqengu`
- `channels` — `url_hash`, `name`, `urls[]`, `category`, `country`, `logo`,
  `media_type`, `source`, etc.
- `channel_status` — `url_hash`, `status` (working/broken), `last_checked`,
  `report_count`
- `analytics_events` — opt-in usage telemetry (sessions, plays, failures)
- `v_channels_with_sources` — view with `security_invoker=true` (RLS honors caller)
- `mv_daily_active_users` — materialized view for aggregated usage data
- `/api/statistics` reads pre-aggregated anonymous data only; clients never query analytics tables directly

## Critical Conventions

### Threading (Desktop)
**Never** modify Tk widgets from background threads → segfault. Always:
```python
self.root.after(0, lambda: self.label.configure(text="Updated"))
```
The `StreamChecker` runs an asyncio loop on a daemon thread; its callbacks fire
off-main and *must* schedule via `root.after`.

### Web — Untrusted Input → Supabase
`/api/health/report` is the only client→shared-DB write surface. Every value
forwarded to PostgREST **must** pass `_is_safe_channel_name` (rejects
`,()*:` and control chars — PostgREST filter metacharacters) and go through
aiohttp's `params=` encoding (never f-string into a query URL). The endpoint
is rate-limited (30/min/IP global, 5/min/IP promote-writes).

If you add a new write endpoint, replicate the pattern in
`_promote_source_supabase` (web/server.py): validate → aiohttp `params=` →
`Prefer: return=minimal`.

### Category Normalization
Use `utils.normalize.normalize_category(raw, channel_name)`. Don't hardcode
category lists. The 14 canonical set is in `CANONICAL_CATEGORIES`. If you add
a category, update both Python (`utils/normalize.py`) and Dart
(`flutter_app/lib/utils/normalize.dart`) — they share the same map structure.

### M3U Parsing Security
`utils/helpers.parse_m3u()` enforces: max 100k lines, max 10k chars/line,
string-type input check. Don't bypass for "trusted" sources — every public
M3U is untrusted.

### Logger
```python
from utils.logger import get_logger
logger = get_logger(__name__)
```
Rotating logs in `logs/`. `logger.debug` for hot paths, `logger.info` for
state changes, `logger.error(..., exc_info=True)` for unexpected.

### VLC (Desktop)
Multiple fallback init attempts (system VLC → PyInstaller bundle → minimal).
**Never** pass `--avcodec-hw=vaapi` or other hardware-accel flags — cross-platform
crashes. See git history for context.

### Channel Data Schema
```python
{
    'name': str,           # Display name
    'url': str,            # Primary stream URL (== urls[0])
    'urls': list[str],     # All known sources for this channel
    'url_hash': str,       # SHA-256 of primary url (Supabase key)
    'category': str,       # One of CANONICAL_CATEGORIES
    'country': str,        # ISO-2 or canonical name
    'logo': str,           # Logo URL (optional)
    'media_type': str,     # 'TV' / 'Radio' / None
    'status': str,         # 'working' / 'broken' / 'unchecked'
    'source': str,         # Repository origin
}
```

## File Organization (top-level)

```
tv_viewer_project/
├── main.py                # Desktop entry point
├── config.py              # APP_VERSION + tunables + Supabase env vars
├── build.py               # PyInstaller wrapper
├── requirements.txt
├── Dockerfile + docker-compose.yml
├── core/                  # Desktop channel/stream logic
├── ui/                    # Desktop Tk UI
├── utils/                 # Shared Python utilities
│   ├── normalize.py       # ★ Category/country canonicalization
│   ├── supabase_channels.py  # ★ Shared DB client
│   ├── epg.py             # XMLTV fetch + fuzzy match
│   ├── analytics.py       # Opt-in telemetry
│   └── logger.py / helpers.py / thumbnail.py
├── web/
│   ├── server.py          # ★ FastAPI app (single file)
│   └── static/index.html  # Web UI
├── flutter_app/lib/       # Flutter mobile sources
├── tests/                 # pytest (Python) — 299 tests
├── scripts/               # One-off ops scripts (Supabase setup, dashboards)
├── docs/                  # ARCHITECTURE, SUPPORT_GUIDE, PRIVACY (canonical)
├── .github/
│   ├── workflows/         # 28 CI workflows
│   └── copilot-instructions.md  # This file
└── .squad/                # Internal planning artifacts (not shipped)
```
└── android/                   # Android app (Kivy/Buildozer)
```

## Common Patterns

### Adding a new channel source
1. Add repository config to `channels_config.json` or `core/repository.py`
2. Ensure M3U format is compatible with `parse_m3u()`
3. Test with `python tests/test_core.py`

### Debugging threading issues
1. Check if UI updates use `root.after(0, ...)`
2. Verify locks are acquired for shared state
3. Enable verbose logging: `python main.py` (logs in `logs/`)

### Before creating a release
1. Update `APP_VERSION` in `config.py`
2. Update `CHANGELOG.md` with changes
3. Run `python tests/validate_build.py` (must pass)
4. Build executable: `python build.py`
5. Test on target platform

## Multi-Agent Collaboration

**Status:** ✅ 20 specialist agents configured for this project

### Available Agents

All agents can be invoked using `@agent-name` syntax in Copilot sessions.

**Core Development:** `@developer`, `@frontend-developer`, `@android-expert`  
**Quality & Testing:** `@qa-engineer`, `@qa-automation`  
**DevOps:** `@azure-cloud-platform`, `@github-operations`  
**Security:** `@security-reviewer`, `@soc-analyst`  
**Product & UX:** `@product-manager`, `@pm-manager`, `@ux-designer`, `@user-researcher`, `@end-user`  
**Support:** `@support-engineer`, `@technical-writer`  
**Business:** `@compete-expert`, `@gartner-analyst`, `@security-sales`  
**Management:** `@hr-manager`

Run `./test_agents.sh` to verify agent availability and view detailed capability matrix.

### Agent Consultation Guidelines

When working on this project, consult specialist agents for domain expertise:

**For Documentation Tasks:**
- Consult `developer` to validate technical accuracy
- Consult `qa-engineer` to review testing guidance
- Consult `azure-cloud-platform` to validate CI/CD sections
- Consult `pm-manager` for completeness review

**For Code Changes:**
- Consult `developer` for code review and architecture
- Consult `qa-engineer` for test strategy and coverage
- Consult `security-reviewer` for security implications

**For GitHub Workflows:**
- Consult `azure-cloud-platform` for CI/CD best practices
- Consult `developer` for build/test integration
- Consult `qa-automation` for automated testing

**For Releases:**
- Consult `product-manager` for release planning
- Consult `developer` for build verification
- Consult `qa-engineer` for release validation
- Consult `pm-manager` for final approval

### Quality Gate Requirements

Before finalizing major changes, ensure:
- [ ] Technical accuracy validated (by `developer` or manual review)
- [ ] Security patterns reviewed (if security-sensitive)
- [ ] CI/CD workflows validated (for workflow changes)
- [ ] Testing guidance validated (for test-related changes)
- [ ] Cross-functional alignment (for releases)

See session artifacts for detailed collaboration protocols and quality checklists.

## GitHub Workflow Management

### Repository Information
- **Repository:** tv-viewer-app/tv_viewer
- **Primary Branch:** master
- **Remote:** git@github.com:tv-viewer-app/tv_viewer.git

### Existing Workflows

**build-apk.yml** - Automated Flutter Android APK/AAB builds
- **Triggers:** Manual dispatch (tag releases flow through `build.yml` / `release.yml`)
- **Actions:** Builds signed APK + AAB, uploads artifacts, and can attach Android assets to GitHub Releases
- **Uses:** Flutter 3.32.0, Java 17, Gradle 8.9, AGP 8.7.0, Kotlin 1.9.22
- **Related store workflows:** `play-store-deploy.yml`, `fdroid-build.yml`, `apkpure-notify.yml`

### Creating New Workflows

When creating workflows, follow these patterns:

```yaml
name: Descriptive Workflow Name

on:
  push:
    branches: [ master ]
    paths:
      - 'relevant/path/**'  # Only trigger on relevant changes
  pull_request:
    branches: [ master ]
  workflow_dispatch:  # Allow manual triggering

jobs:
  job-name:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Run tests
      run: python tests/validate_build.py
```

### Checking Workflow Status

**Using GitHub CLI (gh):**
```bash
# List recent workflow runs
gh run list --limit 10

# View specific workflow runs
gh run list --workflow=build-apk.yml

# View details of failed run
gh run view <run-id>

# View logs of failed run
gh run view <run-id> --log-failed

# Re-run failed jobs
gh run rerun <run-id>
```

**Using GitHub MCP Server (via task tool):**
```bash
# List all workflows
task: github-mcp-server-actions_list with method=list_workflows

# Check recent runs
task: github-mcp-server-actions_list with method=list_workflow_runs

# Get failed job logs
task: github-mcp-server-get_job_logs with failed_only=true
```

### Common Workflow Fixes

**Build failures:**
1. Check dependency versions in requirements.txt or pubspec.yaml
2. Verify action versions (e.g., actions/checkout@v4)
3. Check Python/Node/Java version compatibility
4. Review logs: `gh run view <run-id> --log-failed`

**Workflow not triggering:**
1. Verify path filters match changed files
2. Check branch name (master vs main)
3. Look for `[skip ci]` in commit messages
4. Ensure workflow file is in `.github/workflows/`

**Permission errors:**
1. Add necessary permissions to workflow:
   ```yaml
   permissions:
     contents: write  # For pushing commits
     issues: write    # For creating issues
   ```

### Creating GitHub Releases

**Preparation checklist:**
1. ✅ Version bumped in `config.py` and `flutter_app/pubspec.yaml`
2. ✅ CHANGELOG.md updated with release notes
3. ✅ All tests passing: `python tests/validate_build.py`
4. ✅ CI workflows passing (check with `gh run list`)
5. ✅ Builds tested on target platforms

**Creating release with GitHub CLI:**
```bash
# Create tag and release
VERSION="v2.20.2"
gh release create $VERSION \
  --title "TV Viewer $VERSION" \
  --notes-file <(sed -n "/## \[$VERSION\]/,/## \[/p" CHANGELOG.md | head -n -1) \
  dist/TV_Viewer.exe \
  dist/TV_Viewer_v2.20.2_Android.apk

# Create pre-release (for testing)
gh release create $VERSION \
  --title "TV Viewer $VERSION (Pre-release)" \
  --notes "Testing release" \
  --prerelease \
  dist/TV_Viewer.exe

# Draft release (not published)
gh release create $VERSION \
  --title "TV Viewer $VERSION" \
  --notes "Draft release notes" \
  --draft \
  dist/TV_Viewer.exe
```

**Creating release with GitHub MCP Server:**
Not directly supported - use `gh` CLI or GitHub web interface.

### Updating GitHub on Project Changes

**Creating issues:**
```bash
# Create bug report
gh issue create \
  --title "Bug: VLC crashes on Linux" \
  --body "Description of the bug..." \
  --label bug,P1-High

# Create feature request
gh issue create \
  --title "Feature: Add channel search" \
  --body "User story..." \
  --label enhancement

# Link to milestone
gh issue create \
  --title "Task for v2.20.2" \
  --body "..." \
  --milestone "v2.20.2"
```

**Managing pull requests:**
```bash
# Create PR
gh pr create \
  --title "Fix: Resolve VLC initialization" \
  --body "Fixes #35..." \
  --base master

# Check PR status
gh pr status

# Merge PR (when CI passes)
gh pr merge <pr-number> --squash --delete-branch
```

**Updating repository info:**
```bash
# Set repository description
gh repo edit --description "Cross-platform IPTV streaming application"

# Add topics/tags
gh repo edit --add-topic iptv,python,vlc,streaming

# Enable/disable features
gh repo edit --enable-wiki=false --enable-projects=true
```

### Version Sync Strategy

This project has **separate versions per platform**:
- **Desktop (Python):** Version in `config.py` (currently 2.20.2)
- **Android (Flutter):** Version in `flutter_app/pubspec.yaml`

When releasing:
1. Update relevant platform version(s)
2. Document in CHANGELOG.md under appropriate version
3. Create the release tag from the aligned version, e.g. `v2.20.2`

### Workflow Templates for TV Viewer

**Desktop Build & Test Workflow:**
```yaml
name: Desktop Build & Test

on:
  push:
    branches: [ master ]
    paths-ignore:
      - 'flutter_app/**'
      - 'android/**'
      - 'docs/**'
  pull_request:
    branches: [ master ]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y vlc
        pip install -r requirements.txt
    - name: Run validation
      run: python tests/validate_build.py
    - name: Run tests
      run: python -m pytest tests/ -v

  build-windows:
    runs-on: windows-latest
    needs: test
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Build executable
      run: python build.py
    - name: Upload artifact
      uses: actions/upload-artifact@v4
      with:
        name: tv-viewer-windows
        path: dist/TV_Viewer.exe
```

**Release Creation Workflow:**
```yaml
name: Create Release

See `.github/workflows/WORKFLOWS-README.md` for full documentation.
```

## CI/CD Pipeline Summary

TV Viewer currently uses **28 GitHub Actions workflows** spanning CI, releases, store distribution, Docker publishing, Supabase operations, analytics, and community automation.

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push, PR | Core Python/Web validation |
| `build.yml` | Tags, manual | Canonical release build pipeline |
| `build-apk.yml` | Manual | Ad-hoc signed Android APK/AAB builds |
| `release-gate.yml` | Tags | Release readiness gates |
| `release.yml` / `auto-release.yml` | Tags | GitHub Release publication |
| `docker-publish.yml` | Tags, manual | Push `asummoner/tvviewerapp` with `latest` + version tags |
| `play-store-deploy.yml` | Release, manual | Google Play deployment |
| `fdroid-build.yml` | Tags, manual | F-Droid-compatible unsigned APK |
| `apkpure-notify.yml` | Release/tag | Notify APKPure crawler after release publication |
| `supabase-*.yml` + analytics workflows | Schedule, manual | Monitor backend health and aggregated community analytics |

### Release Process
1. Update `APP_VERSION` in `config.py` + `flutter_app/pubspec.yaml`
2. Update `CHANGELOG.md`
3. Tag: `git tag v2.20.2 && git push origin v2.20.2`
4. Release Gate validates → Build Release publishes all 3 platforms

### What Blocks Releases
- ❌ Test failures (Ubuntu 22.04/24.04 × Python 3.10/3.11/3.12)
- ❌ HIGH severity Bandit issues
- ❌ `shell=True` in production code
- ❌ Missing CHANGELOG entry for version
- ❌ Any platform build failure (Ubuntu + Windows + Android)

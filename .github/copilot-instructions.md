# TV Viewer Project - Copilot Instructions

## Project Overview
Cross-platform IPTV streaming application built with Python and CustomTkinter. Discovers, validates, and plays live TV streams from public IPTV repositories with Windows 11 Fluent Design UI.

**Version:** 1.8.2  
**Platforms:** Windows, Linux, macOS, Android

## Build, Test, and Lint Commands

### Build
```bash
# Build Windows executable (current platform)
python build.py

# Build with specific options
python build.py --onefile   # Single file executable (default)
python build.py --onedir    # Directory-based build
python build.py --debug     # With console for debugging
python build.py --clean     # Clean build artifacts

# Android APK
cd android && buildozer android debug
```

### Test
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
pytest tests/test_core.py -v

# Run post-build validation (critical before releases)
python tests/validate_build.py
python tests/validate_build.py --verbose  # Detailed output
python tests/validate_build.py --quick    # Skip slow tests
```

### Run from Source
```bash
pip install -r requirements.txt
python main.py
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| UI Framework | CustomTkinter | Windows 11 Fluent Design UI |
| Video Player | VLC (python-vlc) | Hardware-accelerated playback |
| HTTP Client | aiohttp + requests | Async network operations |
| Concurrency | asyncio + threading | Non-blocking operations |
| Data Storage | JSON files | Channel cache and config |
| Build | PyInstaller | Windows executable |
| CI/CD | GitHub Actions | Automated Android builds |

## Architecture

### Component Responsibilities

**ChannelManager** (`core/channel_manager.py`)
- Single source of truth for channel data
- Loads/saves channels, organizes by category/country
- Memory-optimized with `__slots__` (40% memory savings)
- Thread-safe with RLock
- URL-to-index mapping for O(1) lookups

**RepositoryHandler** (`core/repository.py`)
- Fetches M3U playlists from IPTV repositories
- Async HTTP requests with aiohttp
- Configurable in `channels_config.json`

**StreamChecker** (`core/stream_checker.py`)
- Background stream validation in daemon thread
- Runs asyncio event loop in separate thread
- Low thread priority to avoid UI blocking
- Concurrent HTTP validation

**MainWindow** (`ui/main_window.py`)
- Main UI with channel list
- Tkinter event loop on main thread
- **CRITICAL:** All UI updates must use `root.after(0, ...)` when called from background threads

**PlayerWindow** (`ui/player_window.py`)
- Separate window for video playback
- VLC integration with python-vlc
- Keyboard shortcuts: Space (pause), F (fullscreen), M (mute), Esc (exit fullscreen)

### Data Flow
```
RepositoryHandler → ChannelManager → StreamChecker
                         ↓
                    MainWindow
                         ↓
                   PlayerWindow
```

## Critical Conventions

### Threading Rules (CRITICAL - Violating causes segfaults)

**NEVER** modify tkinter UI directly from background threads. Always schedule updates on main thread:

```python
# ✅ CORRECT - Schedule UI update on main thread
self.root.after(0, lambda: self.label.configure(text="Updated"))

# ❌ WRONG - Direct modification from background thread causes crash
self.label.configure(text="Updated")
```

**Background thread callbacks** must use `root.after(0, ...)`:
```python
def on_channel_validated(channel, current, total):
    # This callback is called from StreamChecker's background thread
    self.root.after(0, lambda: self._safe_update_ui(channel, current, total))
```

See `CHANGELOG.md` - Issue #32 for historical context on this critical fix.

### Memory Optimization

Use `__slots__` for classes with many instances:
```python
class ChannelManager:
    __slots__ = ('channels', 'categories', 'countries', ...)
```

Channels are stored once; categories/countries contain shared references (not copies).

### UI Design System

Use `FluentColors` from `ui/constants.py` for Windows 11 Fluent Design consistency:
- `FluentColors.ACCENT` - Primary blue (#0078D4)
- `FluentColors.BG_MICA`, `BG_ACRYLIC`, `BG_CARD` - Background layers
- `FluentColors.TEXT_PRIMARY`, `TEXT_SECONDARY` - Text colors
- `FluentColors.SUCCESS`, `ERROR`, `WARNING` - Status colors

### M3U Parsing Security

The `parse_m3u()` function in `utils/helpers.py` includes security limits:
- Max 100k lines per playlist (prevent DoS)
- Max 10k chars per line (prevent memory attacks)
- Input validation for string type

### Configuration

All tunable parameters in `config.py`:
- `MAX_CONCURRENT_CHECKS` - Balance CPU/bandwidth vs speed
- `STREAM_CHECK_TIMEOUT` - Balance speed vs reliability
- `REQUEST_TIMEOUT` - Network timeout for repositories

### Logger Usage

Use module-level logger from `utils/logger`:
```python
from utils.logger import get_logger
logger = get_logger(__name__)

logger.info("Starting channel scan")
logger.error("VLC initialization failed", exc_info=True)
```

Logs saved to `logs/` directory with rotation.

### VLC Initialization

VLC initialization has multiple fallback attempts (see Issue #35):
1. Standard system VLC
2. PyInstaller bundle with environment vars
3. Minimal configuration fallback

**DO NOT** use hardware acceleration flags like `--avcodec-hw=vaapi` (causes instability across platforms).

### Channel Data Structure

Channels are dicts with standard keys:
```python
{
    'name': str,           # Display name
    'url': str,            # Stream URL
    'category': str,       # e.g., "News", "Sports"
    'country': str,        # ISO country code or name
    'logo': str,           # Logo URL (optional)
    'media_type': str,     # 'TV', 'Radio', or None
    'status': str,         # 'working', 'offline', 'unchecked'
    'minimum_age': int,    # Age restriction (optional)
}
```

## File Organization

```
tv_viewer/
├── main.py                    # Entry point with check_requirements()
├── config.py                  # All configurable parameters
├── channels.json              # Cached channels (auto-generated)
├── channels_config.json       # User-configured repositories
├── core/
│   ├── channel_manager.py     # Central channel coordinator
│   ├── repository.py          # Repository fetching (aiohttp)
│   └── stream_checker.py      # Background validation (asyncio)
├── ui/
│   ├── constants.py           # FluentColors and design tokens
│   ├── main_window.py         # Main window (must use root.after)
│   ├── player_window.py       # Video player window
│   └── scan_animation.py      # Loading animation
├── utils/
│   ├── helpers.py             # M3U parsing, JSON I/O
│   ├── logger.py              # Logging setup
│   ├── thumbnail.py           # Thumbnail capture/cache
│   └── channel_lookup.py      # Channel metadata enrichment
├── tests/
│   ├── test_core.py           # Unit tests (pytest)
│   └── validate_build.py      # Pre-release validation
├── docs/
│   ├── ARCHITECTURE.md        # Detailed architecture
│   ├── SUPPORT_GUIDE.md       # Troubleshooting
│   └── *.md                   # Other documentation
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

**android-build.yml** - Automated Flutter Android APK builds
- **Triggers:** Push to `master` (only `flutter_app/**` changes), manual dispatch
- **Actions:** Builds APK, extracts version from pubspec.yaml, uploads artifact, commits to `dist/android/`
- **Uses:** Flutter 3.19.0, Java 17, actions/checkout@v4, actions/upload-artifact@v4
- **Key pattern:** `[skip ci]` in commit message prevents recursive builds

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
gh run list --workflow=android-build.yml

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
VERSION="v1.8.2"
gh release create $VERSION \
  --title "TV Viewer $VERSION" \
  --notes-file <(sed -n "/## \[$VERSION\]/,/## \[/p" CHANGELOG.md | head -n -1) \
  dist/TV_Viewer.exe \
  dist/android/TV_Viewer_v1.8.2.apk

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
  --title "Task for v1.9.0" \
  --body "..." \
  --milestone "v1.9.0"
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
- **Desktop (Python):** Version in `config.py` (currently 1.8.2)
- **Android (Flutter):** Version in `flutter_app/pubspec.yaml`

When releasing:
1. Update relevant platform version(s)
2. Document in CHANGELOG.md under appropriate version
3. Create release tag with platform suffix if needed: `v1.8.2` (desktop), `v1.7.0-android`

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

| Workflow | Trigger | Blocks? |
|----------|---------|---------|
| `test.yml` | Push, PR | No |
| `pr-validation.yml` | PR | **Yes** (lint, security, tests) |
| `security-gate.yml` | Tags, PR | **Yes** (HIGH severity) |
| `release-gate.yml` | Tags (v*) | **Yes** (5 gates) |
| `build-release.yml` | After gate | Creates GitHub Release |
| `cve-scanner.yml` | Daily 6 AM | Creates issue on findings |

### Release Process
1. Update `APP_VERSION` in `config.py` + `flutter_app/pubspec.yaml`
2. Update `CHANGELOG.md`
3. Tag: `git tag v1.9.0 && git push origin v1.9.0`
4. Release Gate validates → Build Release publishes all 3 platforms

### What Blocks Releases
- ❌ Test failures (Ubuntu 22.04/24.04 × Python 3.10/3.11/3.12)
- ❌ HIGH severity Bandit issues
- ❌ `shell=True` in production code
- ❌ Missing CHANGELOG entry for version
- ❌ Any platform build failure (Ubuntu + Windows + Android)

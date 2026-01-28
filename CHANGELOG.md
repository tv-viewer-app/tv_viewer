# Changelog

All notable changes to TV Viewer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.5.0] - 2026-01-28

### Added (Flutter Android App)
- **Cast Button** - Cast button in player with dialog for external player casting
- **Resolution/Bitrate Display** - Shows stream quality info in channel list and player
- **Country Filter** - Dropdown to filter channels by country
- **Radio Station Support** - Media type filter (TV/Radio) with auto-detection
- **Category Dropdown** - Replaced horizontal chips with dropdown selector

### Fixed (Flutter Android App)
- **External App Launch** - Added Android intent queries for VLC, MX Player with proper fallback
- **Category Normalization** - Categories with semicolons now consolidated to single topic
- **Memory Leak** - VideoPlayerController listener now properly removed on dispose
- **Memory Leak** - Controller properly disposed on retry
- **Race Condition** - Batch state updates in channel validation to prevent UI inconsistencies

### Changed (Flutter Android App)
- Updated AndroidManifest.xml with queries for external video players
- Improved player UI with show/hide controls on tap
- Added helpful hints in player overlay

## [1.4.4] - 2026-01-28

### Added
- **Crash Reporter** - Automatic crash reporting via GitHub Issues
  - Opens browser to create issue with crash details
  - No personal data collected (paths sanitized)
  - User prompted before reporting
  - Categorizes errors (network, UI, filesystem, etc.)

### Fixed
- **Scan Animation** - Restored pixel art Earth/satellite animation during scan
  - Light theme compatible colors
  - Optimized to 200ms frame rate for lower CPU

## [1.4.3] - 2026-01-28

### Performance
- **Scan CPU Usage** - Reduced concurrent checks from 10 to 5, added configurable delays
- **Scan Memory** - Smaller batch size (200 vs 500), more aggressive GC between batches
- **UI Updates** - Throttled progress updates (every 100-500 channels vs 50)
- **Connection Pooling** - Reduced per-host limit (2 vs 3), extended DNS cache (10 min)
- **Timeouts** - Faster stream timeout (5s vs 8s), faster connection timeout (3s vs 5s)

### Changed
- Added configurable scan parameters: `SCAN_BATCH_SIZE`, `SCAN_REQUEST_DELAY`, `SCAN_SKIP_MINUTES`
- Background thread uses lower priority for minimal UI impact

## [1.4.2] - 2026-01-28

### Fixed
- **VLC Button** - Fixed AttributeError when clicking VLC button (stop_playback → stop)
- **Player Button Visibility** - Added dark text color and borders to player control buttons for visibility on light background

## [1.4.1] - 2026-01-27

### Security
- **SSL/TLS Error Handling** - SSL errors now properly logged and marked as failed (was silently ignored)
- **PrivateBin** - Removed plaintext deletion token storage for security
- **Exception Handling** - Replaced bare except blocks with specific exception types throughout

### Performance
- **Channel Lookup** - O(1) name-to-channel index for instant lookups (was O(n))
- **Adult Filter** - Pre-compiled keyword set with early-exit matching
- **UI Updates** - Optimized batch updates to reduce screen refreshes

### Code Quality
- **Logging** - Replaced all print() statements with structured logging
- **Error Handling** - Specific exception types instead of generic Exception
- **Documentation** - Added missing docstrings to key methods
- Removed unsafe `exec()` helper scripts (organize_project.py, _create_prd.py)

## [1.4.0] - 2026-01-27

### Added
- **Export M3U** - Export all working channels as M3U playlist file
- **PrivateBin Integration** - Share scan results with other users
  - Upload scan results to privatebin.info after validation
  - On startup, check for recent shared scan (<4 hours old)
  - Only scan non-working channels if shared results available
  - Toggle in sidebar to enable/disable sharing
- **Windows 11 Light Theme** - Complete UI redesign with light Fluent colors

### Changed
- **VLC Button** - Now closes embedded player when opening external VLC
- **UI Theme** - Switched from dark to light Windows 11 Fluent Design
- **About Dialog** - Updated text to reference Windows 11 Fluent Design

### Fixed
- **Double-click on filtered channels** - Now correctly finds channel from displayed list
- **Thumbnail capture** - Improved VLC snapshot with retries and better timing
- **Search in filtered results** - Channel lookup now searches displayed channels first

## [1.3.0] - 2026-01-27

### Added
- **Windows EXE** - Compiled standalone executable (24 MB)
- **Android App** - Kivy-based mobile app for Samsung Galaxy S24 Ultra
  - Browse 10,000+ IPTV channels
  - Search and category filters
  - Plays streams via VLC for Android
  - Dark theme optimized for OLED
- **GitHub Actions** - Automated Android APK build workflow
- `android/` directory with full mobile app source
- `android/buildozer.spec` for APK configuration

### Build Outputs
- Windows: `dist/TV_Viewer.exe`
- Android: Build via GitHub Actions or `buildozer android debug`

## [1.2.0] - 2026-01-27

### Added
- **Automated Build Validation** (`tests/validate_build.py`)
  - Comprehensive post-build validation script
  - Checks all imports, config, modules, and dependencies
  - Run before every release to ensure stability
- **Unit Tests** (`tests/test_core.py`)
  - Tests for M3U parsing, logger, config, constants
  - Tests for channel manager, stream checker, repository handler
- **Tooltips** for all player controls
  - Keyboard shortcuts shown in tooltips (Space, F, M, ESC)
  - Improved discoverability for new users
- **Tooltip utility module** (`ui/tooltip.py`)

### Changed
- **VLC Error Dialog** - Now includes "Download VLC" button linking to videolan.org
- **Player Controls** - Added tooltips: "Play/Pause (Space)", "Fullscreen (F)", etc.

### Fixed
- Build validation now correctly checks `load_cached_channels` method

## [1.1.0] - 2026-01-27

### Added
- Structured logging system with rotating log files (`utils/logger.py`)
- "No results" message when channel list is empty after filtering
- Status icon legend in sidebar (✓ Working ✗ Failed ◌ Checking)
- Volume percentage display in player controls
- VLC error dialog with retry option
- Startup requirements check to verify all dependencies are installed

### Changed
- **UI Redesign**: Replaced Material Design with Windows 11 Fluent Design
  - New color palette with Windows 11 accent colors
  - Updated typography and spacing constants
  - Modern button and control styling
  - Improved contrast for accessibility (WCAG 4.5:1)

### Fixed
- **Security**: Enabled SSL/TLS certificate verification for all HTTP requests
- **Security**: Fixed command injection vulnerability in external VLC launch
- **Security**: Added URL scheme validation before subprocess execution
- Replaced bare `except:` statements with specific exception types
- Improved error messages with actionable recovery steps

### Security
- SSL verification now enabled in `repository.py` and `stream_checker.py`
- URL validation added before launching external applications
- Removed unsafe `os.startfile()` call

## [1.0.0] - 2026-01-27

### Added
- Initial release
- IPTV channel browser with 80+ repository sources
- Background stream validation
- Embedded VLC player with hardware acceleration
- Google Cast support
- Channel categorization by category, country, language
- Adult content filtering
- Thumbnail previews
- Search and filter functionality
- Dark theme UI

# Changelog

All notable changes to TV Viewer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.1.2] - 2026-03-04

### Added
- **Usage telemetry** — anonymous, privacy-first telemetry to Supabase: tracks app launches, channel plays/failures, feature usage, and scan completions. No channel names or URLs sent (only hashed). Random device UUID, country from locale, rate-limited (max 500 events/type/session). Fire-and-forget — never blocks UI
- **Flutter analytics wiring** — trackChannelPlay, trackChannelFail, trackFeature('map_open') wired into home_screen, player_screen, and map_screen
- **SSRF protection** — stream URL validation now blocks private/loopback/link-local/reserved IP addresses via `ipaddress` module

### Fixed
- **Supabase always-on** — shared_db.py now imports URL/key from config.py instead of empty env vars. Crowd-sourced health sharing actually works for all clients now
- **Event loop leaks** — fixed asyncio event loops not closed in player_window.py and channel_manager.py
- **Map pause safety** — scanning resumes on map close even if init fails (try/finally)
- **FMStream HTTPS** — default URL changed from http to https
- **Channel name privacy** — removed channel_name from analytics payloads in health reporting

### Changed
- **Scan 6x faster** — MAX_CONCURRENT_CHECKS 10→30, SCAN_REQUEST_DELAY 0.1→0.005 (was adding 30min of pure sleep for 18K channels)
- **TCP connection reuse** — aiohttp force_close=False with keepalive_timeout=30 enables 2-3x speedup for CDN hosts
- **Always share results** — removed "Share scan results" toggle; scan results stream to Supabase per-batch automatically
- **Removed PrivateBin** — all dead PrivateBin code removed; Supabase is the only backend
- **Removed .env file** — hardcoded defaults in config.py eliminate env-var misconfiguration

### Security
- Private IP blocking prevents SSRF attacks via crafted M3U playlists
- HTTPS enforced for FMStream radio directory
- No PII in telemetry: no channel names, no URLs, no user identifiers

## [2.1.1] - 2026-03-03

### Added
- **Smart scan — primary URL only** — scanner now checks only the last-known-working URL per channel during the main pass; alternative URLs are verified in a separate background phase. Main scan is 2-5x faster for multi-URL channels
- **Dynamic scan priority queue** — channels are scanned in priority order: recently played → user's active country → never-scanned → revalidation → known-failed
- **Country-based priority boost** — selecting a country group or playing a channel automatically boosts that country's channels to the top of the scan queue (both Windows and Android)
- **User interaction drives scan order** — playing a channel records its URL and country for priority scanning in the next cycle
- **Alternative URL background pass** — after the main scan, channels whose primary URL failed are re-checked against their alternative URLs; resolved channels are marked working with updated workingUrlIndex
- **Channel name consolidation** — channels with similar names (e.g. "Reshet 13 720p", "Reshet 13 alt", "Reshet 13") are automatically merged into a single entry with multiple stream URLs (both Windows and Android)
- **100FM digital sub-channels on Android** — added 19 100FM radio stations (Hip Hop, Dance, Trance, Club, Top 40, 90s, 80s, etc.) to Flutter custom channels

### Fixed
- **Missing radio stations on Android** — Flutter was not loading channels_config.json; 100FM sub-channels and other custom radio stations now included in hardcoded custom channel list
- **Ynet Live URL on Android** — updated to new CDN endpoint (was still using dead ynet-pic1 URL)

### Changed
- Stream checker only tests one URL per channel during main scan (was testing all URLs sequentially)
- Flutter scan batches increased delay 50ms→100ms for stability
- Scan priority logged to help debug channel ordering

## [2.1.0] - 2026-03-02

### Added
- **Multi-URL channel fallback** — channels can now have multiple stream URLs. If the primary URL fails, the player automatically tries the next URL in the list (both Windows and Android)
- **Channel health on play/fail** — playing a channel marks it as working; playback failure marks it as failed and triggers fallback to next URL
- **Crowdsourced health reporting** — `track_channel_health()` reports play success/failure to Supabase for future aggregation across all users
- **Supabase keep-alive** — GitHub Actions cron workflow pings Supabase every 5 days to prevent free-tier inactivity pause
- **20 100FM digital sub-channels** — Hip Hop, Dance, Trance, Club, Top 40, 90s, 80s, Workout, Chillout, Retro, Latin, Jazz, Deep, Classic Rock, TikTok, DJ Set, K-Pop, Mizrachit, and more

### Fixed
- **Japan channels** — removed 55 dead JP-PrimeHome URLs (CDN decommissioned), marked 46 geo-blocked willfonk.com channels as not working
- **Ynet Live** — updated stream URL from dead ynet-pic1 CDN to new hls-video-ynet endpoint
- **Map pin labels** — channel names now show under pins when deeply zoomed in (Android)
- **Map pin colors** — pins are green (working) or red (not working) (Android)
- **Map stats bar position** — stats bar positioned above Android navigation bar using MediaQuery padding

### Changed
- **Scan speed reduced** — concurrent checks 30→10, batch size 200→100, request delay 0.005→0.1s, added 0.5s batch delay between batches (less aggressive, avoids CDN rate limits)
- Stream checker iterates all URLs per channel, sets working index on first success
- Python channel_manager migrates old single-URL channels to multi-URL format automatically

## [2.0.3] - 2026-03-02

### Added
- **World Map micro-interactions** — animated pulsing country bubbles, smooth camera fly-to, count-up stat badges, health bars, hover effects, filter chip animations (Windows + Android)
- **Live country search** in Windows map toolbar with debounced input
- **Stats overlay bar** on Flutter map showing countries/channels/working counts with animated counters

### Fixed
- **Map performance (Windows)** — debounced search prevents marker rebuild on every keystroke, lazy-load channel rows in batches of 30 for fast popup opening
- **Map performance (Android)** — eliminated unnecessary `setState` on every zoom change (now only rebuilds on cluster/pin threshold crossing), added tile keepBuffer for smoother panning, reduced pulse animation overhead
- **Onboarding tooltip off-screen** — scan button tooltip now appears below the AppBar (was rendering above the screen), added safety clamping so no tooltip can ever go off-screen
- **Supabase analytics not sending data (Windows)** — Python analytics module used empty env var defaults instead of embedded keys from config.py; now falls back to config.py values. Wired analytics init and flush into main.py entry point
- **Supabase analytics flush on exit** — atexit handler now flushes queued analytics events before app closes

### Changed
- Fluent Design dark theme applied consistently to Windows map window (toolbar, popups, channel rows)
- Country popup uses animated health bar and staggered channel loading
- Flutter map uses `NetworkTileProvider` with `keepBuffer: 8` for smoother tile caching
- Filter toggles show visual active state (color + checkmark) on both platforms

## [2.0.2] - 2026-03-01

### Added
- **🗺️ World Map view** — Zoomable OpenStreetMap showing TV stream sources by country. Country bubbles at low zoom with channel count and health color (green/orange/red). Individual channel pins at high zoom. Tap/click to see channel details and play. Available on both Windows (tkintermapview) and Android (flutter_map)
- **Map filters** — Toggle "Favorites only" and "Hide offline" directly on the map to focus on your channels
- **Supabase analytics embedded** — Crash reporting and anonymous usage analytics now active out-of-the-box (no manual configuration needed). Uses public anon key protected by RLS write-only policies
- **Crash reporting wired to error zones** — Flutter framework errors and uncaught async exceptions automatically reported to Supabase analytics
- **Analytics opt-out** — Users can disable anonymous analytics via `analytics.setEnabled(false)` (GDPR compliance)
- **Error message sanitization** — Crash reports strip file paths, URLs, and tokens before transmission (privacy hardening)

### Changed
- **Supabase schema fixes** — `analytics_events` CHECK constraint now matches actual event types (`app_launch` not `app_open`); added UPDATE RLS policy for `channel_status` upserts
- **favorites_service.dart** — Replaced all `print()` calls with proper `logger.warning()` for production logging

### Security
- [H-001] Fixed event_type mismatch causing silent data loss for app_launch events
- [H-002] Added missing RLS UPDATE policy for channel_status upserts
- [M-001] Sanitized error messages before sending to analytics (strips paths, URLs, tokens)
- [M-002] Added analytics opt-out mechanism for GDPR compliance
- [M-004] Removed Supabase response bodies from warning logs (prevents schema leakage)

## [2.0.1] - 2026-03-01

### Added
- **Channel info (i) icon** — Tap the info icon next to any channel to see a 1-sentence description. 218 channels pre-loaded covering Israeli TV/Radio, international news, sports, entertainment, kids, and more
- **[#20] EPG/Schedule info (e) icon** — Electronic Program Guide with current and next show info. Tap the schedule icon to see program details with progress bars. Category-aware program generation (News, Sports, Entertainment, etc.)
- **[#14] Repository pattern** — Data access layer extracted into ChannelRepository and PlaylistRepository interfaces with concrete implementations. Clean separation of business and data logic
- **[#15] Dependency injection** — Activated get_it DI container in Flutter app. Services registered via setupServiceLocator() with graceful fallback if DI unavailable
- **Analytics dashboard CLI** — New `scripts/analytics_dashboard.py` for monitoring usage stats, crash reports, top channels, and scan statistics from Supabase
- **Language normalization** — ISO language codes (heb, eng, spa, etc.) normalized to full names in Android language filter. 50+ language mappings

### Changed
- **Windows Settings dialog** — Config button now opens a proper GUI dialog with stream settings, repository management, and display preferences (replaces raw JSON editing)
- **Windows Favorites** — Star column in treeview with click-to-toggle, right-click context menu, and "Favorites only" sidebar filter
- **Android Cast button** — Replaced guidance popup with action sheet: "Open in Media Player", "Open in External App", "Copy Stream URL"
- **Category/Country filter separation** — Categories dropdown no longer shows country names; dedicated country filter preserved

### Fixed
- Dart raw string escaping in fmstream_service.dart (9 RegExp patterns)
- `logger.debug()` argument count in fmstream_service.dart
- Android build push conflicts with retry loop

## [2.0.0] - 2026-03-01

### Added
- **[#31] Shared channel health database** — Supabase-powered cross-platform channel status sync. Clients share validation results anonymously (URL hashing with SHA256). Fetch cached results on startup to skip re-scanning working channels. Both Python and Flutter
- **[#45] Working channels filter** — New status filter dropdown (Working/Failed/Unchecked) on Android. Filter to show only validated working channels, hiding offline/untested streams
- **[#24] Anonymous analytics** — Lightweight Supabase-backed analytics (no Firebase). Tracks app launches, stream failures, scan stats, and crashes anonymously. Privacy-first: URL hashing, no PII, random UUID per install. Batched with 30s flush interval
- **[#32] FMStream.org radio integration** — FMStream radio directory parsed and merged into channel list with deduplication. Multi-strategy HTML parsing with bitrate-aware quality selection
- **Cast dialog improvements** — Cast button now shows proper cast guidance with "Copy Stream URL" instead of auto-redirecting to VLC
- **External player fix** — Simplified external player launch: tries direct URL first (Android app chooser), then VLC scheme fallback. More reliable than intent-based approach
- **Category/Country filter separation** — Category dropdown now only shows content categories (News, Sports, etc.), no longer polluted with country names from M3U group-title
- **Dedicated Favorites toggle** — Star/FilterChip button to show only favorited channels, separate from category dropdown

### Changed
- Version bump to 2.0.0 across all platforms (Python + Flutter)
- Supabase sync integrated into stream validation pipeline (fetch cached → validate → upload results)
- FMStream radio stations auto-fetched alongside M3U repositories

## [1.9.2] - 2026-03-01

### Security Fixes
- **[SEC-001] Remove JWT tokens from source** — Replaced i24NEWS Brightcove JWT URLs with clean endpoints; i24NEWS channels still available via IPTV repositories
- **[SEC-003] Supabase credentials to env vars** — Moved hardcoded placeholder credentials to `SUPABASE_URL`/`SUPABASE_ANON_KEY` environment variables (Python + Flutter)
- **[SEC-004] Disable PrivateBin unencrypted upload** — Upload function disabled until AES-256-GCM encryption is implemented per PrivateBin v2 protocol
- **[SEC-005] Replace os.startfile** — Config file now opens with `notepad.exe` (Windows) / `open -t` (macOS) instead of untrusted default handler
- **[SEC-007] Restrict Android cleartext traffic** — `network_security_config.xml` now only allows HTTP for known streaming CDN domains instead of app-wide cleartext
- **[SEC-010] M3U content size limit** — Flutter M3U fetcher now rejects responses exceeding 50MB to prevent OOM on Android devices

### Fixed
- **[#41] Offline/connectivity handling** — App now checks connectivity before network operations, shows offline banner with retry button, falls back to cached channels when offline, and prevents validation when disconnected
- **Release Gate test failures** — Added `pytest-asyncio` to CI test dependencies; all 6 matrix test jobs now pass
- **SEC-002 verified** — URL scheme validation before VLC subprocess launch was already implemented in v1.9.1

### Added
- **KAN 4K channel** — Added `kan11_4k` CDN path for KAN 11 4K UHD stream (Windows + Android)

## [1.9.1] - 2026-03-01

### Fixed (P0-Critical)
- **Windows app crash on startup** — Added ttkbootstrap, PIL, PIL.ImageTk to PyInstaller hidden imports; removed PIL.ImageTk from excludes (ttkbootstrap depends on Pillow)
- **Dark theme unreadable text** — Switched from `FluentColors` (light palette) to `FluentColorsDark` with ttkbootstrap "darkly" theme
- **Country mis-assignment** — Rewrote `_organize_channels()` to use intelligent name/URL lookup instead of trusting M3U `tvg-country` tags (which indicate broadcast availability, not origin)

### Fixed (P1-High)  
- **Israeli channels not working** — Discovered correct CDN paths on `kancdn.medonecdn.net` by scraping kan.org.il live page; all 13 KAN channels now work globally
- **Android app shows version 1.5.0** — Replaced hardcoded version string in 6 Dart files with 1.9.1
- **Android app missing channels** — Expanded from 2 to 17 IPTV repositories; added 24→33 custom Israeli channels with verified CDN URLs
- **Android Radio filter not working** — Custom channels were defaulting to `mediaType: 'TV'`; now correctly set to `'Radio'` when group is Radio
- **Android Language filter empty** — Custom channels were missing `language` field; now all include Hebrew/Arabic/English/French as appropriate
- **CVE Scanner workflow failure** — Fixed `pip-audit --output` flag (only creates file when vulns exist); switched to `pip-audit | tee` pattern
- **Security Gate workflow failure** — Added `usedforsecurity=False` to MD5 hash in thumbnail.py (cache key, not security); removed tag-push trigger
- **Android build 403 push error** — Added `permissions: contents: write` to workflow
- **Flutter compilation errors** — Fixed PlatformException, connectivity_plus List API, floating 2.0 API changes
- **R8/ProGuard minification error** — Added `-dontwarn com.google.android.play.core.**`

### Added
- **59 custom Israeli channels** in `channels_config.json` — KAN TV (11, Kids, Subtitled, Makan 33), Reshet 13 (6 variants), Channel 14, i24NEWS (4 languages), Knesset, Ynet, Hala TV, Kabbalah TV, 20+ radio stations
- **33 custom Israeli channels** in Android app — 19 TV + 14 Radio (Kan Bet, Gimel, 88, Tarbut, Moreshet, Kol Hamuzika, Reka, Radio Makan, Galgalatz, Galei Zahal, 100FM, 103FM)
- **Concurrent repository fetching** — `asyncio.gather` with `Semaphore(10)` replaces sequential fetching
- **Search debounce** (300ms) — Prevents UI lag during rapid typing
- **Treeview bulk insert** — Hide widget during mass insert, pack after
- **Scan polling timer** — Replaces per-channel callback with periodic UI refresh

### Changed
- Window size increased from 900×600 to 1200×700
- Channel list font increased from 12pt to 14pt
- Sidebar widened from 300px to 340px
- Version bumped to 1.9.1 (desktop) / 1.9.1+3 (Android)
- `MAX_CONCURRENT_CHECKS` increased from 20 to 30
- `SCAN_REQUEST_DELAY` decreased from 0.02 to 0.005

### Israeli Channel CDN Discovery
KAN channels on `kancdn.medonecdn.net` use different path names than `*.media.kan.org.il`:
| Channel | CDN Path |
|---------|----------|
| Kan 11 | `kan11` |
| Kan Kids | `kan_edu` |
| Kan 11 Subtitled | `kan11_subs` |
| Makan 33 | `makan` |
| Radio stations | `radio/kan_88`, `radio/kan_tarbut`, etc. |

### Closed Issues
- #26, #39, #40, #42, #43, #44, #47 — Android bugs verified fixed and closed

## [1.9.0] - 2026-02-24

### Fixed (P0-Critical)
- **Segfault crash on startup** — Removed `update_idletasks()` from bulk widget creation loop
  in `_update_groups()`. Buttons now created in batches of 30 via `after()` callbacks to avoid
  tkinter C-level reentrancy crash.

### Fixed (P2-Medium)
- **Scan animation 0% overlay** ([#30](https://github.com/arielsaghiv/tv_viewer/issues/30))
  - Percentage text only shown when scan is active (total > 0), no longer overlays Earth animation
- **Channel deduplication on cache load** ([#29](https://github.com/arielsaghiv/tv_viewer/issues/29))
  - Added URL-based deduplication when loading cached channels from channels.json
  - Logs count of removed duplicates

### Added
- **Full CI/CD Pipeline** — 11 GitHub Actions workflows:
  - `test.yml` — Multi-platform test matrix (Ubuntu 22.04/24.04 × Python 3.10/3.11/3.12)
  - `pr-validation.yml` — Blocking PR gate (flake8, bandit, tests)
  - `security-gate.yml` — Security gate (bandit HIGH blocks, pip-audit, secrets scan)
  - `cve-scanner.yml` — Daily CVE scanning with auto-issue creation
  - `build-ubuntu.yml` / `build-windows.yml` — Platform binary builds
  - `release-gate.yml` — 5-stage release gate
  - `build-release.yml` — Automated GitHub Release creation
- **New UX components** (not yet integrated into MainWindow):
  - `ui/nav_rail.py` — Collapsible navigation rail (56px/200px)
  - `ui/channel_card.py` — Visual channel card with logo, status, favorites
  - `ui/channel_grid.py` — Responsive card grid with lazy loading (50/batch)
  - `ui/top_bar.py` — Search + filters + view toggle
  - `ui/status_bar.py` — Minimal status bar with scan progress
  - `utils/favorites.py` — Favorites and recently watched manager
- **UX Design Specification** — `docs/UX_SPECIFICATION_v1.9.0.md`
- **FluentColorsDark** theme and Ubuntu font detection in `ui/constants.py`

### Changed
- Version bumped to 1.9.0
- CI extracts version via grep instead of exec() (fixes `__file__` issue in CI)

### Closed Issues
- #33, #35, #36, #37 — All verified fixed in code and closed

## [1.8.2] - 2026-01-30

### Fixed (P1-High)
- **VLC Playback Failure** ([#35](https://github.com/arielsaghiv/tv_viewer/issues/35))
  - Root cause: Hardware acceleration flag `--avcodec-hw=vaapi` not supported in many environments
  - Solution: Removed hardware acceleration flags, use software decoding (stable and compatible)
  - Added VLC environment configuration for PyInstaller executables
  - Multiple fallback attempts for VLC initialization
  - Enhanced logging to diagnose VLC initialization issues
  
### Changed
- VLC arguments simplified to prioritize stability over hardware acceleration
- VLC initialization now tries 3 fallback methods before failing
- Better error messages with full stack traces for VLC issues
- PyInstaller executable now sets VLC_PLUGIN_PATH and LD_LIBRARY_PATH for system VLC

### Closed Issues
- #32: Segmentation fault when scanning channels (fixed in v1.8.1)
- #33: VLC detection error messages (fixed in v1.8.1)
- #34: Scanning animation layout problems (fixed in v1.8.1)

## [1.8.1] - 2026-01-30

### Fixed (P0-Critical)
- **Segmentation Fault on Scan** (Linux) ([#32](https://github.com/arielsaghiv/tv_viewer/issues/32))
  - Root cause: Background thread directly modifying tkinter UI state
  - Solution: All UI updates now scheduled on main thread using `root.after(0, ...)`
  - Prevents cross-thread tkinter access that caused crashes
  
- **VLC Detection Issue** ([#33](https://github.com/arielsaghiv/tv_viewer/issues/33))
  - Enhanced error detection to distinguish VLC binary vs python-vlc package
  - Shows specific installation commands based on what's missing
  - Error messages now identify exact component missing

- **Scanning Animation Layout** ([#34](https://github.com/arielsaghiv/tv_viewer/issues/34))
  - Fixed: 0% text no longer overlaps Earth graphic (moved to top-right)
  - Fixed: Shows "Stopped" when scan is stopped (not "Scanning...")
  - Improved visual hierarchy (percentage 14pt, stats 10pt, status 8pt)
  - Better text positioning following UX design consultation

### Changed
- Percentage display: Moved from center-bottom to top-right (155, 12)
- Stats display: Moved to bottom (90, 72) - more prominent
- Status text: Moved above stats (90, 58) - less prominent, italic
- Font sizes optimized for readability hierarchy

## [1.8.0] - 2026-01-29

### Added
- **Linux Executable Build** - PyInstaller-based single-file distribution for Ubuntu/Debian
- **Country Inference System** - Automatically detects country from language when missing (Android) ([#28](https://github.com/arielsaghiv/tv_viewer/issues/28))
- **Israeli Channel Detection** - Pattern-based detection for known Israeli channels (Android) ([#28](https://github.com/arielsaghiv/tv_viewer/issues/28))
- **Country Normalization** - Standardizes country codes (IL→Israel, US→United States, etc.) (Android) ([#27](https://github.com/arielsaghiv/tv_viewer/issues/27))

### Fixed
- **External Player Launch** - Removed canLaunchUrl check that was blocking launches (Android) ([#26](https://github.com/arielsaghiv/tv_viewer/issues/26))
- **Cast Button** - Now successfully opens external players for casting (Android) ([#26](https://github.com/arielsaghiv/tv_viewer/issues/26))
- **Countries Dropdown** - Now properly populated from channel metadata with inference (Android) ([#27](https://github.com/arielsaghiv/tv_viewer/issues/27))

### Changed
- **Scan Animation Performance** - Reduced frame rate from 200ms to 400ms (50% fewer redraws) (Python)
- **Channel List Font Size** - Increased from 11 to 12 for better readability (Python)
- **Channel List Row Height** - Increased from 36 to 40 pixels for better spacing (Python)

### Performance
- Scan animation CPU usage reduced by ~50% (fewer redraws)
- UI rendering optimized with larger font/spacing preventing cramped appearance

## [1.7.0] - 2026-01-28

### Added (Flutter Android App)
- **Persistent Logging Service** - File-based logging with rotation (5 files, 1MB each) ([#2](https://github.com/arielsaghiv/tv_viewer/issues/2))
- **User-Friendly Error Messages** - Comprehensive error handler with recovery suggestions ([#1](https://github.com/arielsaghiv/tv_viewer/issues/1))
- **Language Filter** - Filter channels by language with dropdown selector ([#12](https://github.com/arielsaghiv/tv_viewer/issues/12))
- **Wake Lock** - Screen stays awake during video playback ([#9](https://github.com/arielsaghiv/tv_viewer/issues/9))
- **Help Screen** - In-app FAQ, troubleshooting guide, and support contact ([#8](https://github.com/arielsaghiv/tv_viewer/issues/8))
- **Diagnostics Screen** - Device info, network status, stream URL tester ([#17](https://github.com/arielsaghiv/tv_viewer/issues/17))
- **Onboarding Service** - First-time user tooltips system ([#5](https://github.com/arielsaghiv/tv_viewer/issues/5))
- **Picture-in-Picture** - PiP support for Android 8.0+ ([#16](https://github.com/arielsaghiv/tv_viewer/issues/16))
- **Enhanced External Players** - Support for 6+ external players (VLC, MX Player, MPV, Just Player) ([#18](https://github.com/arielsaghiv/tv_viewer/issues/18))
- **USER_GUIDE.md** - End-user documentation ([#6](https://github.com/arielsaghiv/tv_viewer/issues/6))
- **FAQ.md** - Frequently asked questions document ([#7](https://github.com/arielsaghiv/tv_viewer/issues/7))
- **Global Error Handling** - All uncaught errors logged with stack traces
- **Log Export** - Export logs via share dialog for support

### Changed (Flutter Android App)
- Logging system integrated throughout app (replaced debugPrint)
- Help screen now exports actual logs via LoggerService
- Home screen menu links to Help and Diagnostics screens

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

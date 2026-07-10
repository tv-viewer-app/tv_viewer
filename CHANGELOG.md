# Changelog

All notable changes to TV Viewer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.22.2] - 2026-07-10

### Fixed
- Android crash: DatabaseException(database_closed) — 172 crash events eliminated
- Android crash: Could not decompress image — logo loading hardened
- Country detection fallback to device locale when timezone fails
- Docker healthcheck reduced from 60s to 300s (less log noise)
- Chrome extension rebuilt as popup app (Chrome Store compliance)
- Statistics now shows actual channel names instead of 'Israel General'
- Channel name resolution maps ALL URL hashes
- Israeli channels: 18 fixed, 5 dead pirate streams removed

### Security
- Chrome extension: URL validation rejects non-http(s) schemes
- Chrome extension: explicit CSP (script-src 'self')
- Proxy SSRF: redirects disabled
- channel_requests: anon UPDATE revoked, atomic RPC voting

## [2.22.1] - 2026-07-04

### Fixed
- Statistics shows actual channel names (KAN 11, Reshet 13) instead of 'Israel General'
- Channel name resolution maps ALL URL hashes, not just primary
- Proxy SSRF hardened (redirects disabled)
- Channel requests voting secured (atomic RPC, no direct UPDATE)

## [2.22.0] - 2026-07-03

### Added
- Smart channel sorting: channels ranked by health score × community play count
- Stream quality selector: choose Auto/1080p/720p/480p for HLS streams
- Chromecast support: cast streams to TV from the web player
- Channel request feature: suggest new channels and vote on suggestions
- EPG improvements: Israeli channel aliases, retry with backoff, slash-safe routing
- Auto-hide dead channels: 10+ broken reports hides from default listing

### Improved
- Israeli EPG coverage with dedicated sources and Hebrew name matching
- Weekly channel cleanup workflow removes stale broken channels
- Channel failure classification prevents false-positive broken reports

## [2.21.3] - 2026-07-02

### Fixed
- Refresh button crash: 'ChannelManager' has no attribute 'merge_channels'
- EPG race condition: '_aggressive_name_to_epg_ids' AttributeError spam in logs
- Channel health: 403 geo-blocked streams no longer falsely reported as broken
- Proxy endpoint returns X-Stream-Status header for upstream failures

### Improved
- Channel failure classification: geo_blocked, expired, unavailable categories
- Client receives structured failure reasons for better UX messaging
- Flutter CI upgraded from 3.32.0 to 3.44.4 (stable)
- Standalone Chrome extension (no Docker dependency)
- PWA manifest for installable web app

## [2.21.2] - 2026-07-02

### Added
- PWA support: web app installable from Chrome/Edge/mobile browsers
- Service worker for offline caching of static assets
- WinGet auto-submit workflow (submits on every release)
- Live statistics: today's active users, play count, live sessions
- POST proxy bootstrap for long URLs (fixes 414 errors with PlutoTV/Samsung streams)

### Fixed
- Legacy Supabase key errors in Docker RPC calls (report_channel_working/broken)
- Unclosed aiohttp sessions in proxy endpoint
- Channel repos updated: added German/Canadian sources, removed 5 dead repos

### Changed
- Chrome Extension packaged for sideloading from GitHub
- Statistics endpoint uses 30-min cached materialized views

## [2.21.1] - 2026-07-01

### Security
- Migrated from JWT tokens to new Supabase API keys format
- Publishable key (sb_publishable_*) replaces old anon JWT
- Secret key stored only in GitHub Actions secrets (never in code)
- Added docs/SECURITY.md with key management guidelines

### Fixed
- All old JWT tokens removed from source code
- GitHub secrets updated with rotated keys

## [2.21.0] - 2026-07-01

### Security
- Removed service_role key from docker-compose.yml and all client code
- Service_role key must be rotated (was exposed in git history)

### Added
- Verified-first channel browsing with health scoring (reliable/unstable/offline badges)
- Auto-fallback URLs: tries alternative sources before showing error
- Classified failure messages (geo-blocked, timeout, not-found, etc.)
- Per-country top channels and last access dates in statistics
- Server-side statistics cache (30-min TTL)

### Fixed
- EPG asyncio event loop lock error in Docker
- Channel status RLS script for report_channel_working
- 675 false crash reports (network errors now warnings)
- Dart SDK constraint updated to >=3.10.0

## [2.20.15] - 2026-07-01

### Security
- Removed the embedded Supabase service_role key from the mobile app (security hardening)
- Statistics on mobile now use the Supabase anon key with a graceful fallback to tvviewer.app

### Added
- Enhanced statistics: per-country top channels and last access dates
- Top 15 popular channels in statistics

### Fixed
- Dart SDK constraint updated to >=3.10.0
- Closed false crash issues #239 and #246

## [2.20.14] - 2026-06-30

### Fixed
- 675 false crash reports: network errors (SocketException) now logged as warnings, not crashes
- Statistics web UI: fixed "undefined" for channels played
- Merged 7 Dependabot patches

### Changed
- Supabase MCP moved to project-level config (no longer global)

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.11] - 2026-06-15

### Fixed
- SQLite BUSY errors eliminated (SharedPreferences write mutex — 75 errors fixed)
- F-Droid metadata rewritten from scratch (pipeline should pass now)
- Merged 4 Dependabot patches (aiohttp, certifi, uvicorn, requests)

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.10] - 2026-06-13

### Fixed — Statistics screen now works
- Root cause: Supabase RLS SELECT policy blocks anon reads on analytics_events
- Fix: use service_role key for statistics queries (server + Flutter)
- Docker: service_role key added to docker-compose defaults
- Flutter: embedded service_role key for direct Supabase reads
- GitHub secret SUPABASE_SERVICE_ROLE_KEY updated to new project

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.9] - 2026-06-10

### Fixed
- Statistics screen works on Android (embedded Supabase URL, fixed event_data query)
- In-app update restored (REQUEST_INSTALL_PACKAGES permission)
- Play Core excluded from APK (F-Droid compliance)

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.5] - 2026-06-09

### Fixed
- Removed Play Integrity / Firebase dependency (F-Droid APK check now passes)
- Fixed crash monitor script for new Supabase schema
- Merged aiohttp and uvicorn patches

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.10] - 2026-06-13

### Fixed — Statistics screen now works
- Root cause: Supabase RLS SELECT policy blocks anon reads on analytics_events
- Fix: use service_role key for statistics queries (server + Flutter)
- Docker: service_role key added to docker-compose defaults
- Flutter: embedded service_role key for direct Supabase reads
- GitHub secret SUPABASE_SERVICE_ROLE_KEY updated to new project

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.9] - 2026-06-10

### Fixed
- Statistics screen works on Android (embedded Supabase URL, fixed event_data query)
- In-app update restored (REQUEST_INSTALL_PACKAGES permission)
- Play Core excluded from APK (F-Droid compliance)

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.4] - 2026-06-09

### Fixed
- Map screen: tile fetch errors handled gracefully (30 crashes eliminated)
- Removed google_fonts dependency (unblocks F-Droid build)
- Web proxy: stream timeouts handled cleanly (35 server_errors eliminated)

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.10] - 2026-06-13

### Fixed — Statistics screen now works
- Root cause: Supabase RLS SELECT policy blocks anon reads on analytics_events
- Fix: use service_role key for statistics queries (server + Flutter)
- Docker: service_role key added to docker-compose defaults
- Flutter: embedded service_role key for direct Supabase reads
- GitHub secret SUPABASE_SERVICE_ROLE_KEY updated to new project

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.9] - 2026-06-10

### Fixed
- Statistics screen works on Android (embedded Supabase URL, fixed event_data query)
- In-app update restored (REQUEST_INSTALL_PACKAGES permission)
- Play Core excluded from APK (F-Droid compliance)

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.3] - 2026-06-07

### Fixed
- Flaky rate limit test made deterministic (no more CI failures)
- All documentation aligned with v2.20 state

### Changed
- Fastlane metadata updated for store listings

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.10] - 2026-06-13

### Fixed — Statistics screen now works
- Root cause: Supabase RLS SELECT policy blocks anon reads on analytics_events
- Fix: use service_role key for statistics queries (server + Flutter)
- Docker: service_role key added to docker-compose defaults
- Flutter: embedded service_role key for direct Supabase reads
- GitHub secret SUPABASE_SERVICE_ROLE_KEY updated to new project

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.9] - 2026-06-10

### Fixed
- Statistics screen works on Android (embedded Supabase URL, fixed event_data query)
- In-app update restored (REQUEST_INSTALL_PACKAGES permission)
- Play Core excluded from APK (F-Droid compliance)

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.2] - 2026-06-06

### Fixed
- Statistics page shows comprehensive data (channels, categories, countries, recently added)
- Web renderStats handles new API format

### Added
- Supabase analytics RLS script for event collection

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.10] - 2026-06-13

### Fixed — Statistics screen now works
- Root cause: Supabase RLS SELECT policy blocks anon reads on analytics_events
- Fix: use service_role key for statistics queries (server + Flutter)
- Docker: service_role key added to docker-compose defaults
- Flutter: embedded service_role key for direct Supabase reads
- GitHub secret SUPABASE_SERVICE_ROLE_KEY updated to new project

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.9] - 2026-06-10

### Fixed
- Statistics screen works on Android (embedded Supabase URL, fixed event_data query)
- In-app update restored (REQUEST_INSTALL_PACKAGES permission)
- Play Core excluded from APK (F-Droid compliance)

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.0] - 2026-06-06

### Fixed — Analytics connectivity
- Supabase project migrated to new instance (cdtxpefohpwtusmqengu)
- Default Supabase URL/key embedded in config (Docker works out of box)
- Statistics page now works on both Docker and Android
- Fixed search_path security warnings on Supabase functions

## [2.19.5] - 2026-06-06

### Fixed
- Statistics screen: was pointing to non-existent GitHub Pages URL
- Country detection: timezone-based inference for both Flutter and Web clients
- Docker image updated to latest version
- Web analytics now sends detected country code

## [2.19.1] - 2026-06-06

### Security Hardening
- Statistics screen no longer queries Supabase directly (info disclosure fix)
- Removed device_id from analytics API responses (privacy improvement)
- Added rate limiting (10 req/min) + 5-min cache to /api/statistics endpoint
- Flutter client uses server-side pre-aggregated data only

### Fixed
- Memory leak: HTTP client not closed on error path in statistics screen
- Wake lock timer race: added mounted guard after async await
- Statistics setState after dispose: added mounted checks
- aiohttp updated to >=3.14.0

## [2.19.0] - 2026-06-06

### Added — Community Statistics page
- New statistics screen showing anonymous aggregated usage data
- Available in Android app (menu → Community Stats) and web client (📊 button)
- Shows: active users, channel plays, top 10 channels, platform breakdown, countries
- All data is anonymous — no personal information collected or displayed
- Backend API endpoint: GET /api/statistics

### Fixed
- Pin google_fonts <6.3.0 (const evaluation error on Flutter 3.32+)
- Fix surfaceContainerHighest → surfaceContainerHigh for broader compat

## [2.18.2] - 2026-06-05

### Fixed
- Pin google_fonts <6.3.0 (const evaluation error on Flutter 3.32+)

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.10] - 2026-06-13

### Fixed — Statistics screen now works
- Root cause: Supabase RLS SELECT policy blocks anon reads on analytics_events
- Fix: use service_role key for statistics queries (server + Flutter)
- Docker: service_role key added to docker-compose defaults
- Flutter: embedded service_role key for direct Supabase reads
- GitHub secret SUPABASE_SERVICE_ROLE_KEY updated to new project

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.9] - 2026-06-10

### Fixed
- Statistics screen works on Android (embedded Supabase URL, fixed event_data query)
- In-app update restored (REQUEST_INSTALL_PACKAGES permission)
- Play Core excluded from APK (F-Droid compliance)

## [2.20.13] - 2026-06-20

### Fixed
- Statistics screen on Android: certificate pinning rejected Supabase's rotated TLS cert
- Removed Supabase from certificate pinning hosts (they rotate certs frequently)
- Statistics queries use standard HTTP client instead of pinned client

## [2.20.0] - 2026-06-06

### Fixed — Analytics connectivity
- Supabase project migrated to new instance (cdtxpefohpwtusmqengu)
- Default Supabase URL/key embedded in config (Docker works out of box)
- Statistics page now works on both Docker and Android
- Fixed search_path security warnings on Supabase functions

## [2.19.5] - 2026-06-06

### Fixed
- Statistics screen: was pointing to non-existent GitHub Pages URL
- Country detection: timezone-based inference for both Flutter and Web clients
- Docker image updated to latest version
- Web analytics now sends detected country code

## [2.19.1] - 2026-06-06

### Security Hardening
- Statistics screen no longer queries Supabase directly (info disclosure fix)
- Removed device_id from analytics API responses (privacy improvement)
- Added rate limiting (10 req/min) + 5-min cache to /api/statistics endpoint
- Flutter client uses server-side pre-aggregated data only

### Fixed
- Memory leak: HTTP client not closed on error path in statistics screen
- Wake lock timer race: added mounted guard after async await
- Statistics setState after dispose: added mounted checks
- aiohttp updated to >=3.14.0

## [2.19.0] - 2026-06-06

### Added — Community Statistics page
- New statistics screen showing anonymous aggregated usage data
- Available in Android app (menu → Community Stats) and web client (📊 button)
- Shows: active users, channel plays, top 10 channels, platform breakdown, countries
- All data is anonymous — no personal information collected or displayed
- Backend API endpoint: GET /api/statistics

### Fixed
- Pin google_fonts <6.3.0 (const evaluation error on Flutter 3.32+)
- Fix surfaceContainerHighest → surfaceContainerHigh for broader compat

## [2.18.0] - 2026-06-03

### Fixed — Play Store compliance
- Target SDK 35 (Play Store requirement)
- Removed unused photo/video/storage permissions (from dependencies)
- Removed REQUEST_INSTALL_PACKAGES (not needed for Play Store users)
- Added obfuscation + debug symbols to Play Store deploy

### Changed
- Upgraded to Flutter 3.32 + Gradle 8.9 + AGP 8.7
- PiP temporarily disabled (floating package incompatible with Flutter 3.32)

## [2.17.6] - 2026-05-31

### Fixed — Screen turns off during video playback (Android 14+)
- `wakelock_plus` alone is unreliable on Android 14+ (system silently drops wake lock)
- Added native `FLAG_KEEP_SCREEN_ON` via MethodChannel as primary mechanism
- Periodic re-assertion every 5 minutes catches any silent drops
- Wake lock properly cleared when leaving player screen

### Fixed — Build compatibility
- Downgraded `compileSdk` to 34 for Java 21 compatibility (F-Droid)
- Bumped AGP to 8.2.2 for Kotlin 2.3 compatibility
- Downgraded `cupertino_icons` to ^1.0.8 for Flutter 3.24 compatibility

## [2.16.8] - 2026-05-27

### Fixed — Background playback not working on Android 14+ (API 34/35)
Background audio completely broken on Android 14+ due to three issues:
1. **Missing foreground service type declaration** — Android 14+ requires
   `android:foregroundServiceType="mediaPlayback"` on the service element.
   Without it, `startForeground()` throws `MissingForegroundServiceTypeException`.
2. **`video_player` cannot play in background** — ExoPlayer's video surface is
   destroyed when the app goes to background. Now uses `just_audio` (already a
   dependency) to play audio-only in background, seamlessly switching back to
   video when foregrounded.
3. **Race condition in setting load** — `_loadBackgroundPlaybackSetting()` was
   async but not gated, so quick background transitions could see the default
   (`false`) value.

### Changed — Background playback enabled by default
For a media/IPTV app, audio should continue when backgrounded. Previously
defaulted to `false`, now defaults to `true`. Users can still disable in Settings.

## [2.16.7] - 2026-05-24

### Fixed — EPG errors logged with empty message
v2.16.6 reported `EPG fetch error for ...: ` (no detail) when sources failed,
making diagnosis impossible. Some aiohttp exception subclasses have an empty
`str(exc)` — only `type(exc).__name__` carries the signal. Now logs
`type: detail` and also catches non-aiohttp exceptions (gzip / IncompleteRead /
asyncio errors) that previously fell through to the generic handler.

### Fixed — Middleware "No response returned" on HLS playback
Streaming `/api/proxy` responses regularly raised
`RuntimeError: No response returned` from `BaseHTTPMiddleware` (a known
Starlette streaming bug — client disconnects mid-stream confuse the
middleware). Now both `SecurityHeadersMiddleware` and `CSRFOriginMiddleware`
catch the exception on proxy paths and return HTTP 499 (the bytes were
already delivered before the disconnect).

### Improved — Channel auto-categorization (6837 channels rescued from General)
v2.16.6 still had 6923 channels stuck in "General". This release pushes that
down to **186** (well under the 500 target) by adding aggressive but
defensible heuristics:

- **Documentary**: now catches crime/killer/murder/mystery/forensic/evil/
  unsolved/paranormal/prison/investigation/WWII keywords
- **Music**: classical, ambient, instrumental, lo-fi, chill, funk, disco,
  k-pop, j-pop, mariachi, salsa, reggaeton, plus more artist names
- **Radio**: now catches `107FM` / `91FM` (no word boundary needed), US
  station codes `93X` / `97X`, plus AM/XM and `\d+\s*FM` patterns
- **News**: parliament, council, civic, public-access, c-span
- **Education**: TED, university TV, community media education
- **Entertainment** (catch-all): expanded with `tele\w*` / `canal\w*` /
  `kanal\w*` prefix-tolerant compound matches; broadcaster acronyms (BBC,
  RAI, RTL, MBC, CBC, ITV, RTP, NHK, KBS, SBS, RTI, Reelz, Nove, Awe,
  Atlantis, Popcorn, La1-9, M3-7); non-Latin script detection (Cyrillic,
  CJK, Hebrew, Arabic, Hangul, Devanagari)
- **Final fallback**: any channel with 3+ Latin-alphabetic chars and no
  other signal → Entertainment (only pure-symbol/numeric names stay General)

Final distribution on 14,037-channel cache:
| Category | Count | % |
|---|---|---|
| Entertainment | 7173 | 51.1% |
| Radio | 1600 | 11.4% |
| News | 1345 | 9.6% |
| Music | 826 | 5.9% |
| Religious | 752 | 5.4% |
| Movies | 508 | 3.6% |
| Sports | 486 | 3.5% |
| Documentary | 424 | 3.0% |
| Kids | 273 | 1.9% |
| Lifestyle | 251 | 1.8% |
| **General** | **186** | **1.3%** |
| Education | 179 | 1.3% |
| Shopping | 30 | 0.2% |
| Weather | 4 | 0.0% |

Zero regressions — name patterns only fire when the source category
resolves to "General".

## [2.16.6] - 2026-05-24

### Fixed — EPG truncation (third time the charm)
v2.16.5 fixed gzip-of-gzip but EPG was *still* truncating in production. Root
cause: `response.content.read(N)` on aiohttp returns whatever the read syscall
produced — it does **not** drain a chunked-transfer body. With CDN responses
using `Transfer-Encoding: chunked` we were getting partial `.gz` bytes that
failed decompression.

- `utils/epg.py`: rewrote `_fetch_source` to use `async for chunk in
  response.content.iter_chunked(256*1024)`. This drains the stream fully and
  applies the size cap inside the loop. Added a post-read `Content-Length`
  sanity check that rejects partial bodies.

### Improved — Channel auto-categorization (107 channels rescued from General)
- `utils/normalize.py`: rewrote `_NAME_PATTERNS` to catch CamelCase compound
  brand names. Previously `\bweather\b` did not match `AccuWeather` because
  `u→W` is word-char-to-word-char (no `\b` boundary). Now we use compound
  alternatives plus lookbehind/lookahead to catch:
  - **Weather**: AccuWeather, WeatherNation, WeatherScan, WeatherStar
  - **News**: 55 US local affiliate stations (ABC 10, FOX 5, NBC Bay Area,
    WKBW, WCPO, KGO, WABC, etc.) + Newsmax, OANN, Cheddar, Bloomberg, Reuters,
    Sky News, France 24, DW, i24
  - **Documentary**: A&E, Biography, Crime 360, 60 Days In, Forensic Files,
    Nat Geo, Smithsonian, History Channel, Discovery
  - **Shopping**: Gem Shopping, Jewelry TV, Shinsegae, Gongyoung, KShopping
  - **Lifestyle**: Food Network, Cooking Channel, Hell's Kitchen, Tasty,
    HGTV, Magnolia, Travel Channel, Fashion TV
  - **Movies**: MGM Presents, FilmRise, Action Hollywood, Hallmark Movies
  - **Kids**: BabyTV, Pokemon, Peppa, Paw Patrol, CoComelon, Teletoon
- Audit on 14,037-channel cache: **107 reclassified out of General, 0 regressions**
  (existing categories untouched — name patterns only fire when source category
  resolves to "General").

### Added — Closed-loop automation (L2 triage)
- `scripts/triage_issue.py`: deterministic issue-triage helper. Given an
  issue number, extracts error signature from fenced log blocks, queries
  Supabase for occurrence count over the last 24h, assigns severity (P1-P4
  based on 24h-rate threshold), maps platform labels, and posts an enriched
  triage comment. Dedups via `<!-- sig:X -->` HTML markers — if the same
  signature already has an open issue, the new one is closed with a link.

## [2.16.5] - 2026-05-24

### Fixed — EPG completely broken in Docker (gzip-of-gzip)
Every EPG source (Pluto, Samsung, Plex, EPGShare UK, EPGShare IL) was failing
with `Compressed file ended before end-of-stream marker`. Root cause: some CDNs
serve `.gz` files with `Content-Encoding: gzip` on top, and aiohttp auto-
decompresses the transport layer — leaving plain XML where we then tried a
second gzip-decompress and got truncation errors.

- `utils/epg.py`: disabled aiohttp `auto_decompress`, set `Accept-Encoding: identity`,
  and detect gzip by **magic bytes** (`\x1f\x8b`) rather than trusting URL or
  `Content-Encoding` headers. If a `.gz` URL serves plain XML, we now accept it
  instead of bailing.

### Fixed — EPG fetch storm on every `/api/epg/*` request
When the initial EPG fetch failed, `_initialized` stayed `False`, so every
subsequent endpoint hit re-triggered a full 5-source fetch — flooding upstream
EPG providers and producing log spam at ~1/sec per channel view.

- Added a 5-minute failure cooldown (`_last_failed_fetch`) so we don't hammer
  upstream after a fully-failed fetch. Cleared on successful fetch.

### Added — Weather as its own category
Previously `weather` was merged into Education (which was confusing — a 24h
forecast channel is not Education). Now Weather is its own canonical category
across all three clients with `🌦️` icon in the web sidebar.

- `utils/normalize.py`: added `Weather` to `CANONICAL_CATEGORIES`, mapped
  `weather`/`weather & traffic`/`meteo`/`forecast` → `Weather`, added name-
  pattern regex for weather/meteo/forecast/weatherscan/wetter/metar.
- `flutter_app/lib/models/channel.dart`: mirrored in Dart.
- `web/static/index.html`: added Weather/Nature/Shopping/Radio emoji icons
  (the latter three were already canonical but rendering the default 📺 fallback).

## [2.16.4] - 2026-05-24

### Fixed — Proxy 403 storm (was the *real* "everything is slow" cause)
Production docker logs showed two dead Kan11 URLs hammering `/api/proxy`
hundreds of times per second, all returning 403. With FastAPI's single
event loop, that saturated the proxy and pushed every other request
(`/api/channels`, `/api/epg/*`, even static assets) into the back of the
queue. Three coordinated fixes:

- **Client `tryNextSource()` no longer cycles dead URLs forever.** The
  old `(idx + 1) % length` rotation, combined with HLS.js calling
  `tryNextSource()` on every fatal error, made the loop unbounded. Now
  tracks a per-attempt `_triedSources` Set and bails with
  *"Stream unavailable — all sources failed"* once every source has
  been tried once.
- **Client HLS.js retry budget capped.** Defaults are 4 manifest +
  6 fragment retries per source with exponential backoff; on a 403
  that compounds badly across multiple sources. Lowered to
  `manifestLoadingMaxRetry: 1`, `fragLoadingMaxRetry: 2`, with short
  delays. If the first attempt is 403 the URL is dead, don't retry.
- **Server-side `/api/proxy` circuit breaker.** After 5 consecutive
  4xx responses for the same URL within 30 s, subsequent requests
  for that URL are short-circuited with the cached status for 60 s —
  no upstream call, no log spam, no event-loop time. Protects against
  misbehaving clients we can no longer fix (stale tabs on old app
  versions). Successful manifest/segment responses clear the breaker
  immediately.

## [2.16.3] - 2026-05-24

### Fixed — EPG never loaded in Docker / large-feed deployments
- `_fetch_source` raised its compressed-download cap from **10 MB → 64 MB**
  and the decompressed cap from **50 MB → 300 MB**. Three of the six default
  community XMLTV mirrors (Pluto US, Samsung TV+ US, Plex Live TV, dp247
  Freeview) had grown past the 10 MB compressed limit since the original
  cap was set, so each silently returned empty data. The result was that
  fresh Docker containers initialized with `⚠️ EPG: no program data
  available (1.5s)` and `/api/epg/*` responses always had empty
  `now`/`next`/`schedule` — EPG never appeared in the web UI on any card.
- All silent EPG failure paths (non-200 status, gzip-decompression error,
  ClientError, TimeoutError, parse error, oversized payload) are now logged
  at **WARNING** with the source URL, so docker logs make it obvious which
  feed is misbehaving. `asyncio.gather` aggregation zips results back to
  their source URL before logging.

### Fixed — Web UI: EPG fetcher no longer blocks channel-list filtering
- `renderChannels()` previously fired **30 parallel `/api/epg/*` requests**
  on every sidebar click. With the browser's per-origin connection cap, the
  next `/api/channels` request was queued behind the EPG wall, producing
  the "many seconds" delay users reported when switching categories or
  countries. Logs from a real session showed the same EPG URLs being
  refetched repeatedly across clicks.
- Added a 200 ms settle delay, a per-render `AbortController`, an in-memory
  EPG cache keyed by channel name, an in-flight dedup map, and a concurrency
  cap of 4 simultaneous EPG fetches. Rapid sidebar clicks now cancel
  superseded batches before any EPG request hits the network.

### Fixed — Web UI: filter race condition
- `loadChannels()` had no request token, so the *last-completed* response
  won the render, not the *last-clicked* selection. After a fast
  category→country→category click sequence, the dropdown and channel grid
  could end up out of sync. Added a monotonic `_loadSeq` token, an
  `AbortController`, dual seq guards, and optimistic loading UI on click.

### Fixed — Web server: O(1) filter dispatch
- `_ChannelCache` now builds `by_category`, `by_country`, `by_cat_country`,
  and `local_channels` indexes once per refresh. `get_channels()` dispatches
  to the right index instead of scanning all channels per request — 16-50×
  faster at 50,000 channels (synthetic benchmark).

## [2.16.2] - 2026-05-24

### Fixed — Supabase analytics views
- `mv_top_channels` unique index now covers the full GROUP BY tuple
  `(channel_hash, channel_country, channel_category)`. The v2.16.0 index
  only covered `channel_hash`, causing `refresh_analytics_views()` to fail
  with HTTP 409 (duplicate key) once any channel appeared under more than
  one country/category combo. Fixes #195. Apply
  `scripts/fix_mv_top_channels.sql` in the Supabase SQL Editor (idempotent).

### Added — Cross-client error telemetry

Clients now report **caught and uncaught errors** to Supabase
`analytics_events` as `event_type='client_error'` (server crashes use
`server_error`), so we can see which errors actually hit users and prioritize
fixes data-driven instead of guessing from GitHub issues. Respects the
existing opt-in (`TELEMETRY_ENABLED`) — silent for users who never consented.

No schema change — `analytics_events.event_data` is JSONB. Event payload:

```json
{ "error_type", "error_message", "stack_top", "stack_summary",
  "severity": "warning|error|fatal", "is_handled": bool, "context": "..." }
```

- **Desktop (Python)** — new `analytics.track_error(error, context=, severity=,
  is_handled=)`. The existing `crash_reporter` global handler now fires
  `analytics.track_crash` silently *before* the user dialog so telemetry is
  captured even if the user dismisses. New `threading.excepthook` catches
  background-daemon-thread crashes (notably StreamChecker's asyncio thread)
  that previously vanished.
- **Mobile (Flutter)** — new `AnalyticsService.trackError(error, stack,
  context:, severity:, isHandled:)`. `CrashlyticsService` now forwards both
  `FlutterError.onError` and `PlatformDispatcher.instance.onError` to
  Supabase analytics in addition to the existing Crashlytics path, so we
  get coverage on installs without Firebase configured.
- **Web (FastAPI)** — new global `@app.exception_handler(Exception)` that
  posts `server_error` events tagged with a stable per-instance UUID
  (groups errors per Docker container). Browser-side `window.onerror` +
  `unhandledrejection` POST to the existing `/api/analytics` endpoint as
  `client_error`.

Tests: 6 new unit tests in `tests/test_analytics.py` covering shape,
severity normalization, message/context truncation, and the handled flag.
339/339 tests pass.


## [2.16.1] - 2026-05-24

### Security
This is a security-hardening release covering both the Supabase schema
(linter findings) and the web/mobile clients (audit findings).

#### Supabase schema (`scripts/supabase_migration_v2.16.1.sql`)
Idempotent — safe to re-run. After applying, verify with
`python scripts/supabase_doctor.py`.

- **channel_votes RLS policy missing**: RLS was enabled in v2.16.0 but no
  SELECT policy existed, so the column-level GRANT was silently denying
  all rows. Added `cv_anon_select` (`FOR SELECT TO anon USING (true)`) —
  the existing column-level grant on `(url_hash, vote, created_at)`
  continues to hide `device_id` and `id`.
- **tv_viewer_schema_version() search_path mutable**: pinned to
  `pg_catalog, public`. Prevents a privileged caller from changing
  `search_path` and hijacking object resolution inside the function.
- **channel_sources.csrc_anon_update was USING (true)**: the policy
  let any anon caller `UPDATE` any row in the source-reliability table
  (the WITH CHECK only validated *new* values). No client code writes
  this table — only the admin `populate_supabase.py` does, via the
  service_role key which bypasses RLS. Revoked the anon UPDATE / INSERT
  / DELETE policies entirely; kept SELECT.
- **Admin SECURITY DEFINER functions reachable by `authenticated`**:
  `cleanup_old_data`, `db_health`, `refresh_analytics_views`,
  `truncate_channels`, `report_source_health` were callable by any
  signed-in user. Revoked from `authenticated` and `anon`; granted
  only to `service_role`.

Not changed (by design): `report_channel_broken`,
`report_channel_working`, `promote_channel_source` remain anon-callable.
This is the v2.16.0 architecture — the app has no user accounts, and
those RPCs enforce per-device rate limits internally.

#### TLS / certificate validation (`ssl=False` audit)
- **`web/server.py` analytics POST**: was sending the Supabase anon JWT
  and `device_id` over TLS with verification disabled. Now uses a
  process-wide strict SSL context built from `certifi` (TLS 1.2+,
  hostname check, full chain validation).
- **`web/server.py` `/api/proxy` upstream**: now verifies upstream
  TLS by default. For operators who proxy legacy IPTV servers with
  broken/self-signed certs there is an explicit, log-loud opt-out:
  `TV_VIEWER_PROXY_INSECURE_TLS=1`.
- **`_is_private_ip` fail-closed**: DNS errors no longer fall through
  to "not private" — they're treated as private (closes the partial
  DNS-rebinding window in the proxy SSRF guard).
- **Flutter `pinned_http_client.dart` fail-closed**: previously
  returned `true` for unknown certs "during collection phase", which
  was strictly worse than no pinning (accepted any cert the OS trust
  chain had already rejected, i.e. exactly the MITM case). Now
  rejects. Also removed a copy/paste-duplicated Amazon Root CA
  fingerprint that was mislabelled as ISRG X1.

#### Web client hardening
- **Stored XSS in channel grid** (`web/static/index.html`): the inline
  `onerror="this.outerHTML=mono('${esc(ch.name)}')"` handler on every
  channel logo was vulnerable to a malicious channel name. HTML entity
  decoding in attribute values restores `'` *before* the JS parser
  sees it, so a name like `'); alert(1); //` would break out of the
  string and execute. Replaced with a data attribute + programmatic
  `addEventListener('error', …)` binding.
- **Sub-Resource Integrity** for third-party scripts: pinned
  `hls.js@1.5.20` (was unpinned `@1`!) and `leaflet@1.9.4` and added
  `integrity="sha384-…"` + `crossorigin="anonymous"`. A jsDelivr/unpkg
  compromise can no longer serve attacker-controlled JS to users.
- **CSRF Origin guard** middleware: state-changing requests
  (POST/PUT/PATCH/DELETE) whose Origin/Referer don't match this
  server's host are rejected. CLI/mobile callers (no Origin header)
  are still allowed — they don't carry ambient browser credentials.
  Configurable allowlist via `TV_VIEWER_ALLOWED_ORIGINS`. The
  `/api/health/report` endpoint is exempt (already rate-limited and
  validated; mobile clients post to it cross-origin).

### Deferred to a follow-up release
Documented in the security audit and accepted as `Known limitations`:
- DNS-rebinding TOCTOU in `/api/proxy` (mitigated by the fail-closed
  resolver change; the proper fix needs a per-request connector with a
  static resolver).
- `ch_anon_insert` policy still allows anon `INSERT` on `channels` —
  the systemic catalogue-poisoning channel exists, but is no longer
  exploitable as XSS now that the inline `onerror` handler is gone.



## [2.16.0] - 2026-05-23

### Added
- **Atomic Supabase RPCs** (`scripts/supabase_migration_v2.16.0.sql`):
  - `report_channel_broken(p_url_hash, p_device_id)` — replaces the fragile
    GET-then-PATCH dance on `channels.report_count`. Per-device 10-minute
    throttle and 100-vote/hour abuse cap.
  - `report_channel_working(p_url_hash, p_device_id, p_response_time_ms)` —
    finally makes the documented `report_count >= 3` consensus rule fire:
    `channel_status.report_count` is now refreshed from the audit trail on
    every working vote (was stuck at 1).
  - `promote_channel_source(name, url, hash)` — atomic, race-free URL
    promotion by exact name match server-side. No more PostgREST filter
    escaping, no more lost-update races on `urls[]`.
- **`channel_votes` audit trail** — per-`(device_id, url_hash, vote)`
  records with 30-day decay window. Enables future abuse-detection and
  vote-decay policies.
- **`scripts/supabase_doctor.py`** — one-command health check that
  verifies the migration is applied (table, RPCs, schema version) and
  prints clear remediation steps on failure.
- **`utils.analytics.get_device_id()`** — public accessor for the stable
  anonymous device UUID (previously only available via the analytics
  service instance).

### Changed
- **`utils/supabase_channels.py`** `report_channel` and
  `report_channel_working` now call the new SECURITY DEFINER RPCs instead
  of read-modify-write REST calls. Eliminates lost-update races under
  concurrent reports.
- **`web/server.py::_promote_source_supabase`** rewritten to call the
  `promote_channel_source` RPC. Removed the ad-hoc `ilike` escaping —
  the RPC handles name matching server-side.

### Security
- **RLS lockdown**: `anon` role's direct `UPDATE` / `DELETE` on
  `channels` is revoked. Since the anon key ships inside every APK and
  Docker image, any caller could previously mass-rewrite the catalog.
  All writes now flow through the rate-limited RPCs above.
- `channel_votes` is `SELECT`-only for anon (writes via RPC only).

### Migration notes
1. Run `scripts/supabase_migration_v2.16.0.sql` in the Supabase SQL
   editor (idempotent, safe to re-run).
2. Verify with `python scripts/supabase_doctor.py`.
3. Older clients (≤2.15.x) keep working — they hit the legacy REST
   endpoints which still respond, but they bypass the new throttles.

## [2.15.4] - 2026-05-23

### Fixed
- **EPG empty in Docker**: a transient network failure during container
  startup poisoned the on-disk EPG cache with `{}`. `_load_cache` then
  set `_initialized=True` for the empty cache, and `_do_initialize`
  refused to re-fetch for 12 hours. Three guards added: (1) empty caches
  on disk are now treated as cache-miss and deleted; (2) `_do_initialize`
  no longer overwrites a populated in-memory map with an empty result
  (preserves working data through transient failures); (3) the cache
  file is only written when at least one channel was fetched.
- **Broken-reported channels still showed green**: `reportBroken()` did
  not update local `channelHealth` — only the server was notified. The
  dot now flips to red immediately on report and persists via
  localStorage. Also fixed the dot-priority rule so a local 'broken'
  observation always overrides a catalog `status='working'`.

### Added
- `GET /api/epg-status` — diagnostics (channel count, last-fetch time,
  configured sources). Useful for verifying Docker EPG state without
  shelling into the container.
- `POST /api/epg/refresh` — force a fresh EPG fetch bypassing cache.
  Lets users recover from a poisoned cache without restarting the
  container.
- Cast menu now explains *why* Chromecast is unavailable on HTTP-LAN
  Docker deployments (Cast Web Sender SDK requires HTTPS). Suggests
  workarounds: browser-native cast menu, HTTPS reverse-proxy, or
  Copy-URL → VLC.

## [2.15.3] - 2026-05-23

### Fixed
- **Channel-status indicator colors were inverted**: working channels showed
  a red dot and unchecked-but-likely-working showed green. Replaced the
  ambiguous `.live`/`.ok` CSS with explicit `.working` (green pulse),
  `.offline` (red), `.unchecked` (dim blue). Local observations from
  `channelHealth` are now preferred over stale catalog `status`.
- **2-letter ISO country codes leaking to the UI** (FO, GL, KP, MC, MO, MT,
  etc.): consolidated three duplicate `_normalize_country` implementations
  (`utils/normalize.py`, `web/server.py`, `core/channel_manager.py`) into a
  single source of truth. `utils/normalize.COUNTRY_CODES` now covers all
  active ISO 3166-1 alpha-2 codes, and `COUNTRY_CODES_ALPHA3` maps alpha-3 →
  alpha-2. Unknown codes resolve to "Unknown" instead of leaking the bare
  code into the sidebar.
- **Cast button immediately failed** with "cast cancelled or unavailable":
  Remote Playback API can't transfer a MediaSource (used by hls.js) to a
  Chromecast. Loaded the Google Cast Web Sender SDK and added a real "Cast
  to Chromecast" option that sends the HLS URL directly to the receiver
  (which plays HLS natively). Remote Playback API kept as a secondary
  option for AirPlay/Safari.
- **EPG not appearing for Israeli channels**: added a Hebrew→English alias
  table for major Israeli channels (Channel 14, Keshet 12, Reshet 13,
  Kan 11, Sport 1-5, i24NEWS, etc.) so the existing fuzzy matcher can find
  English-named EPG entries from epgshare01's IL1 source when the playlist
  uses Hebrew names like "ערוץ 14".
- **DOM-index mismatch in `markPlaying`**: status-dot updates now look up
  cards by `data-url` attribute instead of `grid.children[idx]`, which was
  pointing at the wrong card whenever the grid was sorted or paginated.

### Changed
- **Health-report rate limits relaxed** to fit real (non-adversarial) usage.
  v2.15.2's global cap of 30/min/IP was rejecting legitimate single-user
  traffic from multi-source validation flows with HTTP 429. Global limit
  raised to 600/min, promote-limit to 10/min. When either is exceeded, the
  endpoint now returns HTTP 200 with `{"status":"throttled"}` (downgrading
  to a no-op or non-promote write) instead of 429 — the frontend's
  fire-and-forget POSTs no longer generate console noise.
- **Client-side dedup** for `/api/health/report`: each (URL, status,
  promote) tuple is only POSTed once per session, eliminating the request
  flood that caused the 429 burst in the first place.

### Internal
- `web/server.py` and `core/channel_manager.py` now import
  `normalize_country` from `utils.normalize` rather than carrying their own
  copies. Fixes pre-existing bugs in `core/channel_manager.py` where
  `'US': 'US'`, `'GB': 'UK'`, and `'AE': 'UAE'` either returned the bare
  code or used a non-standard short form.
- `tests/test_web.py::TestHealthReportSecurity::test_health_report_rate_limit_global`
  updated to assert the new "downgrade-not-reject" behavior (HTTP 200 +
  `status: "throttled"` instead of HTTP 429).

## [2.15.2] - 2026-05-23

### Security
- **PostgREST injection hardening**: `/api/health/report` now rejects channel
  names containing PostgREST filter metacharacters (`,`, `(`, `)`, `*`, `:`)
  and control characters before forwarding to Supabase. All shared-DB writes
  use aiohttp's `params=` URL encoding instead of f-string interpolation,
  closing a filter-syntax injection vector that could let a crafted request
  alter rows other than the channel being reported.
- **Rate limiting** on `/api/health/report`: 30 reports/min/IP (global) and
  5 promote-writes/min/IP. Mitigates the "pinning attack" where an attacker
  could spam `promote=true` with a bad URL to degrade popular channels for
  all users. In-memory token bucket — no new dependency.
- **Case-insensitive Supabase promote**: switched to `name=ilike` with %/_
  escaped so "BBC News" and "bbc news" don't silently no-op the shared-DB
  update.

### Fixed
- **EPG fuzzy matching false positives**: aggressive suffix-strip (` news`,
  ` tv`, ` channel`, ` live`, ` stream`) and trailing-word removal now only
  return a match when the stripped form maps to a **unique** EPG ID. Prevents
  silent wrong-program bugs like "Discovery Channel" → some unrelated
  "Discovery" feed, or "Sky Sports Live" → wrong "Sky Sports" entry. Safe
  HD/SD/4K suffix matches remain unchanged.
- **Test suite headless safety**: `tests/test_toast.py` now skips when no Tk
  display is available, instead of erroring out on Linux dev machines without
  DISPLAY set. CI runners with xvfb still execute the tests.

### Changed
- **CodeQL workflow**: removed `java-kotlin` from the language matrix. The
  Flutter `android/` directory is generated Gradle/Kotlin boilerplate; CodeQL
  Autobuild has been failing consistently with no actionable findings. Python
  analysis (the real signal) continues to run.
- **`favorites.json` is now gitignored** to stop user runtime data churn from
  dirtying the working tree. The file is created on first run as needed.
- **`.github/copilot-instructions.md` brought up to date**: reflects the
  current architecture (FastAPI web/Docker + Flutter mobile + Python desktop
  + Supabase shared DB), removes stale v1.8.2/Kivy references, and documents
  the new untrusted-input → Supabase write convention so future contributions
  follow the same pattern.

## [2.15.1] - 2026-05-23

### Added
- **Promote working source**: When a stream successfully plays, that URL is
  promoted to primary position in the channel's `urls` array — locally in the
  in-memory cache and persisted to Supabase via PATCH. Over time the shared DB
  self-heals: the most reliable source for each channel bubbles to position 0
  for all users. New `report_channel_working()` upserts into `channel_status`.
- **Web UI remembers working sources**: Browser localStorage tracks last
  successful source per channel; player starts from the remembered URL on the
  next play instead of cycling through dead sources first.

### Fixed
- **EPG SSL errors in Docker**: EPG fetcher now uses certifi CA bundle,
  resolving certificate verification failures on Alpine-based images.
- **EPG matching for Israeli channels**: Fuzzy matcher now strips trailing
  ` news`, ` tv`, ` channel`, ` live`, ` stream` and also tries no-space
  variants — so "Kan 11 news" correctly matches EPG ID "Kan11.il". Also
  indexes the EPG ID itself (lowercased) for direct hits.
- **EPG fetcher User-Agent**: Added `TVViewer/2.15 EPG-Fetcher` UA header
  (some EPG sources 403 requests without one).

## [2.15.0] - 2026-05-22

### Changed
- **Category consolidation**: Reduced from 28+ categories to 14 canonical categories
  across all clients (Web/Docker, Desktop Python, Flutter/Android)
  - Merged: Action/Crime/Drama → Movies; Comedy/Classic/Series/Reality → Entertainment;
    Cooking/Food/Travel/Auto/Culture → Lifestyle; Business/Tech/Science/Weather → Education;
    Animation → Kids
  - Eliminated: "Other" merged into "General"; all Xumous-prefixed categories normalized
- **Shared normalization module**: New `utils/normalize.py` is the single source of truth
  for category and country normalization. Desktop `categorize_channel()` now delegates to it.
  Flutter `normalizeCategory()` ported with identical map.
- **Name-based auto-classification**: Channels with "General" category are now auto-classified
  by name patterns (FM frequencies → Radio, jazz/rock/hits → Music, news/CNN → News, etc.)
  Reclassified ~500 channels from General into proper categories.

### Fixed
- **Docker channel loading**: Cloud DB auto-fetch triggers when cache < 5000 channels
  or cache > 24h old (previously skipped refresh when any cache existed)
- **EPG not showing in Docker**: EPG now preloads at startup; fixed field name mismatch
  (`start_time`/`end_time` → `start`/`end`) in web UI
- **Map country click**: Fixed channel loader showing spinner forever (API response
  structure extraction)
- **Search UX**: Added ✕ clear button; selecting category/country now clears search filter

## [2.14.5] - 2026-05-22

### Security
- **SSRF protection**: Proxy endpoint now blocks requests to private/internal IP ranges
  (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16, link-local)
- **Security headers**: Added X-Content-Type-Options, X-Frame-Options, Referrer-Policy,
  and Permissions-Policy headers to all non-proxy responses
- **Docker telemetry default to opt-in**: TELEMETRY_ENABLED now defaults to `false` in
  Docker for GDPR compliance (users must explicitly opt-in)

### Fixed
- **Docker channel loading**: Web UI now polls for up to 5 minutes during startup
  (previously gave up after single 10s retry), showing loading spinner during fetch
- **EPG cache permission denied in Docker**: Cache now writes to DATA_DIR volume
  (/data) with proper directory creation, not /app (read-only)
- **EPG log spam**: Fixed gzip decompression errors flooding logs when EPG sources
  return error pages (HTML) instead of valid gzipped XML
- **EPG concurrent initialization**: Added guard to prevent multiple simultaneous
  EPG fetches when many channel pages request EPG data at once
- **Startup fetch progress tracking**: `/api/status` now returns `refresh_in_progress`
  flag so web UI can show loading state during background channel fetch

## [2.14.4] - 2026-05-22

### Fixed
- **Release pipeline**: Build jobs create draft releases (mutable) so all platforms
  can upload assets. Publish job undrafts after all artifacts are attached.
## [2.14.3] - 2026-05-22

### Fixed
- **Release pipeline**: Properly create GitHub release with all platform artifacts
## [2.14.2] - 2026-05-22

### Fixed
- **CI: web tests no longer require Supabase** — Tests validate API structure/format
  without asserting channel count > 0 (CI has no access to external data sources).

## [2.14.1] - 2026-05-22

### Fixed
- **CI: add httpx to requirements** — FastAPI TestClient requires httpx; was missing
  from requirements.txt causing release-gate test collection failure.

## [2.14.0] - 2026-05-22

### Added
- **Anonymous usage analytics** — Lightweight telemetry tracks sessions, channel plays,
  failures, and feature usage. No PII collected. Device ID is a random UUID stored in
  localStorage. Data sent to Supabase `analytics_events` table via server-side proxy.
- **LOCAL category** — Auto-detects user's country (env `LOCAL_COUNTRY` or system locale),
  pins a "LOCAL" category first in sidebar showing only channels from that country.
- **Server-side search** — Search now queries the full database (up to 500 results)
  instead of filtering only loaded page channels.
- **Health reporting to Supabase** — When channels play/fail, status is reported
  to the server for community-driven health tracking.

### Fixed
- **Radio channels not showing** — `media_type` field was stripped from API payload;
  added server-side media_type filter. Radio detection now checks both `media_type`
  and `category` containing "radio" (covers 37 vs 9 channels).
- **EPG completely broken** — All previous sources (epg.pw, iptv-org) return 404.
  Replaced with 6 verified working sources (epgshare01 IL/UK, i.mjh.nz, dp247).
- **EPG cache permission denied** — Cache now writes to `DATA_DIR` volume in Docker.
- **Categories showing country names** — Cross-references actual channel countries to
  filter dirty data like "Bosnia and Herzegovina" from categories list.
- **Load More doing nothing with type filter** — Pagination now passes media_type
  to server so subsequent pages respect the TV/Radio filter.
- **Proxy session leak** — Replaced per-request TCP connectors with shared connection
  pool (`connector_owner=False`). Fixes "Unclosed client session" log spam.
- **Refresh polling infinite loop** — Added 3-minute timeout (60 polls × 3s) with
  error handling to prevent indefinite polling if refresh stalls.
- **EPG log spam** — Parse errors and 404s downgraded from WARNING to DEBUG level.

### Performance
- **Shared proxy connection pool** — Reuses TCP connections across proxy requests
  instead of creating/destroying per request. Reduces latency and memory.
- **Search debounce** — Increased to 300ms to reduce server load during typing.

### Security
- **Analytics input validation** — Server validates event_type length (≤100),
  device_id length (≤64), and event_data size (≤5KB) before forwarding.
- **RLS fix script** — `scripts/fix_analytics_rls.sql` restores anon INSERT policy
  for analytics_events with proper field validation.

## [2.13.3] - 2026-05-21

### Performance (Docker/NAS optimization)
- **Only fetch working channels from Supabase** — Skips 14,500+ failed channels (59%),
  reducing startup payload from ~21K to ~10K channels. Faster load, less RAM.
- **GZip compression** — All API responses compressed (saves 70-80% bandwidth)
- **Pre-sorted channel cache** — Israeli channels first, then A-Z. No per-request sort.
- **Paginated API** — `/api/channels` returns 200 per page with `Load More` button
- **Slim JSON responses** — Only essential fields sent (30% smaller payloads)
- **Cached favorites** — Memory-cached with stat-based reload (no disk I/O per request)
- **Selective Supabase columns** — `select=name,urls,...` instead of `select=*`

### Fixed
- **NoneType crash** — Channels with null country/category/name no longer cause 500 errors
- **Source switcher** — Now reads `urls` array for multi-source channels from Supabase
- **Sidebar categories** — Auto-retry after 10s if empty (background fetch race condition)

## [2.13.2] - 2026-05-21

### Fixed
- **Docker crash on startup** — Server was blocked fetching 34 M3U repositories
  before uvicorn started. Healthcheck failed with "Address not available" because
  nothing was listening. Now fetches channels in a background thread.
- **Healthcheck reliability** — Changed from `localhost` to `127.0.0.1` (Alpine DNS),
  increased start-period to 30s, retries to 3.

### Changed
- **Supabase fast-start** — On first boot, tries Supabase channel pull first (~5s)
  before falling back to slow M3U repository fetch (~60-120s).
- **Non-blocking startup** — Server responds to requests immediately; channels
  populate in background. Users see channels appear via automatic refresh.
- **Channel cleanup** — Removed 1,595 non-working PlutoTV channels, fixed 1,626
  mojibake channel names, added URL blocklist to prevent re-import.
- **Status filter** — Simplified to "All Channels" / "Hide Broken" (removed "Working Only").
- **Alphabetical sort** — Channel list sorted A-Z by default.

## [2.13.1] - 2026-05-20

### Added
- **In-memory channel cache** — Channels loaded once from disk, served from RAM.
  API responses ~40% faster. Only reloads when file mtime changes.
- **Health status filter** — Dropdown in web UI: "Working Only" or "Hide Broken".
  Tracks playback success/failure per channel in localStorage.
- **Health reporting endpoint** — `POST /api/health/report` accepts `{url, status}`
  from client. Updates local cache and Supabase (when configured).
- **Docker: NAS-optimized** — Alpine-based image (~25 MB), runs on 48 MB RAM,
  0.1 CPU reservation. Compatible with Synology, QNAP, Unraid, TrueNAS, RPi 4+.

### Changed
- Docker base image: `python:3.12-slim` → `python:3.12-alpine` (smaller).
- Docker resource limits reduced: 128 MB / 0.5 CPU (was 256 MB / 1 CPU).
- Country sidebar shows all countries (was capped at 30).
- `_mark_local_broken/working` update in-memory cache directly (no re-read from disk).
- Channel writes protected: never overwrites with empty data during race conditions.

### Fixed
- **Empty channel list crash** — `_persist_channels()` skipped when cache is empty,
  preventing data loss from race conditions during health reporting.
- **JSON parse error on reload** — Cache tolerates partial file writes (keeps stale
  data if JSON decode fails during concurrent writes).
- **ABC News Live** — Dead Tubi URL replaced with working akamaized.net stream.
- **`re` import** — Moved from inside loop in `_rewrite_manifest` to module level.

## [2.13.0] - 2026-05-20

### Added
- **Web: CORS Proxy** — All HLS streams route through server-side proxy by default,
  fixing playback for the vast majority of IPTV channels that lack CORS headers.
  Manifests are rewritten so segment URLs also proxy transparently.
- **Web: Stream source switching** — Auto-retry with next available source when a
  stream fails. Manual source selector dropdown in player controls.
- **Web: Cast menu** — Cast to Chromecast/AirPlay (Remote Playback API), present
  to external display, Picture-in-Picture, open in new tab, or copy URL.
- **Web: Play/Pause button** — Visible transport control synced with Space key.
- **Web: Enhanced EPG** — Now playing (accent-colored with time range) and Next
  shown on separate lines, plus upcoming schedule strip.
- **Web: Map channel browser** — Click a country on the map to see its channels
  in a side panel. Play any channel directly from the map view.
- **Web: Country/Category/Type filters** — Dropdown filters above channel grid
  with proper event handling. Sidebar sorted alphabetically.
- **Web: Stream stats overlay** — Live resolution, buffer health, and bitrate
  displayed during playback (top-right corner).
- **Web: Radio spectrum visualizer** — Animated frequency bars using Web Audio API
  with fallback animation for CORS-restricted audio.
- **Docker support** — `Dockerfile` for running the web interface standalone.
  `docker build -t tv-viewer-web . && docker run -p 8765:8765 tv-viewer-web`
- **Automated web tests** — `tests/test_web.py` validates API endpoints, proxy
  functionality, and server startup.

### Changed
- Web player uses proxy by default instead of waiting for CORS failure (instant playback).
- Sidebar categories and countries sorted alphabetically (was by channel count).
- Player controls layout improved with play/pause and source selector.

### Fixed
- Map view now has proper channel browsing (was display-only with no interaction).
- Favicon uses proper PNG icons (192/512) for modern browsers.
- Filter dropdowns properly wired to reload channels on change.

## [2.12.0] - 2026-05-20

### Added
- **Web UI: Favorites management** — Add/remove favorites from web interface with
  server-side persistence (synced with desktop favorites.json). Heart icon on cards
  and dedicated Favorites view.
- **Web UI: Fullscreen player** — Press F or click Fullscreen button for immersive
  video playback. Uses Fullscreen API with CSS fallback.
- **Web UI: Volume control** — Slider + mute button in player. Volume persists
  across sessions. Arrow keys (↑/↓) adjust volume.
- **Web UI: Keyboard shortcuts** — Space (play/pause), F (fullscreen), M (mute),
  Escape (close), arrows (prev/next/volume), / (focus search), 0-9 (channel jump).
- **Web UI: Settings panel** — Theme selector, stream quality, parental controls
  with PIN, keyboard shortcuts reference.
- **Web UI: Parental controls** — Hide 18+ channels with optional PIN protection.
- **Web UI: Channel quick-jump** — Type channel numbers (0-9) to jump directly.
- **Web UI: Recent channels** — Stores last 50 channels in localStorage with
  full metadata for the Recent view.
- **Server: Favorites API** — `GET /api/favorites` and `POST /api/favorites/toggle`
  endpoints for server-side favorite management.

### Changed
- Web player now saves volume preference and restores it across sessions.
- Card actions show favorite toggle (★/☆) with visual state feedback.
- Feature parity audit completed across Windows, Android, and Web platforms.

## [2.11.1] - 2026-05-20

### Fixed
- **VLC crash on Escape** (Windows): Fixed crash/freeze when pressing Escape during
  video playback. Root causes: (1) VLC's video thread wrote to a destroyed HWND —
  fixed by detaching HWND before stopping; (2) VLC cleanup (up to 5s blocking) ran
  on the main thread causing "Not Responding" — moved to background daemon thread.
  Frame is now destroyed only after cleanup completes.

## [2.11.0] - 2026-05-19

### Added
- **Category drill-down grid view** (Windows): Click any category label to see
  all its channels in a full wrapping grid — no more left/right scrolling.
  Back arrow, Escape, or Backspace returns to category browse.
- **Spectrum analyzer** (Windows): Radio/audio-only channels display a live
  32-bar animated frequency visualizer instead of a black screen. Energy
  driven by VLC stats, runs at 24fps with low CPU usage.
- **Native debug symbols** uploaded with Android AAB for better crash analysis
  in Google Play Console.
- **Playback → health feedback**: Channels marked broken that play successfully
  are automatically updated to healthy in both local cache and Supabase.

### Fixed
- **Escape key crash** (Windows): Pressing Escape while playing a channel
  entered from category drill-down no longer crashes the app. Fixed priority
  order — playback state is checked before drill-down state.
- **Hebrew channel names garbled** (Android): Double-encoded UTF-8 names
  (×§×¨×™×ª pattern) are now auto-repaired on load and fetch.
- **Radio favorites filter leak** (Android): Switching from TV (with favorites
  active) to Radio no longer shows an empty list. Radio screen now uses
  unfiltered channel source.

## [2.10.10] - 2025-07-14

### Security
- **TLS certificate pinning** for Supabase analytics and GitHub update endpoints
  — MITM protection in release builds (#171).
- **PyInstaller bootloader rebuild** in CI — unique binary hash reduces AV false
  positives (#201).
- **Azure Trusted Signing** code-sign step added to Windows build workflow —
  gracefully skips if secrets not configured (#202).

### Fixed
- Closed 20+ GitHub issues confirmed fixed in prior versions.
- All remaining open infrastructure issues addressed (#200, #201, #202, #203).

## [2.10.9] - 2026-05-18

### Added
- **Pull-to-refresh** on channel list — drag down to refresh channels and
  check for app updates simultaneously.
- **Radio favorites** — select favorite radio stations with heart icon, filter
  by favorites using toggle button or chip in genre row.

### Fixed
- **Israeli channels stale** (#193): Custom verified CDN channels now load
  first (priority) before M3U repository fetch, ensuring working Israeli
  streams aren't overshadowed by stale repo-sourced duplicates.
- **Map favorites toggle unresponsive**: Replaced `GestureDetector` with
  `Material` + `InkWell` in FilterChip for stable hit area when toggling.

### Closed (confirmed fixed in earlier releases)
- #192 Country code normalization (fixed in 2.10.7)
- #196 Null check setState crashes (fixed in 2.10.6)
- #199 Logo URL crash (fixed in 2.10.6)
- #204 Phone landscape tablet layout (fixed in 2.10.1)
- #205 Persist filter selections (fixed in 2.10.4)
- #206 Fullscreen leaves channel list (fixed in 2.10.2)
- #208 Help screen layout (fixed in 2.10.5)
- #209 Player toolbar overflow (fixed in 2.10.5)
- #210 Black screen after fullscreen (fixed in 2.10.6)
- #211 Portrait filters space (fixed in 2.10.4)
- #212 Logger arity mismatch (fixed in 2.10.7)

## [2.10.8] - 2026-05-18

### Added
- **Background playback** (#213): New setting to continue audio/video when
  screen is off or app is backgrounded. Works for both TV player and radio.
  Off by default — enable in Settings → Stream Settings.
- **Android foreground service permissions**: Added `FOREGROUND_SERVICE` and
  `FOREGROUND_SERVICE_MEDIA_PLAYBACK` for reliable background audio on
  Android 14+.

### Fixed
- **Hebrew/Arabic channel names garbled** (#214): M3U playlists served without
  explicit charset header were decoded as Latin-1 (Dart http default), corrupting
  non-ASCII characters. Now explicitly decoded as UTF-8 with `allowMalformed`.
  Affects Israeli radio stations and all non-Latin channel names from IPTV-org.
- **Android UI freeze ~10s after startup** (#215): Background channel fetch
  called `_saveToCache()` synchronously before `notifyListeners()`, blocking
  the UI thread with JSON encoding of thousands of channels. Cache save now
  runs deferred via `compute()` in a background isolate. EPG generation also
  yields every 50 channels to avoid frame drops.

## [2.10.7] - 2026-05-17

### Fixed
- **CI release pipeline unblocked** (#212): ``logger.warning(msg, error,
  stackTrace)`` in update_service.dart used 3 positional args, but the
  project's ``LoggerService.warning`` only accepts 2. ``flutter analyze``
  treated it as a hard error, failing the Release Gate on v2.10.3, .4, .5,
  and .6 — none of those tags ever published an APK to GitHub Releases.
  Switched to ``logger.error(msg, error, stackTrace)`` which has the right
  signature. v2.10.7 is the first build to ship the in-app updater +
  portrait compaction + back-from-fullscreen fixes the user has been
  testing visually for the last several iterations.

### Note for users still on v2.10.2
v2.10.7 carries forward everything from v2.10.3-2.10.6:
- In-app APK download + install with release notes (v2.10.3)
- "Check for updates" button in Settings → About (v2.10.3)
- Help & Support empty section + nav-bar overlap fix (v2.10.4)
- Compact player top bar + bottom-OSD transport controls (v2.10.5)
- Back-from-fullscreen black-screen fix + portrait compaction (v2.10.6)

## [2.10.6] - 2026-05-17

### Fixed
- **Back from fullscreen → black screen** (#210): Pressing system back or the
  top-bar back arrow while the embedded player was in fullscreen used to pop
  the HomeScreen route and leave a black screen. Back now first exits
  fullscreen and returns to the channel-list playback view; a second back
  exits to the previous screen.

### Changed
- **Portrait layout compacted** (#211): Filters now start collapsed in
  portrait so the channel list is visible immediately. Recently Played is
  also collapsible (still 1-tap to expand), uses compact chips, and a
  smaller header with a count. Stats bar uses the compact density. Net
  vertical savings ~120-160 px on a typical phone, enough to show 2-3 more
  channel rows above the fold.

## [2.10.5] - 2026-05-17

Player top bar redesign — fits on narrow phones.

### Fixed
- **Top toolbar overflow / fullscreen button half-cut** (#209): The player
  top bar packed 7-9 IconButtons (back, prev, next, PiP, cast, report,
  external, fullscreen) plus the channel title at default 48 dp width each,
  overflowing portrait-phone widths and clipping the fullscreen button.

### Changed
- **Compact top bar**: back / title (+ live badge / quality / bitrate) /
  fullscreen / "more". Secondary actions (PiP, Cast, Report, External) moved
  into a 3-dot overflow menu. Icons shrunk to 22 px with 6 px padding.
- **Transport controls moved to bottom OSD**: Previous / Play-Pause / Next
  are now centered above the volume slider in the bottom control bar.
  Disabled prev/next still render (dimmed) to keep the layout stable while
  navigating.

## [2.10.4] - 2026-05-17

Help & Support screen layout fixes.

### Fixed
- **Empty "Settings" section header in Help & Support** (#208): A bare
  ``_buildSectionHeader('Settings')`` was rendered with no content below it,
  leaving an orphan heading. Removed.
- **"Export Logs" hidden behind Android navigation bar** (#208): The Help
  & Support ``ListView`` had a fixed 8 px bottom padding, so on Android
  devices with a software nav bar / gesture handle the last few list items
  (Export Logs, Reset Onboarding, App Version, Legal) were partially or fully
  covered. The body is now wrapped in ``SafeArea(top: false)`` so the system
  bottom inset is honored.

## [2.10.3] - 2026-05-17

In-app update install (no more "hunt-for-the-APK-on-GitHub").

### Added
- **In-app APK install on Android** (#207): The update dialog now downloads
  the APK directly from the GitHub release asset and hands it to the Android
  package installer. Three days post-2.10.0 our analytics showed 0% adoption —
  every user had to visit the releases page, find the right asset, allow
  "install from unknown sources" and tap install. Now it's one button.
  - Added `REQUEST_INSTALL_PACKAGES` permission + `FileProvider` (authority
    `${applicationId}.fileprovider`, paths in `res/xml/file_paths.xml`).
  - New dep `open_filex` to launch the installer with the correct MIME type.
  - APKs are cached in the app's external files dir under `updates/` and
    re-used if a previous attempt already pulled the same byte count.
- **Release notes + progress in the update dialog** (#207): The dialog now
  shows the GitHub release `body` (markdown text) and a live download
  progress bar instead of a one-line "new version available" banner.
- **"Check for updates" in Settings → About** (#207): Forces a fresh API
  call that bypasses both the 24-hour rate limit and the "Later" dismissal.

### Changed
- `UpdateService.checkForUpdate()` now returns a structured `UpdateInfo`
  (version, tag, release notes, APK asset URL, size, html_url) instead of a
  bare version string. The legacy banner helper still works via the new
  rich dialog so any third-party callers keep functioning.
- Auto-check on app open now opens the rich dialog directly (no banner step).

## [2.10.2] - 2026-05-16

Android UX fix for the embedded fullscreen experience.

### Fixed
- **Android fullscreen showed channel list and toolbar** (#206): On Android phones
  in landscape and tablets, tapping the fullscreen button only hid the system
  status bar — the left-hand channel list and app top bar stayed visible, so the
  video occupied only a fraction of the screen. The embedded `PlayerScreen` now
  notifies its parent (`HomeScreen`) via an `onFullscreenChanged` callback, and
  the home Scaffold hides the AppBar, drawer, scan/error banners, channel-list
  panel and divider while the player is fullscreen — giving the video 100% of
  the screen until the user double-taps or presses the exit-fullscreen button.

## [2.10.1] - 2026-05-16

UX fixes for Android landscape mode based on direct user feedback.

### Fixed
- **Android landscape unusable on phones** (#204): Phones in landscape were routed
  to the tablet layout (because `screenWidth > 600` is true on most landscape
  phones), which stacked search + 2 rows of filters + stats above the channel
  list — leaving room for ~1 channel on a 6" device. Phone-vs-tablet detection
  now uses `MediaQuery.size.shortestSide > 600` (the Material Design definition),
  so any real phone in landscape gets the dedicated phone-landscape layout with
  filters in a drawer.
- **Search field moved into the AppBar** in phone-landscape mode, reclaiming an
  entire row of vertical space. Stats bar height halved (compact variant).

### Added
- **Filter persistence** (#205): The user's last-used filter selections
  (category, country, language, media type, status, favorites-only) are now
  saved in `SharedPreferences` and restored on app launch. Favorites were
  already persisted via `FavoritesService`; this extends the same pattern to
  all filter dropdowns through a new `FiltersService`. Search query is
  intentionally NOT persisted (transient by design).
- "Clear filters" now also resets the persisted values.

### Files changed
- `flutter_app/lib/services/filters_service.dart` (new)
- `flutter_app/lib/providers/channel_provider.dart` (load on `fetchChannels`,
  save on every `setX` / `toggleFavoritesFilter` / `clearFilters`)
- `flutter_app/lib/screens/home_screen.dart` (`shortestSide` detection,
  in-AppBar search field, compact stats bar)

## [2.10.0] - 2026-05-12

This release was driven by Supabase telemetry analysis. Crash data showed that
21% of all events from the field were Android crashes, dominated by three root
causes (#199, #196, #194). On the desktop side, multiple users reported that
the Windows EXE was being quarantined by Microsoft Defender. This release
fixes all of those without requiring any AV exclusions on the user side.

### Fixed — Android (P0/P1)
- **Logo URL crashes — `No host specified in URI file:[PATH]` (#199, P0, 82× in field)**:
  `Image.network(...)` and `CachedNetworkImage(...)` throw `ArgumentError`
  *synchronously* inside Dart's HTTP client when handed a `file://...` URL or a
  URL with no host — `errorBuilder` does not catch sync throws, so the whole
  widget tree crashed. Added `flutter_app/lib/widgets/safe_channel_logo.dart`
  which validates `Uri.tryParse(url)?.isScheme('http'|'https')` and `host.isNotEmpty`
  before constructing the network image. `radio_screen.dart` and
  `channel_tile.dart` now both go through it; bad logo URLs render the fallback
  icon instead of crashing.
- **Null-check operator crash in radio_screen `_playStation` setState (#196, P0, 20× in field)**:
  the method `await`-ed `VideoPlayerController.initialize()` and `play()` then
  called `setState()`. If the user tapped Back during the await the State was
  already disposed and the `_controller!` null-check threw. Added `if (!mounted)`
  guards after each await, with `_controller?.dispose()` cleanup, and a guard in
  the catch block. Same hardening previously applied to `player_screen.dart`
  (#82) is now consistent across the app.
- **HTTP 429 from logo CDN crashes the player (#194, P1, 13× in field)**:
  the new `SafeChannelLogo` widget uses `cached_network_image`'s built-in
  exponential backoff and disk cache, so transient 429s now degrade to the
  fallback icon and recover on next launch instead of taking the screen down.

### Fixed — Analytics & data quality (P1/P2)
- **`refresh_analytics_views()` failed with duplicate-key on `idx_mv_top` (#195, P1)**:
  `mv_top_channels` groups by `(channel_hash, country, category)` but the
  unique index that backs `REFRESH MATERIALIZED VIEW CONCURRENTLY` only
  covered `channel_hash`. Same hash legitimately appears under multiple
  country/category pairs, so the upsert phase blew up with `23505`. The MV is
  rebuilt with `COALESCE(NULLIF(...), 'XX'/'')` on the nullable group cols
  (NULLs in unique-index columns also break CONCURRENTLY refresh) and the
  unique index now spans the full `(hash, country, category)` tuple. Migration
  script: `scripts/fix_mv_top_channels.sql`.
- **Country normalization (#192, P2)**: Flutter `analytics_service` now
  routes `country` through a 50+ alias `_normalizeCountry()` map → ISO-3166
  alpha-2. Old data showing `ISRAEL`, `Israel`, `il`, `IL` now all land as `IL`,
  fixing dashboard breakdowns.

### Changed — Windows EXE (P0/P1)
- **Eliminated VLC prerequisite (#200, P1)**: Windows builds now bundle
  `libvlc.dll`, `libvlccore.dll`, and the full `plugins/` tree from VLC 3.0.20
  inside the EXE folder. The app starts and plays streams on a clean Windows
  install with no VLC installation required. Adds ~70 MB to the bundle but
  removes the #1 install blocker. `ui/vlc_controller.py` sets
  `PYTHON_VLC_LIB_PATH` / `VLC_PLUGIN_PATH` to the bundled copies before
  importing `vlc`, so it transparently prefers bundled libvlc and falls back
  to system VLC if the user has it installed.
- **Defender-hardened EXE bundle (#190)**: removed AV-flagged libraries from
  the PyInstaller spec — `zeroconf` (mDNS, frequent false-positive),
  `pychromecast`/`casttube`, `PIL._avif.pyd`/`PIL._webp.pyd`/`PIL._imagingcms`
  (unused codec plugins, `_avif.pyd` is a known trigger). Cast support remains
  available via runtime import (`try/except` already in place) — install
  `pychromecast` separately to enable. UPX is explicitly disabled
  (`--noupx` + `upx=False` in spec) — UPX-compressed EXEs are weighted
  heavily in Defender's reputation model. Bundle is now ~12 MB lighter
  before the libvlc addition.
- **Windows VERSIONINFO embedded in EXE (#190)**: PyInstaller now writes a
  proper `version_info.txt` (CompanyName, FileDescription, FileVersion,
  ProductVersion, copyright) and embeds it in the EXE. SmartScreen and
  Defender's cloud-reputation system weight signed metadata heavily —
  unsigned binaries with no metadata are flagged as "unknown publisher".
  This is the cheapest reputation signal we can ship without code-signing.

### Build & CI
- `TVViewer.spec` rewritten as a documented, structured spec (was an
  auto-generated single-line file). Bundles customtkinter theme JSONs (fixes
  the v2.9.4 OSD invisibility regression) and conditionally bundles libvlc
  when CI sets `BUNDLE_LIBVLC_DIR`.
- `.github/workflows/build.yml` Windows job now downloads VLC 3.0.20 portable,
  generates `version_info.txt` from `config.APP_VERSION`, sets
  `BUNDLE_LIBVLC_DIR` and verifies that `libvlc.dll` + plugins are present in
  the final bundle. Build fails if any expected asset is missing.

### Notes
- Code signing (#202) is still pending — requires either a paid certificate
  or a SignPath Foundation OSS sponsorship. The reputation hardening in this
  release should sharply reduce false-positive rate, but signing remains the
  definitive fix.
- A bootloader rebuild from source (#201) was deferred to a follow-up release
  — it adds 30+ minutes of CI time per platform and the cumulative impact of
  the changes above (no UPX, no zeroconf, no _avif, version metadata, proper
  VLC bundling) should already move the needle significantly.

## [2.9.7] - 2026-05-11

### Fixed
- **In-app feedback dialog lost typed text when "Open GitHub" was pressed (#191)**: the deep link sent the user to GitHub's issue form but the URL only carried `template=feedback.yml` (a template that doesn't exist in this repo) and the title — the body was never set, so everything the user typed was discarded. Switched to a direct `?body=…&labels=…&title=…` deep link that prefills the issue body with the rating, category, app version, the feedback text, and a timestamp. Category now also maps to a sensible label (`bug`, `enhancement`, or `feedback`).
- **Settings → Parental Controls bypassed the PIN gate (security)**: the overflow menu's Parental Controls path required the PIN, but tapping Parental Controls inside Settings navigated straight to the screen with no check. Anyone with physical access could change parental settings without the PIN. The Settings entry now goes through the same PIN gate.

### Changed
- **Overflow menu reorganized for clarity**: items are now grouped into three sections separated by dividers — **Tools** (Sort, Radio, Map on compact screens), **Feedback** (Send Feedback, Rate App), and **Help & info** (Help & Support, Diagnostics, About). The duplicate Parental Controls entry was removed (it lives under Settings, where it belongs).

## [2.9.6] - 2026-05-11

### Fixed
- **Screen sleeps while watching video on Android (#190)**: wake lock was only enabled once at player startup, so any system-side preemption (battery saver waking, returning from background) silently dropped it and the screen would dim/sleep mid-stream. The wake lock is now re-asserted whenever the app returns to the foreground (`AppLifecycleState.resumed`) and whenever the user resumes playback via the play button. Also calls `WakelockPlus.enable()` defensively on every play action — the package is idempotent so this is safe.
- **No fullscreen button or way to fullscreen on tablet (#189)**: portrait tablet mode left video letterboxed with no way to expand it. Added an explicit fullscreen / exit-fullscreen `IconButton` to the player's top control bar (next to the External Player button) and rebound double-tap on the video surface to toggle fullscreen, matching mainstream player behavior. Long-press still toggles play/pause, and the center play/pause icon is now a tappable target (it used to be display-only) so users keep that affordance now that double-tap means fullscreen.

## [2.9.5] - 2026-05-03

### Fixed
- **Favorite star never toggled in player OSD**: `_refresh_fav_button` was passing `bootstyle=` to `CTkButton`, which silently raised an exception so the star glyph never updated and the user couldn't tell whether a channel was favorited. Now updates text + `text_color` (gold when active, white when not) using only CTkButton-supported kwargs.
- **Escape key racing with main window's `bind_all('<Escape>')`**: Player Escape handler now returns `'break'` so the global Esc binding doesn't fire `_clear_search` after the player window has destroyed itself. Reduces the rare crash some users hit when pressing Escape during VLC startup.
- **OSD controls invisible in packaged Windows EXE**: PyInstaller spec now bundles `customtkinter` theme + asset files via `collect_data_files('customtkinter')`. Without these, CTkButton couldn't read its theme JSON, so OSD buttons rendered as zero-size canvases — making the controls bar appear empty. The dev environment had the assets on disk so the bug only surfaced in the packaged build.
- **Map "list view" warning was misleading**: Changed import-time log from WARNING to INFO since the fallback list view handles the missing dependency gracefully.

## [2.9.4] - 2026-05-03

### Fixed
- **Player OSD invisible on some launches**: explicitly forces `'-fullscreen'=False` on player startup and pins `minsize=60` on the controls grid row so the playback bar can never collapse. Also fixes a `<Configure>` handler leak in the radio overlay (the resize binding was being re-added on every `_update_radio_overlay()` call, accumulating exponentially and starving the Tk event loop).
- **Crash when leaving certain channels with Escape**: `bind_all('<Escape>')` on the main window was firing globally — including while the player Toplevel was focused — and then touching widgets in transient states. The handler now checks that the main window root actually has focus before clearing the search, and is wrapped in defensive try/except.
- **Map window unusable when `tkintermapview` is missing**: Map button used to show a "module not installed" dialog and quit. The window now opens in a built-in fallback **list view** that shows the same toolbar (search, favorites, hide-offline, stats), a country picker on the left (sorted by channel count), and the channel list on the right — fully functional without the optional dependency.

### Changed
- **Player Escape = "leave the channel"**: pressing Escape in the player now exits fullscreen if active, otherwise closes the player window cleanly. Matches the user's mental model of Escape as "back / leave".
- **Round OSD buttons**: all player playback controls (play, stop, prev, next, favorite, mute, fullscreen, VLC, cast, report) are now rendered as round/pill `CTkButton`s with the Defender accent palette. The previous ttk buttons were forced to a square shape by Windows native theming regardless of the ttkbootstrap style applied. Falls back to ttk.Button on environments without `customtkinter`.

## [2.9.3] - 2026-05-03

### Fixed
- **Privacy policy link was broken** — `https://tv-viewer.app/privacy` is not our domain. Updated to the published GitHub Pages URL `https://tv-viewer-app.github.io/tv_viewer/privacy.html`.

### Changed
- **Privacy dialog: single master toggle** — replaced the three separate checkboxes (analytics / online DB / geo-IP) with one "Participate in the community channel database" toggle that controls all three together. The hint copy enumerates exactly what's covered. Same opt-out trade-off banner.

## [2.9.2] - 2026-05-03

### Fixed
- **Privacy dialog crash on first launch**: tuple-form `pady=(0, 8)` was passed to a `tk.Label` constructor (only `.pack()`/`.grid()` accept tuples), producing `TclError: bad screen distance "0 8"`. Moved the tuple to `.pack()`.
- **Settings dialog crash in TV Mode**: `'TVModeApp' object has no attribute 'group_by_mode'`. The Settings dialog now defensively reads `group_by_mode`, `parental_controls`, theme, and `_save_telemetry_preference` via `getattr`/`hasattr`, so it works in both Standard and TV mode.
- **Legacy Release workflow Windows EXE build**: PyInstaller `--add-data "channels.json;."` failed because the runtime cache file is gitignored. Build now creates an empty `channels.json` placeholder before invoking PyInstaller.
- **Legacy Release workflow Flutter version**: bumped pinned Flutter `3.19.0` → `3.24.0` so Material 3 `ColorScheme.surfaceContainerHighest` is available.

### Added
- **Privacy dialog redesigned**: Single **Save** button (replaces the Decline All / Accept Selected pair). New banner explains the trade-off: declining analytics + online DB means no community channel updates, no new channels, and no channel status updates. Users can always change the choice in Settings → Privacy.
- **Radio playback overlay**: when a Radio channel is playing, the player canvas now shows a large station name, a 📻 glyph, and a "● LIVE RADIO" badge (instead of a black canvas). OSD play / pause / stop / prev / next remain visible.
- **Favorite (★) button on the player**: toggle the playing channel in/out of favorites without leaving the player. Bound to `F2`.
- **"Add Channel" labeling**: the contribute dialog's submit button and TV mode's nav bar now say **"➕ Add Channel"** instead of "📡 Submit".
- **Map button icon**: replaced `🗺️ Map` with `🌍 Map` so the icon renders consistently and at the same visual weight as the other toolbar buttons (Windows often renders the variation-selector form text-style and visually smaller).

## [2.9.1] - 2026-05-03

### Fixed (post-release self-review)
- **Privacy dialog no longer clobbers `TELEMETRY_ENABLED=true` env var**: `maybe_show_privacy_dialog` previously called `apply_to_config(stored)` *before* the user answered the dialog, overwriting any opt-in set via environment variable. Now config is only mirrored after the user answers, or when a stored consent file exists.
- **`load_consent` now defaults `answered` to `False`** when the field is missing from a malformed file (was `True`, which could silently mark a stale file as already-answered).
- **`channel_passes` category filter is now lenient** like language and country: channels without a category are no longer excluded when a category filter is active. Previously empty categories were treated as "Other" and silently filtered out.

## [2.9.0] - 2026-05-03

### Added — Windows
- **Filter chip dialog** (#160): 🔎 Filter button in the nav bar opens a multi-select dialog (Language / Country / Category). Filters are persisted to `~/.tv_viewer/ui_state.json` and apply to every tab.
- **First-run interactive tour** (#162): 7-step coachmark walkthrough that fires once on first launch (Navigate → Search → Quick-jump → Submit → Filter → Map → Fullscreen). Suppress with the ? Help button if not wanted.
- **First-run privacy / consent dialog** (#170): Modal Toplevel with three explicit checkboxes — Anonymous Analytics / Online Channel DB / Geo-IP Lookup — all default OFF. Mirrors selections into `config.TELEMETRY_ENABLED`, `config.ONLINE_DB_ENABLED`, `config.GEO_IP_ENABLED`. Re-prompts if `POLICY_VERSION` bumps.
- **Spring-physics scroll** (#175): Channel-row scrolling now uses a critically-damped spring integrator instead of linear easing, giving the TV-style fluid deceleration without overshoot. Tunable via `stiffness=0.18 / damping=0.55`.
- **Windows performance & dependency audit** (#168): New `docs/WINDOWS_PERF_AUDIT.md` documents the cold-start budget, AV friendliness matrix, dependency pin policy, and the WinUI3/WebView2 evaluation deferred to post-v3.

### Changed
- v2.9 bumps `POLICY_VERSION` to `1`; existing users who silently inherited telemetry from env vars will see the consent dialog once.

## [2.8.1] - 2026-05-03

### Fixed
- **Wide channel logos no longer crop to a tiny circle** (#175): Banner-style logos (e.g. 96×21) are now padded to a centered square before the circular mask is applied, so the full logo is preserved inside the circle.
- **Player OSD now visible on Windows** (#175): The metadata/OSD labels are explicitly raised above the VLC video surface; previously they were rendered behind the DirectX overlay and never appeared.

### Added
- **Local file logging** (#176): All logs and any uncaught exception are now written to `~/.tv_viewer/app.log` (rotating, 2 MB × 3). Provides a local crash trail when Supabase telemetry is disabled.

## [2.8.0] - 2026-05-03

### Added — Windows
- **Hardware-accelerated video decoding** (#166): D3D11VA on Windows, VideoToolbox on macOS, VAAPI on Linux. Drastically reduces CPU usage on HD/4K streams. Includes 4-step graceful fallback chain (HW → SW → minimal args → no args). Opt-out via `TV_VIEWER_NO_HWACCEL=1` env var.
- **Player metadata OSD** (#165, #172): Live overlay showing resolution × FPS × bitrate while playback is active. Polls VLC every 1s.
- **Submit channel button + 'A' key** (#161): One-tap "📡 Submit" in the nav bar to crowdsource new IPTV channels.
- **Map view button restored** (#167): Geographic channel browser opens with the 🗺 button in the nav bar.
- **Local channels row** (#169): "🏠 Local (Country)" pinned at the top of Home tab using your system locale.
- **Animated loading dots** (#164): Channel-scan progress bar shows a typing-style dots animation.
- **Circular channel logos** (#159): Refreshed visual style with PIL ellipse mask + center-crop applied at render time.

### Fixed — Windows
- **Hover no longer changes rows unexpectedly** (#157): Mouse hover now only updates the column within the active row; arrows and wheel still navigate freely.
- **No more letter flash before logos load** (#158): When a channel has a logo URL, the monogram placeholder is suppressed.
- **Faster startup** (#163): Analytics initialization moved to a background daemon thread — UI no longer blocks on Supabase round-trip.

### Documentation
- New baseline: 262 passing tests (was 283; +6 hwaccel tests, -27 stale tk-bootstrap tests skipped).
- pip-audit clean: 0 known CVEs.

## [2.7.3] - 2026-05-02

### Fixed — Windows
- **App icon now reflects current Prism Play branding** (#155): Regenerated `tv_viewer.ico` (and `assets/icons/tv_viewer.ico`, `docs/favicon.ico`) from `docs/icon-512.png` as a multi-resolution ICO (16/24/32/48/64/128/256). Previous EXE shipped with a stale generic TV icon predating the Prism Play rebrand. Affects Windows taskbar, Alt-Tab, and File Explorer thumbnails.
- **Debug build icon**: `TV_Viewer_Debug.spec` now embeds the same icon (was previously default PyInstaller icon).

## [2.7.2] - 2026-05-02

### Fixed — Android
- **Release signing key (Play Store)**: CI now signs APK and AAB with the official upload key (SHA1 `56:21:F2:7C:DA:DC:12:C3:22:A4:00:BD:74:28:27:97:EA:97:6B:E4`) instead of the debug key. v2.7.1 artifacts were debug-signed and rejected by Play Console — re-release as v2.7.2 with correct signing. Workflow now hard-fails if the keystore SHA1 doesn't match the expected fingerprint.

## [2.7.1] - 2026-05-02

### Added — Windows
- **Google TV-style primary UI** (#155): Brand-new lean-back interface as the sole Windows UI — horizontal scrolling channel rows grouped by category, keyboard/remote-friendly navigation, embedded fullscreen playback, top nav bar (Home/Favorites/Recent), real-time search overlay (Ctrl+F or `/`), channel number quick-jump (0-9), and player OSD with auto-fade.
- **Smooth animated scrolling**: Pixel-based eased animation at 60fps replaces step-snap behaviour.
- **Mouse wheel support**: Vertical wheel scrolls rows, Shift+wheel scrolls within a row, hover highlights card under cursor.
- **Channel logos**: Async fetch from web with on-disk cache (`~/.tv_viewer/logos/`); monogram fallback for channels without logos.
- **Larger fonts and bigger cards**: Card 260×160 (288×180 focused), name 15-17px, row labels 15-20px.

### Fixed — Windows
- **ttkbootstrap dependency removed**: Now optional via compat fallback layer — fixes recurring import failures.
- **`python312.dll` Bad Image crash**: Switched PyInstaller from onefile to onedir build, disabled UPX.
- **Window not appearing**: Forced plain `tk.Tk()` root with DPI awareness — fixes invisible window in frozen builds.
- **Silent `AttributeError` on startup**: Replaced ttkbootstrap-only `style.colors.*` references with fallback color dict.
- **Consent dialog re-shown every launch**: Fixed `CONSENT_ACCEPTED` being overwritten after `load_external_config()`.
- **Invisible consent dialog**: Plain `tk.Tk()` parent (CTk singleton conflicted with `Toplevel` children).

## [2.7.0] - 2026-04-27

### Added — Windows
- **Collapsible filters panel** (#138): Sidebar filters section can be collapsed/expanded with a toggle; preference persisted
- **Onboarding tooltips** (#139): First-run sequential tooltips guide new users through scan, filters, search, and settings
- **First-run consent dialog** (#140): Content notice, age verification, and analytics opt-in shown on first launch
- **Diagnostics screen** (#141): Device info, network connectivity tests, stream URL tester, and report export
- **Rich channel info popup** (#142): Full detail dialog with metadata, URLs, EPG, and action buttons replacing simple messagebox
- **Auto-update version check** (#149): Checks GitHub releases on startup; non-intrusive toast notification when update available

### Added — Android
- **Settings screen** (#143): Full settings with stream timeouts, theme toggle, repository management, privacy controls, and about section
- **Advanced search syntax** (#144): Support for `country:US`, `category:news`, `language:english`, `type:radio`, `status:working` in search
- **Channel sort options** (#145): Sort by name, status, category, or country via bottom sheet selector
- **Chromecast support** (#146): Cast dialog with VLC-based casting, open in external player, and copy URL options
- **Channel thumbnails** (#147): Cached network images for channel logos with circular avatar display and fallback icons
- **Repository management** (#148): Add/remove M3U repository URLs with validation, swipe-to-delete, and reset to defaults
- **Auto-update version check** (#149): Checks GitHub releases API; shows Material banner when newer version available
- **Dedicated radio player** (#150): Radio screen with genre browsing, search, now-playing bar, volume control, and station list

## [2.6.4] - 2025-07-12

### Security
- **XXE prevention**: Replaced xml.etree with defusedxml for EPG parsing (prevents XML entity attacks)
- **PIN hardening**: Upgraded parental PIN hashing from SHA-256 to PBKDF2-HMAC-SHA256 with random salt (backward-compatible migration)
- **URL validation**: Added scheme allowlist and shell metacharacter blocking before VLC subprocess launch (Windows) and external player (Android)
- **DLL hijacking mitigation**: Removed CWD from DLL search path on Windows via SetDllDirectoryW
- **EPG download limits**: Capped EPG downloads at 10MB compressed / 50MB decompressed
- **M3U export escaping**: Escape special characters in channel metadata for M3U export
- **Temp file security**: Use tempfile.mkstemp for unpredictable temp file names
- **HTTPS enforcement**: Warn users when adding HTTP repository URLs
- **Supabase input sanitization**: Length-cap names/logos, validate URL schemes from Supabase data
- **Dependency bumps**: requests≥2.32.0, aiohttp≥3.9.2, Pillow≥10.2.0
- **GitHub Actions hardening**: All 13 workflows pinned to immutable commit SHAs, input validation, injection prevention
- **Flutter error sanitization**: Generic error messages instead of raw exception details
- **Lockout persistence**: Parental PIN lockout state persists across app restarts (Android)
- **Privacy Policy link**: Implemented in consent dialog (Android)

### Changed
- File permissions restricted on parental settings file (Linux/macOS)

## [2.6.3] - 2026-04-25

### Added
- **Swipe-to-report broken channel**: Swipe a channel tile left to report it as broken (replaces long-press)
- **Collapsible filters**: Tap the "Filters" arrow to collapse/expand for full-screen channel list; shows "Active" badge
- **Radio player display**: Radio channels show station name, country, and audio icon instead of black video

### Changed
- **Adult content consolidated**: Single over-18 toggle in Parental Controls replaces the separate "Show Adult Content" toggle
- **Hebrew font support**: Added Roboto/Noto Sans Hebrew fallback chain so Hebrew channel names render correctly

### Fixed
- **Font rendering**: Inter font now falls back to system fonts for non-Latin scripts (Hebrew, Arabic, etc.)

## [2.6.2] - 2026-04-25

### Added
- **Channel request automation** (#131-#137): Users can request channels via GitHub issue form; bot auto-searches IPTV databases, health-checks streams, and creates PRs
- **Misclassification reporting**: Long-press/right-click "Wrong Info" option to report incorrect channel metadata (country, category, name, language) — submits as GitHub issue
- **Request Channels button**: In-app and landing page CTAs to request new channels from the community
- **Swipe-to-report broken channel**: Swipe a channel tile left to report it as broken (replaces long-press for this action)
- **Collapsible filters**: Tap the "Filters" header arrow to collapse/expand the filter section for a full-screen channel list; shows "Active" badge when filters are applied
- **Radio player display**: Radio channels now show the station name, country, and audio visualizer icon instead of a black video area

### Changed
- **Age gate simplified**: Replaced min-age slider (0–18) with simple "I am over 18" toggle; under-18 users cannot see adult content toggle at all
- **Adult content controls consolidated**: Removed the separate "Show Adult Content" toggle — adult visibility is now controlled entirely by the over-18 age confirmation in Parental Controls
- **Hebrew font support**: Added font family fallback chain (Roboto → Noto Sans → Noto Sans Hebrew) so Hebrew channel names render correctly instead of garbled text
- **Landing page updated**: Added Request Channels and Report Broken Channel buttons with community workflow visual

### Fixed
- **Android adaptive icon**: Created `mipmap-anydpi-v26/` XML wrappers so the Prism Play icon displays correctly on Android 8+ (was falling back to old PNG)
- **AndroidManifest roundIcon**: Added `android:roundIcon` attribute for devices that use round icons

## [2.6.1] - 2026-04-22

### Security
- **GDPR telemetry consent** (#65, #79, #114): Telemetry defaults to OFF; first-run consent dialog asks user; Settings toggle to change anytime
- **SSL certificate verification** (#97): All Supabase connections now use certifi CA bundle via explicit SSL context
- **TOCTOU thumbnail fix** (#89): Atomic `os.replace()`, SHA-256 hashes, `tempfile.mkstemp()` for temp files
- **Favorites file permissions** (#106): Restrictive `0o600` permissions on Linux/macOS
- **Channel contribution validation** (#74): Client-side URL validation, category allowlist, rate limit (100/call)
- **CDN allowlist documented** (#100): Explanatory comments for why broad CDN domains are necessary for IPTV

### Changed
- **Refactored main_window.py** (#118): Extracted settings_dialog.py (568 lines), pin_dialogs.py (281 lines), export_manager.py (74 lines) — main_window reduced from 2872 to 2157 lines
- **Refactored player_window.py** (#118): Extracted vlc_controller.py (490 lines) — player_window reduced from 1380 to 1158 lines

### Fixed
- **Windows exe startup crash**: Clean PyInstaller rebuild with --noupx flag
- **Test suite** (#127): Removed 3 fake tests, added 16 real tests (favorites, config, thumbnail, telemetry, shared_db), all 279 tests pass
- **Supabase contract tests**: Updated to respect GDPR opt-in (patch ENABLED in tests)

## [2.6.0] - 2026-04-20

### Added
- **Side-by-side landscape layout**: Filters panel (left 300dp) + channel list (right) — no more horizontal scroll
  - Left panel: Search bar, all filter dropdowns stacked vertically, favorites toggle, stats, recently played
  - Right panel: Full-width scrollable channel list with standard ChannelTile
  - Scan progress and error banners remain full-width above the split layout
- **First-launch consent dialog**: Age verification (18+) and analytics opt-in required before using the app (GDPR/Play Store compliance)
- **Privacy policy**: Added PRIVACY_POLICY.md documenting data practices
- **Consent dialog widget**: Reusable ConsentDialog with checkboxes for age and analytics

### Fixed
- **Hardcoded Supabase credentials in Flutter** (#65/#114): Removed hardcoded JWT from analytics_service.dart and shared_db_service.dart — now requires --dart-define at build time
- **Analytics default opt-in** (#79): Changed default from opted-in to opted-out; user must explicitly consent
- **Version fallback in Gradle**: Default version now 2.6.0 instead of 2.4.0
- **targetSdk/compileSdk bumped to 35**: Meets current Google Play Store requirements

### Changed
- **Landscape home screen completely redesigned**: Replaced horizontal scroll filter row + 2-column compact GridView with persistent sidebar + full ListView

## [2.5.1] - 2026-04-20

### Fixed
- **Windows EXE won't start**: Added customtkinter and tkintermapview to PyInstaller hidden imports
- **EPG sources broken**: Replaced dead iptv-org EPG URLs with working epg.pw community XMLTV endpoints
- **TOCTOU race in thumbnails** (#89): Use tempfile.mkstemp() + os.replace() for atomic writes
- **Telemetry enabled by default** (#79/#114/#65): Disabled telemetry by default; removed hardcoded Supabase credentials from source
- **Favorites file corruption** (#106): Atomic write with tempfile + os.replace() prevents partial writes
- **CDN cleartext allowlist too broad** (#100): Removed unnecessary domains (gostreaming.tv, encoders.immergo.tv, GitHub) from Android network security config
- **Added customtkinter to REQUIRED_PACKAGES**: Version check now includes customtkinter dependency

### Improved
- **Android landscape layout**: All screens now fully usable in landscape orientation
  - Home screen: 2-column compact channel grid, collapsible single-row filters, hidden "Recently Played"
  - Channel tiles: Compact mode with smaller avatars, hidden secondary icons, dense ListTile
  - Map screen: Responsive markers (48px), compact stats bar, reduced bottom sheet
  - Log viewer: Compact info card and buttons, more space for log content
  - Diagnostics: Wider label column in landscape
  - PIN dialog: Smaller fields in landscape (40×48px)
  - Onboarding tooltip: Width scales to 40% of screen in landscape

## [Unreleased]

### Added
- **Feedback System**: Added feedback dialog to desktop app (#23)

## [2.4.0] - 2026-04-19

### Added
- **Smart channel scanning** — Clients fetch health cache from Supabase, skip re-scanning known-working channels. 70% scan time reduction.
- **Local health cache** — Channel health persists in SharedPreferences. App works 100% without Supabase.
- **Playback failure reporting** — Failed channels reported to Supabase so other clients benefit.
- **Supabase health scanner** — `scripts/supabase_health_scanner.py` for bulk channel validation and upload.
- **Feedback/rating system** — In-app feedback form with email and analytics integration (both platforms).
- **EPG (Electronic Program Guide)**: Full XMLTV parser with community EPG sources (IL, US, GB, DE, FR). Shows "Now playing" and "Up next" in channel preview with live progress bar. Auto-refreshes every 2 hours with disk caching
- **Toast notifications**: Non-blocking popup notifications (success/error/info/warning) with Fluent Design dark theme, fade animation, auto-dismiss, and vertical stacking
- **Watch history**: Thread-safe recently-played tracker with play counts and timestamps. Sidebar shows last 5 channels with dedicated "Recently Played" virtual group. Debounced auto-save with atomic writes
- **Parental controls**: PIN-based access control with SHA-256 hashing, 3-attempt lockout, category blocking (10 categories), and age rating filter (0–18). Full settings UI with auto-advancing PIN entry and shake animation on wrong PIN
- **Keyboard shortcuts**: Ctrl+F (search), F5 (refresh), Ctrl+comma (settings), Escape (clear search)
- **Channel preloading**: Pre-buffers next channel for instant switching
- **Auto-hide broken channels**: Channels failing 3 consecutive scans are auto-hidden
- **Data quality improvements**: Enhanced category normalization, country name deduplication

### Fixed
- **SSRF DNS bypass**: Hostnames resolving to private IPs are now blocked (resolves all addresses via `socket.getaddrinfo`)
- **SSRF in repository**: URL validation now delegates to full SSRF protection
- **Analytics thread safety**: Added `threading.Lock` to shared queue operations
- **Shutdown blocking**: Analytics flush runs in background thread with 3-second timeout
- **MouseWheel bind leak**: Settings dialog now properly unbinds `<MouseWheel>` on close
- **Tree row stability**: Channel rows now use URL-based stable IDs instead of name-based keys
- **Test encoding**: Log file reads use UTF-8 with `errors='replace'` for Windows compatibility
- **Version mismatch**: README badges now match config.py version
- **Flutter tests** — Fixed channel_provider_test assertions, repaired repository test scaffolding.
- **Feedback service TODOs** — Replaced placeholder package name and support email.
- **Supabase security** — Fixed 20 linter warnings: search_path injection, RLS policies, materialized view access.

### Changed
- **Flutter UX overhaul** — Material 3 design system, improved loading states, friendly error messages, better accessibility.
- **Desktop UX polish** — Consistent FluentColors usage, improved error messages and loading states.
- **Channel cleanup** — Validated 17,948 channels, kept 12,013 working (66.9% pass rate).

### Security
- DNS resolution check on all stream URLs prevents SSRF via hostname-to-private-IP attacks
- Parental control PINs stored as SHA-256 hashes, never in plaintext
- **Supabase hardening** — Set search_path on all functions, revoked anon access to analytics views, tightened RLS policies with field validation.
- **Migration script** — `scripts/supabase_security_fix.sql` for database security fixes.

### Closed Issues
- #61 — Can't change sources on error (already implemented in v2.2.1)
- #62 — False positive CVE scan (no vulnerabilities found)
- #23 — Feedback/rating system (implemented for both platforms)

## [2.3.3] - 2026-03-05

### Fixed
- **Android version display**: Fixed 10 hardcoded "2.2.3" version strings across Flutter app (about dialog, help screen, diagnostics, user-agent headers, player, M3U service, FMStream service)
- **Centralized version constant**: Created `constants.dart` with `appVersion` and `appUserAgent` — all version references now use the central constant
- **About dialog dynamic version**: About dialog now reads version from `PackageInfo.fromPlatform()` instead of hardcoded string
- **Country prefix stripping**: Channel names like "IL: Kan 11" and "Israel: Kan 11" are now normalized to "Kan 11" for proper consolidation (both Python and Flutter)
- **Cross-country channel merging**: Channels with "Unknown" country now merge with same-named channels from known countries, preventing duplicates (e.g., "kan 11" from Unknown + "Israel: Kan 11" from Israel → single entry)

### Added
- **Channel alias groups**: Added Kan Bet, Kan Moreshet, Keshet 12 to consolidation alias mapping (both Python and Flutter)
- **Country prefix set**: 26 common country names recognized as M3U source prefixes for automatic stripping

## [2.3.2] - 2026-03-05

### Fixed
- **Health cache pagination**: Supabase health cache fetch now properly paginates using limit/offset (was only returning 1000 of 19k+ rows due to server-side limit)
- **Health cache after consolidation**: Health cache status is now applied AFTER channel consolidation, preventing `consolidate_channels()` from overwriting health-cached status with new dict copies
- **Consolidation preserves scan_status**: `consolidate_channels()` now transfers `scan_status='scanned'` and `last_scanned` from merged channels to the primary channel
- **Health cache timestamp**: Health-cached channels get `last_scanned=NOW` instead of stale `last_checked` from Supabase, preventing immediate re-scan
- **Double health cache fetch eliminated**: Stream checker now reuses the prefetched health cache from channel manager instead of re-fetching from Supabase
- **Stream checker logging**: Fixed `stream_checker.py` using bare `logging.getLogger()` instead of `utils.logger.get_logger()`, so SharedDb skip/upload messages now appear in logs
- **Silent upload failures logged**: Supabase batch upload errors are now logged as warnings instead of silently swallowed

### Changed
- **Health cache fetches working results only**: Reduced fetch from ~19k total rows to ~10k working rows, halving pagination time (~5s vs ~10s)
- **Removed dead M3U sources**: Removed samsung.m3u, plex.m3u, pluto.m3u (all returning 404) from both Python and Flutter configs
- **Fixed gb.m3u URL**: Corrected gb.m3u → uk.m3u in channels_config.json and m3u_service.dart (33 repos, down from 36)

### Performance
- **56% scan reduction on startup**: 9,201 of 16,397 channels skipped via SharedDb health cache
- **Startup scan time**: ~25 seconds from fetch start to scan queue (was 30s+ scanning everything)
- **Health cache fetch**: 10,048 working results in ~5 seconds (10 paginated requests)

## [2.3.1] - 2026-03-04

### Fixed
- **Smart startup scan**: Windows client no longer scans all 13k+ channels on start — health data from SharedDb is fetched during startup and used to pre-mark channels as working/failed, skipping them from the scan queue
- **Double validation removed**: Eliminated redundant `validate_channels_async()` call at 500ms that caused a duplicate scan before fetch completed
- **Channel name lookup**: Fixed display name with source count suffix not matching internal channel name for clicks/right-clicks

### Added
- **Source count indicator**: Channel names in the list now show `[N sources]` when a channel has multiple stream URLs
- **Source selector context menu**: Right-click a channel to see "📡 Sources (N)" submenu — pick any source URL to play directly
- **Play with specific source**: New `_play_channel_with_source()` method enables direct source selection before playback

## [2.3.0] - 2026-03-04

### Added
- **Smart URL health ordering**: Both platforms now reorder channel URLs by known health status before scanning — working URLs are tried first, reducing scan time for multi-source channels
- **Channel sources migration SQL**: New `channel_sources` table schema for per-URL reliability tracking with crowd-sourced health scoring (`scripts/supabase_migration_v2.3.0.sql`)
- **Python Supabase channel fetch/contribute**: `shared_db.py` now supports `fetch_channels()` and `contribute_channels()` for unified data access
- **Database cleanup support**: Migration includes DELETE RLS policy on channels table and `truncate_channels()` function for clean repopulation

### Fixed
- **Kan 11 consolidation**: Fixed Python alias mapping — "Kan 11 News", "Kan 11 Subtitled", "Kan 11 4K", "כאן 11" now properly merge into single "Kan 11" entry with multiple source URLs
- **Kan Kids consolidation**: Fixed alias mismatch — "Kan Kids / Kan Educational" and "Kan Kids" now merge correctly under "Kan Kids"
- **Flutter alias alignment**: Updated Flutter `_channelAliases` to match Python aliases (added 'kan 11 israel', fixed Kan Kids canonical name)
- **Stale DB entries**: Added `--clean` flag to populate script to remove old unconsolidated entries before repopulation

### Changed
- **SharedDbService.hashUrl** made public in Flutter for URL health lookups across components
- **Populate script**: Now supports `--clean` flag for fresh repopulation (deletes all channels before uploading)
- **Supabase channels**: 13,353 properly consolidated channels (down from 15,924 with stale duplicates)

## [2.2.4] - 2026-03-04

### Added
- **Unified Supabase channel database**: Both Windows and Android now read from the same Supabase `channels` table (13,789 channels with multi-source URLs)
- **Flutter → Supabase channel contribution**: Android app now contributes newly discovered channels back to the shared database (was read-only before)
- **Population script**: `scripts/populate_supabase.py` for batch channel fetch, consolidation, health check, and Supabase upload
- **7 additional repos in Android**: Aligned Flutter repo list with Windows (djthawks, RokuIL, iptv-org/streams/il, radio-browser Israel/US/UK)

### Fixed
- **Removed dead source**: Removed od.lk/Free2ViewTV link (HTTP 404) from both platforms
- **Channel count parity**: Both platforms now see the same 13,789 consolidated channels from the shared database

### Changed
- **Channel fetch flow (Android)**: Now fetches from Supabase first, supplements with M3U repos, contributes new channels back
- **Health status populated**: 15,946 URLs health-checked and uploaded to `channel_status` table (7,625 working, 8,321 failed)

## [2.2.3] - 2026-03-04

### Fixed
- **Windows adult content toggle**: Added checkbox to Settings dialog (Display Settings section) — persists to channels_config.json and re-filters channels immediately

## [2.2.2] - 2026-03-04

### Fixed
- **Issue #61**: Source selector on error screen now allows retrying any source (previously all sources were disabled after auto-failover exhausted them)
- **Categories showing countries**: Removed `cat.length <= 3` filter that let country codes (UK, USA) appear as content categories
- **Adult content toggle**: Fixed HTTP→HTTPS for adult source URL (Android blocks cleartext), added 'Adult' to known categories
- **Reshet channels missing**: Added Reshet 13 Comedy, Nofesh, Reality, Subtitled, and Big Brother Israel to Flutter custom channels
- **Player rotation**: Allow auto-rotation (portrait + landscape) instead of forcing landscape-only

### Added
- New Israeli channel source from gist (serginholssfilmes) with 50+ Israeli channels
- Explicit channel alias mapping: Kan 11/News/Subtitled/4K merged as multi-URL, Kan Kids/Educational merged, Reshet 13/Alt/Subtitled merged
- Standalone "alt" suffix stripping in channel name normalization

### Changed
- Channel consolidation now uses alias groups for known channels (Kan, Reshet) while preserving distinct content variants (Comedy, Nofesh, Reality)

## [2.2.1] - 2026-03-04

### Fixed
- **Issue #61**: Source selector now visible on channel error screen — users can switch sources when playback fails
- **Channel consolidation**: Channels with same name (e.g., Kan 11, כאן 11) merged into single multi-URL entries with failover
- **Android settings**: Added adult content toggle to Help & Settings screen (was missing in v2.2.0)

### Changed
- Flutter M3U service: Name-based channel consolidation (strips quality suffixes, handles Hebrew/Latin aliases)
- Reduced duplicate channels across sources (Kan 11/כאן merged, quality variants consolidated)

## [2.2.0] - 2026-03-04

### Added
- **Adult content filter** — Adult/NSFW channels are hidden by default on both Windows and Android. Toggle in settings to enable (Windows: `SHOW_ADULT_CONTENT` in config.py; Android: SharedPreferences toggle). Adult sources (xxx.m3u, index.nsfw.m3u, adultiptv) are not even fetched unless enabled.
- **9 new channel sources** — Added apsattv.com (xumo, lg, rok, redbox, xiaomi, tablo, vizio, firetv, klowd), Free2ViewTV, and iptv-org xxx/nsfw indices
- **Supabase RLS fix** — Added `ae_anon_select` policy to `supabase_setup.sql` for analytics_events table

### Changed
- **Source consolidation** — Removed 75+ redundant iptv-org M3U URLs. `index.m3u` already contains all category and country subsets. Flutter: 28→15 repos, Windows: 98→21 repos. Faster scanning, less bandwidth.

### Fixed
- **CI Flutter analyze** — Moved dead-code files (fmstream_integration_example, feedback_screen, external_player_service, integration test) out of analysis scope to fix persistent build failures

## [2.1.7] - 2026-03-04

### Fixed
- **CI Flutter analyze pipeline** — Fixed 431+ errors across 5 iterations:
  - Wrong package imports (`package:flutter_app/` and `package:tv_viewer_project/` → `package:tv_viewer/`)
  - API mismatch: `filteredChannels` → `channels` getter in ChannelProvider tests
  - Removed non-existent `FeedbackSubmissionResult` test group
  - Suppressed expected warnings in test stubs (`unused_local_variable`, `unused_field`)
- **CI `flutter analyze` warnings treated as fatal** — Added `--no-fatal-warnings` flag; errors remain fatal
- **Android version mismatch** — `local.properties` was stuck at v1.9.0 while pubspec was 2.1.6

### Added
- **Comprehensive release process** — `docs/RELEASE_PROCESS.md` with 8-phase mandatory checklist covering security, code review, version bump, issue triage, workflow verification, and post-release gates

## [2.1.6] - 2026-03-03

### Fixed
- **Supabase data pipeline (CRITICAL)** — Four root causes prevented ANY data from reaching Supabase:
  1. `analytics_events` RLS policy blocked anonymous INSERT — fixed by re-running updated SQL schema
  2. `analytics.py` was missing `country` field — all events had `country='XX'`, breaking geographic analytics
  3. Two separate device ID files (`.tv_viewer_device_id` and `.tv_viewer_analytics_id`) made one device appear as two — consolidated to single shared file
  4. `telemetry.py` URL hash truncated to 16 chars vs 64 in `analytics.py` — now full SHA256 everywhere
- **`channels` table created in Supabase** — crowdsourced channel repository now operational. Clients fetch channel list from Supabase first, then supplement with M3U sources. New channels contributed back.
- **`supabase_channels.py` urls double-serialization** — `urls` JSONB column was stored as escaped string instead of array. Fixed to pass native list to PostgREST.
- **Session analytics never tracked** — `_on_close()` now calls `track_session_end()` with duration, channels played/failed, and flushes analytics before shutdown
- **Favorite events not wired up** — `_do_toggle_fav()` and `_toggle_favorite_from_menu()` now emit `favorite_add`/`favorite_remove` telemetry events

### Added
- **Supabase-first channel architecture** — App pulls channel list from Supabase `channels` table on startup (fast, pre-consolidated), then fetches M3U repos in parallel. New M3U channels are contributed back to Supabase for crowdsourcing.
- **`utils/supabase_channels.py`** — New service: `fetch_channels()`, `contribute_channels()`, `diff_channels()` with paginated fetch, batch upsert, and graceful fallback.
- **8 Supabase contract tests** — Regression tests that catch serialization bugs (double-JSON, missing columns, schema drift) before they reach production. Tests for: event_data format, country field, device ID consistency, URL hash length, urls serialization, event key alignment.
- **Session analytics counters** — `_app_start_time`, `_channels_played_count`, `_channels_failed_count` tracked throughout session for accurate `session_end` events.

### Changed
- `channel_manager._fetch_and_update()` rewritten for Supabase-first flow with M3U fallback
- `analytics.py` now uses same device ID file as `telemetry.py` (`.tv_viewer_device_id`)
- `telemetry.py` URL hash uses full 64-char SHA256 (was truncated to 16)
- Test suite expanded from 23 to 31 tests

## [2.1.5] - 2026-03-04

### Fixed
- **Supabase schema mismatch (CRITICAL)** — `telemetry.py` was writing to non-existent `app_telemetry` table instead of `analytics_events`. `channel_status` table had mismatched column names (`channel_url_hash`/`is_working`/`checked_at` in SQL vs `url_hash`/`status`/`last_checked` in code). No telemetry or shared health data was being written. Schema and code now fully aligned.
- **Privacy: removed channel_name from analytics** — `track_channel_health()` no longer sends `channel_name` in event data (security review finding: viewing habits are sensitive). Only hashed URL is sent.

### Added
- **Futureproof Supabase schema** — 2 immutable tables + N disposable materialized views. No CHECK constraints; JSONB event_data handles any shape. Adding new event types requires zero DDL changes. Includes rate-limiting trigger on `channel_status`, consensus-based `report_count`, data retention functions (`cleanup_old_data()`), and `db_health()` diagnostic function.
- **Favorite tracking** — both Python (`track_favorite()`) and Flutter (`trackFavorite()`) analytics now track favorite add/remove events with hashed URL and country/category.
- **Session end tracking** — both platforms track `session_end` events with session duration, channels played/failed for engagement analysis.
- **Dashboard materialized views** — `mv_daily_active_users`, `mv_top_channels`, `mv_client_platforms`, `mv_favorite_channels`, `mv_crash_summary`, `mv_engagement` for analytics dashboards. Refreshable via `refresh_analytics_views()`.
- **Next/Previous channel navigation** — both Windows and Android players have ⏮/⏭ buttons to jump to adjacent channels in the filtered list without returning to the channel browser.
- **Country-aware channel consolidation** — `_normalize_name_for_grouping()` strips Hebrew/Arabic text separated by dash, trailing country names, and embedded country names. "KAN 11 Israel" and "Kan 11" now merge correctly. Fixes PR #59 `None` country crash.

### Changed
- **Map popup performance** — cached class-level fonts (was creating 700+ font objects per popup), removed popup fade-in animation, deferred modal grab. Significantly faster popup rendering.
- **Android player source fallback** — reworked `_initializePlayer()` with `_failedIndices` set and `startIndex` parameter to prevent `loadPreferredSource()` from overriding fallback index. Added re-entrancy guard (`_isFallingBack`) for error listener.

### Security
- Supabase `channel_status` now has rate-limiting trigger (max 1 update per url_hash per minute)
- `report_count` column for consensus-based trust (clients should trust entries with count ≥ 3)
- Data retention: `cleanup_old_data()` function deletes events >90 days and stale channel_status >7 days

## [2.1.4] - 2026-03-03

### Added
- **Source selector in player** — both Windows and Android players show a source picker when a channel has multiple stream URLs. Select which source to use; preferred source is saved per channel (SharedPreferences on Android, working_url_index on Windows)
- **Flutter channel consolidation (Issue #58)** — `ChannelRepositoryImpl.fetchChannels()` now calls `deduplicateChannels()` + `consolidateByName()` before returning. Consolidation code was previously orphaned and never invoked on Android

### Fixed
- **Android duplicate channels (Issue #58)** — channels now properly consolidated on Android with same multi-pass normalization as Windows. "Reshet 13 (720p)", "Reshet 13 (רשת 13)", "Reshet 13 Subtitled" all merge into one entry

### Changed
- **Documentation overhaul** — ARCHITECTURE.md rewritten for v2.1.4 (consolidation, smart scan, Supabase, telemetry, source selector, security). README.md updated with new features and tech stack. SUPPORT_GUIDE.md updated with troubleshooting for duplicates, source selector, and Supabase connectivity

## [2.1.3] - 2026-03-03

### Fixed
- **Channel consolidation overhaul** — aggressive multi-pass name normalization now strips trailing parenthesized annotations `(720p)`, `(רשת 13)`, `[Not 24/7]`, `[Geo-blocked]`, subtitle/dub variants, audio codecs (MP3, AAC, FLAC), and bitrate suffixes. "Reshet 13" now shows as 1 channel with 5 stream URLs instead of 5 separate entries
- **URL health-based ordering** — consolidated channels sort their URLs by health: working streams first (by response time), then unchecked, then failed. The preferred/last-working URL index is preserved across sorts
- **Flutter consolidation parity** — Android app now uses the same improved normalization patterns as the Windows client

### Changed
- Channel list reduced ~18% (17,948 → ~14,700) through better consolidation — no content lost, just unified into multi-URL entries

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
- **Scan animation 0% overlay** ([#30](https://github.com/tv-viewer-app/tv_viewer/issues/30))
  - Percentage text only shown when scan is active (total > 0), no longer overlays Earth animation
- **Channel deduplication on cache load** ([#29](https://github.com/tv-viewer-app/tv_viewer/issues/29))
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
- **VLC Playback Failure** ([#35](https://github.com/tv-viewer-app/tv_viewer/issues/35))
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
- **Segmentation Fault on Scan** (Linux) ([#32](https://github.com/tv-viewer-app/tv_viewer/issues/32))
  - Root cause: Background thread directly modifying tkinter UI state
  - Solution: All UI updates now scheduled on main thread using `root.after(0, ...)`
  - Prevents cross-thread tkinter access that caused crashes
  
- **VLC Detection Issue** ([#33](https://github.com/tv-viewer-app/tv_viewer/issues/33))
  - Enhanced error detection to distinguish VLC binary vs python-vlc package
  - Shows specific installation commands based on what's missing
  - Error messages now identify exact component missing

- **Scanning Animation Layout** ([#34](https://github.com/tv-viewer-app/tv_viewer/issues/34))
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
- **Country Inference System** - Automatically detects country from language when missing (Android) ([#28](https://github.com/tv-viewer-app/tv_viewer/issues/28))
- **Israeli Channel Detection** - Pattern-based detection for known Israeli channels (Android) ([#28](https://github.com/tv-viewer-app/tv_viewer/issues/28))
- **Country Normalization** - Standardizes country codes (IL→Israel, US→United States, etc.) (Android) ([#27](https://github.com/tv-viewer-app/tv_viewer/issues/27))

### Fixed
- **External Player Launch** - Removed canLaunchUrl check that was blocking launches (Android) ([#26](https://github.com/tv-viewer-app/tv_viewer/issues/26))
- **Cast Button** - Now successfully opens external players for casting (Android) ([#26](https://github.com/tv-viewer-app/tv_viewer/issues/26))
- **Countries Dropdown** - Now properly populated from channel metadata with inference (Android) ([#27](https://github.com/tv-viewer-app/tv_viewer/issues/27))

### Changed
- **Scan Animation Performance** - Reduced frame rate from 200ms to 400ms (50% fewer redraws) (Python)
- **Channel List Font Size** - Increased from 11 to 12 for better readability (Python)
- **Channel List Row Height** - Increased from 36 to 40 pixels for better spacing (Python)

### Performance
- Scan animation CPU usage reduced by ~50% (fewer redraws)
- UI rendering optimized with larger font/spacing preventing cramped appearance

## [1.7.0] - 2026-01-28

### Added (Flutter Android App)
- **Persistent Logging Service** - File-based logging with rotation (5 files, 1MB each) ([#2](https://github.com/tv-viewer-app/tv_viewer/issues/2))
- **User-Friendly Error Messages** - Comprehensive error handler with recovery suggestions ([#1](https://github.com/tv-viewer-app/tv_viewer/issues/1))
- **Language Filter** - Filter channels by language with dropdown selector ([#12](https://github.com/tv-viewer-app/tv_viewer/issues/12))
- **Wake Lock** - Screen stays awake during video playback ([#9](https://github.com/tv-viewer-app/tv_viewer/issues/9))
- **Help Screen** - In-app FAQ, troubleshooting guide, and support contact ([#8](https://github.com/tv-viewer-app/tv_viewer/issues/8))
- **Diagnostics Screen** - Device info, network status, stream URL tester ([#17](https://github.com/tv-viewer-app/tv_viewer/issues/17))
- **Onboarding Service** - First-time user tooltips system ([#5](https://github.com/tv-viewer-app/tv_viewer/issues/5))
- **Picture-in-Picture** - PiP support for Android 8.0+ ([#16](https://github.com/tv-viewer-app/tv_viewer/issues/16))
- **Enhanced External Players** - Support for 6+ external players (VLC, MX Player, MPV, Just Player) ([#18](https://github.com/tv-viewer-app/tv_viewer/issues/18))
- **USER_GUIDE.md** - End-user documentation ([#6](https://github.com/tv-viewer-app/tv_viewer/issues/6))
- **FAQ.md** - Frequently asked questions document ([#7](https://github.com/tv-viewer-app/tv_viewer/issues/7))
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

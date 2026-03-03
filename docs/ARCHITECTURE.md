# TV Viewer — Architecture Documentation

## Overview

TV Viewer is a cross-platform IPTV streaming application. The Windows desktop
client is built with Python (CustomTkinter + VLC); the Android client is built
with Flutter. Both platforms share a common data model and connect to the same
Supabase backend for crowd-sourced channel health and anonymous telemetry.

**Version:** 2.1.4
**Platforms:** Windows (primary), Android (Flutter)

## Technology Stack

### Windows (Python)

| Component | Technology | Purpose |
|-----------|------------|---------|
| UI Framework | CustomTkinter | Windows 11 Fluent Design UI |
| Video Player | VLC (python-vlc) | Hardware-accelerated playback |
| HTTP Client | aiohttp | Async network operations |
| Concurrency | asyncio + threading | Non-blocking operations |
| Data Storage | JSON files | Channel cache and config |
| Backend | Supabase (REST) | Crowd-sourced health & telemetry |
| Telemetry | utils/telemetry.py | Privacy-first anonymous events |
| Maps | tkintermapview | Interactive channel map |
| Logging | Python logging | Rotating file logs |
| Build | PyInstaller | Windows executable |
| CI/CD | GitHub Actions | Automated builds |

### Android (Flutter)

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Flutter / Dart | Cross-platform mobile UI |
| State Mgmt | Provider 6.1.x | Reactive state management |
| DI | GetIt 7.6.x | Service locator |
| Video | video_player | Native playback |
| Storage | SharedPreferences | Local prefs & source selection |
| Maps | flutter_map 6.1.x | Channel world map |
| Backend | Supabase (REST) | Shared with Windows client |
| Telemetry | services/analytics_service.dart | Privacy-first anonymous events |

## Project Structure

```
tv_viewer_project/
├── main.py                    # Desktop entry point
├── config.py                  # Settings, Supabase URL/key
├── build.py                   # PyInstaller build script
├── channels.json              # Cached channel data
├── channels_config.json       # User config (repos, custom channels)
│
├── core/                      # Core business logic (Python)
│   ├── channel_manager.py     # Channel coordinator + consolidation
│   ├── repository.py          # IPTV repository fetching
│   └── stream_checker.py      # Smart Scan engine
│
├── ui/                        # Desktop UI components
│   ├── main_window.py         # Main window + nav rail
│   ├── player_window.py       # Player + source selector
│   ├── map_window.py          # World map (CartoDB tiles)
│   ├── channel_card.py        # Channel card widget
│   ├── channel_grid.py        # Scrollable channel grid
│   ├── nav_rail.py            # Navigation rail
│   ├── status_bar.py          # Bottom status bar
│   └── scan_animation.py      # Pixel art scan animation
│
├── utils/                     # Shared utilities (Python)
│   ├── helpers.py             # M3U parsing, JSON I/O, SSRF guard
│   ├── shared_db.py           # Supabase client (channel_status)
│   ├── telemetry.py           # Privacy-first telemetry
│   ├── channel_lookup.py      # Channel metadata lookup
│   ├── thumbnail.py           # Thumbnail capture/cache
│   ├── favorites.py           # Favorite channels
│   ├── cache.py               # Generic cache utilities
│   ├── analytics.py           # Analytics helpers
│   └── logger.py              # Logging configuration
│
├── flutter_app/               # Android client
│   └── lib/
│       ├── models/            # Channel, Category, etc.
│       ├── repositories/
│       │   └── impl/
│       │       ├── channel_repository_impl.dart
│       │       └── playlist_repository_impl.dart
│       ├── services/
│       │   ├── shared_db_service.dart
│       │   └── analytics_service.dart
│       ├── providers/         # Provider state classes
│       ├── screens/           # UI screens
│       ├── widgets/           # Reusable widgets
│       ├── di/                # GetIt registration
│       └── data/              # Constants, API config
│
├── tests/                     # Test suite
├── docs/                      # Documentation
├── scripts/                   # Build & utility scripts
├── thumbnails/                # Cached thumbnails
└── logs/                      # Rotating log files
```

## Component Architecture

### Data Flow

```
┌──────────────┐    ┌───────────────┐    ┌──────────────┐
│  Repository  │───>│  Channel      │───>│  Stream      │
│  Handler     │    │  Manager      │    │  Checker     │
│  (fetch M3U) │    │  (organise +  │    │  (Smart Scan │
│              │    │   consolidate)│    │   + priority) │
└──────────────┘    └──────┬────────┘    └──────┬───────┘
                           │                     │
                    ┌──────▼────────┐     ┌──────▼───────┐
                    │  Main Window  │     │  Supabase    │
                    │  (display)    │     │  shared_db   │
                    └──────┬────────┘     │  (health +   │
                           │              │   telemetry) │
                    ┌──────▼────────┐     └──────────────┘
                    │  Player       │
                    │  (playback +  │
                    │   source sel) │
                    └───────────────┘
```

### Threading Model

```
┌──────────────────────────────────────────────────────────────┐
│  Main Thread (UI)                                            │
│  - CustomTkinter event loop                                  │
│  - User interaction handling                                 │
│  - UI updates via root.after()                               │
└──────────────────────────────────────────────────────────────┘
          │ Callbacks (thread-safe)
          v
┌──────────────────────────────────────────────────────────────┐
│  Background Thread — StreamChecker (Smart Scan)              │
│  - asyncio event loop with priority queue                    │
│  - 30 concurrent HTTP checks (semaphore)                     │
│  - Pause/resume via threading.Event                          │
│  - Low thread priority (below normal)                        │
└──────────────────────────────────────────────────────────────┘
          │
          v
┌──────────────────────────────────────────────────────────────┐
│  Supabase Upload Thread (daemon)                             │
│  - Per-batch streaming of scan results                       │
│  - Telemetry event queue (fire-and-forget)                   │
└──────────────────────────────────────────────────────────────┘
          │
          v
┌──────────────────────────────────────────────────────────────┐
│  VLC Threads (managed by libvlc)                             │
│  - Video decoding (hardware accelerated)                     │
│  - Audio processing · Network streaming                      │
└──────────────────────────────────────────────────────────────┘
```

## Key Subsystems

### 1. Channel Consolidation

Multi-pass name normalisation merges duplicate channels that differ only in
quality tags, codec labels, or regional suffixes into single multi-URL entries.
Both platforms implement the same algorithm; the result is an **~18 % reduction**
in visible channel count.

#### Normalisation Patterns Stripped

| Category | Examples |
|----------|----------|
| Quality / resolution | `(720p)`, `(1080i)`, `HD`, `FHD`, `4K`, `SD` |
| Regional suffixes | `(רשת 13)`, `(Geo-blocked)`, `[Not 24/7]` |
| Audio codecs | `MP3`, `AAC`, `AAC+`, `FLAC` |
| Video codecs | `h.264`, `h.265`, `HEVC` |
| Variant markers | `alt`, `backup`, `mirror`, `dubbed`, `subtitled`, `multi-audio` |
| Version / stream IDs | `v1`, `v2`, `option1`, `stream1`, `128k`, `320k` |

#### Merge Logic

1. Channels are grouped by **normalised name + country** (case-insensitive).
2. All unique URLs are collected into a `urls[]` array on the merged entry.
3. **Python second pass** sorts URLs by health: working (fastest first) →
   unchecked → failed. A `working_url_index` tracks the preferred source.
4. **Flutter** ORs the `isWorking` flag (if any variant works, the merged
   entry is marked working) and preserves the first occurrence's metadata.

#### Entry Points

| Platform | Location | Function |
|----------|----------|----------|
| Windows | `core/channel_manager.py` | `consolidate_channels()` |
| Android | `playlist_repository_impl.dart` | `consolidateByName()` |
| Android | `channel_repository_impl.dart` | `fetchChannels()` → calls `deduplicateChannels()` before returning (Issue #58 fix) |

---

### 2. Smart Scan

`StreamChecker` (`core/stream_checker.py`) replaces the old linear scan with a
**dynamic priority queue** and primary-URL-only main pass.

#### Priority Order

| Priority | Bucket | Rationale |
|----------|--------|-----------|
| 1 (highest) | Recently played channels | Immediate user interest |
| 2 | User's country (via `boost_country()`) | Regional relevance |
| 3 | Never-scanned channels | New additions |
| 4 | Working channels needing revalidation | Staleness check |
| 5 (lowest) | Known-failed channels | Unlikely to recover |

#### Scan Strategy

- **Main pass:** Only the primary URL of each channel is checked.
  Alternative URLs are queued for background verification.
- **Pause / resume:** `threading.Event` flag; triggered when the map window
  opens (frees bandwidth for tile downloads) and resumed on close.
- **Streaming upload:** Scan results are pushed to Supabase per-batch as they
  complete, not at the end.

---

### 3. Supabase Integration

Supabase is the **always-on** shared backend (replaces the earlier PrivateBin
experiment). Both platforms use REST with an anonymous key protected by Row
Level Security.

#### Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `channel_status` | Crowd-sourced channel health | `url_hash` (SHA-256), `status`, `last_checked`, `response_time_ms` |
| `app_telemetry` | Anonymous usage telemetry | `device_id` (random UUID), `event_type`, `payload`, `created_at` |

#### Client Code

| Platform | File | Notes |
|----------|------|-------|
| Windows | `utils/shared_db.py` | Imports `SUPABASE_URL` / `SUPABASE_KEY` from `config.py` |
| Android | `services/shared_db_service.dart` | Same Supabase instance |

**Privacy:** Channel URLs are SHA-256 hashed before transmission. A 24-hour
cache prevents redundant re-scanning.

---

### 4. Privacy-First Telemetry

Anonymous, opt-out telemetry with no PII. Implemented independently on each
platform but sharing the same Supabase table and event schema.

#### Tracked Events

| Event | Payload (examples) | Notes |
|-------|--------------------|-------|
| `app_start` | platform, OS version, Python/Flutter version | — |
| `channel_play` | country (locale), category, hashed URL | No channel name |
| `channel_fail` | country, category, error type, hashed URL | No channel name |
| `feature_use` | feature name (map, search, scan, fullscreen) | — |
| `scan_complete` | total channels, working count, duration | — |

#### Privacy Guarantees

- **No PII**: No usernames, IPs, emails, or device fingerprints.
- **No channel names or URLs**: Only SHA-256 hashes are transmitted.
- **Random device ID**: Persistent UUID per install; not tied to hardware.
- **Opt-out**: Flutter: `setEnabled(false)`; Python: config flag.
- **Rate-limited**: Max 500 events per type per session.
- **Fire-and-forget**: Never blocks UI; silently drops on failure.

#### Implementation

| Platform | File | Mechanism |
|----------|------|-----------|
| Windows | `utils/telemetry.py` | Daemon threads, immediate upload |
| Android | `services/analytics_service.dart` | Batched queue (20 events or 30 s) |

---

### 5. Source Selector

For channels with multiple stream URLs (created by consolidation), the player
exposes a **source selector** control.

- **UI**: Dropdown (`#1`, `#2`, …) in `ui/player_window.py`; only shown when
  `len(urls) > 1`.
- **Default selection**: Pre-selects `working_url_index` (last known-working
  source).
- **Persistence**: Flutter stores the preferred source per channel in
  `SharedPreferences`. Python persists `working_url_index` in the channel
  cache.
- **Background verification**: Alternative URLs are verified in the background
  so the selector reflects up-to-date health.

---

## Key Classes

### ChannelManager (`core/channel_manager.py`)

Central coordinator for channel data. Thread-safe with `RLock`.

**Responsibilities:**
- Load / save channel cache
- Fetch from IPTV repositories
- Organise by category / country
- **Consolidate duplicate channels** (`consolidate_channels()`)
- Coordinate validation
- Filter by media type

**Memory Optimisation:**
- Uses `__slots__` (~40 % memory savings)
- Shared references between categories / countries
- In-place channel updates

### StreamChecker (`core/stream_checker.py`)

Background stream validator — **Smart Scan** engine.

**Responsibilities:**
- Dynamic priority-queue scheduling
- Async HTTP HEAD/GET requests (30 concurrent via semaphore)
- Primary-URL-only main pass; alternatives queued in background
- Pause / resume (map viewing, user request)
- Per-batch streaming of results to Supabase
- Graceful cancellation

**Performance Features:**
- Low thread priority
- DNS caching
- TCP connection reuse (`force_close=False`, `keepalive_timeout=30`)
- Batch processing with GC

### MainWindow (`ui/main_window.py`)

Main desktop UI with navigation rail.

**Features:**
- Category / country grouping
- Media type filtering
- Real-time scan progress
- Debounced UI updates
- Channel card grid

### PlayerWindow (`ui/player_window.py`)

Embedded video player with hardware acceleration.

**Features:**
- Platform-specific HW acceleration
- Volume / mute controls
- Fullscreen toggle
- **Source selector** for multi-URL channels
- Google Cast support (optional)

### MapWindow (`ui/map_window.py`)

Interactive world map showing channel locations.

**Features:**
- CartoDB Dark Matter basemap tiles
- SQLite tile cache (`tv_viewer_tiles.db` in temp directory)
- Pauses Smart Scan while open (frees bandwidth)

## Performance Optimisations

### Scanning (6× faster than v1.x)

| Lever | Old | New | Impact |
|-------|-----|-----|--------|
| Concurrent checks | 10 | **30** | 3× throughput |
| Inter-request delay | 100 ms | **5 ms** | Eliminated 30+ min of sleep for 18 K channels |
| URL strategy | All URLs | **Primary only** (alternatives in background) | 2–5× fewer checks |
| Connection reuse | Off | **`force_close=False`, `keepalive_timeout=30`** | 2–3× speedup for CDN hosts |
| Channel count | — | **−18 %** via consolidation | Fewer total checks |

### CPU Optimisation

1. **Thread Priority**: Background checker runs at below-normal priority
2. **Adaptive Delays**: `SCAN_REQUEST_DELAY` (5 ms) between HTTP requests
3. **Batch Processing**: `SCAN_BATCH_SIZE=100`, with `SCAN_BATCH_DELAY=0.5 s`
4. **Debounced Updates**: UI refreshes are rate-limited
5. **Skip recent**: `SCAN_SKIP_MINUTES=30` avoids re-checking recent results

### Memory Optimisation

1. **`__slots__`**: Reduces per-channel object overhead
2. **Shared References**: Categories / countries point to same channel objects
3. **In-Place Updates**: Channels modified without copying
4. **Generational GC**: Triggered between batches

### Network Optimisation

1. **TCP Connection Pooling**: `force_close=False`, `keepalive_timeout=30`
2. **DNS Caching**: 5-minute TTL for lookups
3. **Per-Host Limits**: Prevents overwhelming individual servers
4. **Timeout Tuning**: `STREAM_CHECK_TIMEOUT=5 s`

### Map & Tile Performance

- **CartoDB Dark Matter** basemap — lightweight, dark-theme-matched
- **SQLite tile cache** in system temp directory — eliminates repeat downloads

### Video Optimisation

1. **Hardware Acceleration**:
   - Windows: D3D11VA
   - macOS: VideoToolbox
   - Linux: VAAPI / VDPAU
2. **Network Buffering**: 1-second cache for smooth playback

## Configuration

### `config.py` Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_CONCURRENT_CHECKS` | 30 | Parallel stream validations |
| `SCAN_REQUEST_DELAY` | 0.005 s | Delay between requests |
| `SCAN_BATCH_SIZE` | 100 | Channels per batch |
| `SCAN_BATCH_DELAY` | 0.5 s | Pause between batches |
| `SCAN_SKIP_MINUTES` | 30 | Skip recently-checked channels |
| `STREAM_CHECK_TIMEOUT` | 5 s | Per-stream timeout |
| `REQUEST_TIMEOUT` | 20 s | Repository fetch timeout |
| `SUPABASE_URL` | *(see config)* | Supabase project URL |
| `SUPABASE_KEY` | *(see config)* | Supabase anonymous key |

### `channels_config.json` (User Config)

```json
{
  "repositories": [
    "https://iptv-org.github.io/iptv/index.m3u"
  ],
  "custom_channels": [
    {
      "name": "My Channel",
      "url": "http://example.com/stream.m3u8",
      "category": "Custom"
    }
  ]
}
```

## Security

### URL & Network Safety

1. **Scheme allowlist**: Only `http` / `https` / `rtmp` / `rtsp` accepted
2. **SSRF protection** (`utils/helpers.py`): Resolves hostnames and blocks
   private / loopback / link-local / reserved IP ranges via
   `ipaddress.ip_address()` checks (`is_private`, `is_loopback`,
   `is_link_local`, `is_reserved`). Also blocks `javascript:`, `data:`,
   `file:`, `vbscript:`, `about:` schemes.
3. **FMStream HTTPS**: All FMStream URLs upgraded to HTTPS
4. **Content Limits**: Max file sizes on M3U downloads prevent DoS

### Analytics & Privacy

5. **No channel names in analytics**: Only SHA-256 hashed URLs
6. **No PII collected**: Random device UUID, no IP logging
7. **Rate-limited telemetry**: 500 events / type / session cap

### Player

8. **No Lua**: VLC Lua scripting disabled
9. **Input Sanitisation**: M3U content sanitised before parsing

## Error Handling

- **Network errors**: Logged, channel marked as failed, result uploaded to
  Supabase `channel_status`
- **Parse errors**: Skipped with warning; consolidation tolerates partial data
- **VLC errors**: Fallback to software decoding; source selector lets user try
  alternative URLs
- **UI errors**: Wrapped in try/catch to prevent crashes
- **Telemetry errors**: Silently dropped (fire-and-forget)
- **Supabase errors**: Logged but never block the UI or scan

## Testing

Run the desktop application:
```bash
python main.py
```

Build Windows executable:
```bash
python build.py
```

Run Flutter app (Android):
```bash
cd flutter_app
flutter run
```

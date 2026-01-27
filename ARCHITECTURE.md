# TV Viewer - Architecture Documentation

## Overview

TV Viewer is a cross-platform IPTV streaming application built with Python. It discovers, validates, and plays live TV streams from public IPTV repositories.

**Version:** 1.3.0  
**Platforms:** Windows, Linux, macOS, Android

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| UI Framework | CustomTkinter | Windows 11 Fluent Design UI |
| Video Player | VLC (python-vlc) | Hardware-accelerated playback |
| HTTP Client | aiohttp | Async network operations |
| Concurrency | asyncio + threading | Non-blocking operations |
| Data Storage | JSON files | Channel cache and config |
| Logging | Python logging | Rotating file logs |
| Mobile | Kivy | Android app UI |
| Build | PyInstaller | Windows executable |
| CI/CD | GitHub Actions | Automated builds |

## Project Structure

```
tv_viewer_project/
├── main.py                    # Application entry point
├── config.py                  # Configuration settings
├── channels.json              # Cached channel data
├── channels_config.json       # User configuration (repos, custom channels)
│
├── core/                      # Core business logic
│   ├── __init__.py
│   ├── channel_manager.py     # Central channel coordinator
│   ├── repository.py          # IPTV repository fetching
│   └── stream_checker.py      # Background stream validation
│
├── ui/                        # User interface components
│   ├── __init__.py
│   ├── main_window.py         # Main application window
│   ├── player_window.py       # Video player window
│   └── scan_animation.py      # Pixel art scan animation
│
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── helpers.py             # M3U parsing, JSON I/O
│   ├── channel_lookup.py      # Channel metadata lookup
│   └── thumbnail.py           # Thumbnail capture/cache
│
└── thumbnails/                # Cached channel thumbnails
```

## Component Architecture

### Data Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Repository     │────>│  Channel         │────>│  Stream         │
│  Handler        │     │  Manager         │     │  Checker        │
│  (fetch M3U)    │     │  (organize)      │     │  (validate)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               v
                        ┌──────────────────┐
                        │  Main Window     │
                        │  (display)       │
                        └──────────────────┘
                               │
                               v
                        ┌──────────────────┐
                        │  Player Window   │
                        │  (playback)      │
                        └──────────────────┘
```

### Threading Model

```
┌─────────────────────────────────────────────────────────────────┐
│  Main Thread (UI)                                                │
│  - Tkinter event loop                                           │
│  - User interaction handling                                     │
│  - UI updates via root.after()                                  │
└─────────────────────────────────────────────────────────────────┘
          │
          │ Callbacks (thread-safe)
          v
┌─────────────────────────────────────────────────────────────────┐
│  Background Thread (StreamChecker)                               │
│  - asyncio event loop                                           │
│  - Concurrent HTTP validation                                    │
│  - Low thread priority (below normal)                           │
└─────────────────────────────────────────────────────────────────┘
          │
          │ VLC internal threads
          v
┌─────────────────────────────────────────────────────────────────┐
│  VLC Threads (managed by libvlc)                                │
│  - Video decoding (hardware accelerated)                        │
│  - Audio processing                                             │
│  - Network streaming                                            │
└─────────────────────────────────────────────────────────────────┘
```

## Key Classes

### ChannelManager (`core/channel_manager.py`)

Central coordinator for channel data. Thread-safe with RLock.

**Responsibilities:**
- Load/save channel cache
- Fetch from IPTV repositories
- Organize by category/country
- Coordinate validation
- Filter by media type

**Memory Optimization:**
- Uses `__slots__` (~40% memory savings)
- Shared references between categories/countries
- In-place channel updates

### StreamChecker (`core/stream_checker.py`)

Background stream validator with CPU optimization.

**Responsibilities:**
- Async HTTP HEAD/GET requests
- Semaphore-limited concurrency
- Graceful cancellation

**Performance Features:**
- Low thread priority
- DNS caching
- Connection pooling
- Batch processing with GC

### MainWindow (`ui/main_window.py`)

Main application UI with Material Design.

**Features:**
- Category/country grouping
- Media type filtering
- Real-time scan progress
- Debounced UI updates

### PlayerWindow (`ui/player_window.py`)

Embedded video player with hardware acceleration.

**Features:**
- Platform-specific HW acceleration
- Volume/mute controls
- Fullscreen toggle
- Google Cast support (optional)

## Performance Optimizations

### CPU Optimization

1. **Thread Priority**: Background checker runs at below-normal priority
2. **Adaptive Delays**: Configurable sleep between HTTP requests
3. **Batch Processing**: Groups operations to reduce context switching
4. **Debounced Updates**: UI refreshes are rate-limited

### Memory Optimization

1. **`__slots__`**: Reduces object overhead
2. **Shared References**: Categories/countries point to same channel objects
3. **In-Place Updates**: Channels modified without copying
4. **Generational GC**: Triggered between batches

### Network Optimization

1. **Connection Pooling**: Reuses HTTP connections
2. **DNS Caching**: 5-minute TTL for lookups
3. **Per-Host Limits**: Prevents overwhelming servers
4. **Timeout Tuning**: Balanced for speed vs. reliability

### Video Optimization

1. **Hardware Acceleration**:
   - Windows: D3D11VA
   - macOS: VideoToolbox
   - Linux: VAAPI/VDPAU
2. **Network Buffering**: 1-second cache for smooth playback

## Configuration

### `config.py` Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_CONCURRENT_CHECKS` | 10 | Parallel stream validations |
| `STREAM_CHECK_TIMEOUT` | 8s | Per-stream timeout |
| `REQUEST_TIMEOUT` | 20s | Repository fetch timeout |

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

## Security Considerations

1. **URL Validation**: Only http/https/rtmp/rtsp allowed
2. **Content Limits**: Max file sizes prevent DoS
3. **Input Sanitization**: M3U content sanitized
4. **No Lua**: VLC Lua scripting disabled

## Error Handling

- Network errors: Logged, channel marked as not working
- Parse errors: Skipped with warning
- VLC errors: Fallback to software decoding
- UI errors: Wrapped in try/catch to prevent crashes

## Testing

Run the application:
```bash
python main.py
```

Build executable:
```bash
python build.py
```

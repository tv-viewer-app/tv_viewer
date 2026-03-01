# TV Viewer - API Reference

## Core Module (`core/`)

### ChannelManager

Central coordinator for channel data management.

```python
from core.channel_manager import ChannelManager

manager = ChannelManager()
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `channels` | `List[Dict]` | All channel dictionaries |
| `categories` | `Dict[str, List]` | Channels grouped by category |
| `countries` | `Dict[str, List]` | Channels grouped by country |
| `group_by` | `str` | Current grouping: 'category' or 'country' |
| `media_type_filter` | `str` | Current filter: 'All', 'TV', or 'Radio' |

#### Callbacks

| Callback | Signature | When Called |
|----------|-----------|-------------|
| `on_channels_loaded` | `(count: int) -> None` | After channels loaded from cache/repo |
| `on_channel_validated` | `(channel: Dict, current: int, total: int) -> None` | Per-channel validation |
| `on_validation_complete` | `() -> None` | All validation finished |
| `on_fetch_progress` | `(current: int, total: int) -> None` | Repository fetch progress |

#### Methods

##### `load_cached_channels() -> bool`
Load channels from local cache file.

```python
if manager.load_cached_channels():
    print(f"Loaded {len(manager.channels)} channels")
```

##### `save_channels() -> bool`
Save current channels to cache file.

##### `fetch_channels()`
Fetch channels from configured IPTV repositories.

##### `start_validation(force: bool = False)`
Start background stream validation.

| Parameter | Description |
|-----------|-------------|
| `force` | If True, re-validate all channels |

##### `get_groups() -> List[str]`
Get list of groups based on current `group_by` mode.

##### `get_channels_by_group(group: str) -> List[Dict]`
Get channels in specified group, filtered by `media_type_filter`.

##### `set_group_by(mode: str)`
Set grouping mode: 'category' or 'country'.

##### `set_media_type(media_type: str)`
Set media type filter: 'All', 'TV', or 'Radio'.

##### `search_channels(query: str) -> List[Dict]`
Search channels by name (case-insensitive).

---

### StreamChecker

Background stream validator with optimized resource usage.

```python
from core.stream_checker import StreamChecker

checker = StreamChecker(batch_size=500, request_delay=0.01)
```

#### Constructor Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `batch_size` | 500 | Channels per processing batch |
| `request_delay` | 0.01 | Seconds between requests |

#### Methods

##### `start_background_check(channels, on_channel_checked, on_complete)`
Start validation in background thread.

```python
checker.start_background_check(
    channels=manager.channels,
    on_channel_checked=lambda ch, cur, tot: print(f"{cur}/{tot}"),
    on_complete=lambda results: print("Done!")
)
```

##### `stop()`
Stop the background checker gracefully.

##### `is_running -> bool`
Property indicating if checker is active.

---

### RepositoryHandler

Async handler for fetching IPTV playlists.

```python
from core.repository import RepositoryHandler

handler = RepositoryHandler()
```

#### Methods

##### `fetch_repository(url: str) -> List[Dict]`
Fetch and parse a single M3U playlist URL.

##### `fetch_all_repositories(progress_callback) -> List[Dict]`
Fetch all configured repositories with deduplication.

---

## UI Module (`ui/`)

### MainWindow

Main application window with Material Design.

```python
from ui.main_window import MainWindow

app = MainWindow()
app.run()
```

#### Key Methods

| Method | Description |
|--------|-------------|
| `run()` | Start the Tkinter main loop |
| `_update_groups()` | Refresh category/country list |
| `_select_group(group)` | Display channels in group |
| `_play_channel(channel)` | Open player window |

---

### PlayerWindow

Video player window with VLC integration.

```python
from ui.player_window import PlayerWindow

player = PlayerWindow(parent, channel_dict)
```

#### Constructor Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `parent` | `tk.Tk` | Parent window |
| `channel` | `Dict` | Channel dictionary with 'url' key |

#### Key Methods

| Method | Description |
|--------|-------------|
| `play()` | Start playback |
| `stop()` | Stop playback |
| `_toggle_play()` | Toggle play/pause |
| `_toggle_fullscreen()` | Toggle fullscreen mode |
| `_toggle_mute()` | Toggle audio mute |

---

## Utils Module (`utils/`)

### helpers.py

Utility functions for data processing.

#### `parse_m3u(content: str) -> List[Dict]`
Parse M3U playlist content into channel dictionaries.

```python
channels = parse_m3u(m3u_content)
# Returns: [{'name': '...', 'url': '...', 'category': '...', ...}]
```

#### `load_json_file(filepath: str) -> Optional[Dict]`
Safely load JSON file with size limits.

#### `save_json_file(filepath: str, data: Dict) -> bool`
Save data to JSON file with error handling.

#### `categorize_channel(channel: Dict) -> str`
Determine channel category from metadata.

#### `get_channel_country(channel: Dict) -> str`
Determine channel country from URL/metadata.

---

## Channel Dictionary Structure

Each channel is a dictionary with these keys:

```python
{
    'name': str,           # Channel display name
    'url': str,            # Stream URL (http/https/rtmp/rtsp)
    'category': str,       # Category name (News, Sports, etc.)
    'country': str,        # Country name or code
    'logo': str,           # Logo URL (optional)
    'language': str,       # Language code (optional)
    'media_type': str,     # 'TV' or 'Radio'
    'min_age': int,        # Minimum age rating (7, 13, 18)
    'is_working': bool,    # Validation result (None = not checked)
    'last_scanned': str,   # ISO timestamp of last check
    'scan_status': str,    # 'pending', 'scanning', 'scanned'
}
```

---

## Configuration (`config.py`)

### Constants

| Constant | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | "TV Viewer" | Application name |
| `APP_VERSION` | "1.0.0" | Version string |
| `MAX_CONCURRENT_CHECKS` | 10 | Parallel validations |
| `STREAM_CHECK_TIMEOUT` | 8 | Seconds per stream check |
| `REQUEST_TIMEOUT` | 20 | Seconds for repo fetch |
| `WINDOW_WIDTH` | 900 | Main window width |
| `WINDOW_HEIGHT` | 600 | Main window height |
| `PLAYER_WIDTH` | 800 | Player window width |
| `PLAYER_HEIGHT` | 500 | Player window height |

### File Paths

| Path | Description |
|------|-------------|
| `CHANNELS_FILE` | Channel cache (channels.json) |
| `CHANNELS_CONFIG_FILE` | User config (channels_config.json) |
| `THUMBNAILS_DIR` | Thumbnail cache directory |

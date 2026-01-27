# TV Viewer

A cross-platform IPTV streaming application built with Python and CustomTkinter.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

- 🌍 **Auto-discover IPTV repositories** - Fetches channels from configurable IPTV repositories
- ✅ **Background channel validation** - Validates streams in background with low CPU priority
- 📂 **Categorized channel list** - Channels organized by category or country
- 📺 **Media type filtering** - Filter by TV, Radio, or All
- 🎬 **Embedded video player** - VLC-powered player with hardware acceleration
- 💾 **Persistent cache** - Saves working channels for faster startup
- 🎨 **Material Design UI** - Modern dark theme interface
- 🖼️ **Thumbnail previews** - Captures and caches channel thumbnails
- 🔒 **No login required** - Just start and watch

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and design |
| [PERFORMANCE.md](PERFORMANCE.md) | Performance optimization guide |
| [API.md](API.md) | API reference for developers |

## Requirements

- Python 3.8 or higher
- VLC media player installed on your system
- Required Python packages (see requirements.txt)

## Installation

1. **Install VLC Media Player**
   - Windows: Download from [videolan.org](https://www.videolan.org/vlc/)
   - Linux: `sudo apt install vlc` (Ubuntu/Debian) or `sudo dnf install vlc` (Fedora)

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

## Usage

### Main Window
- **Categories panel** (left): Browse channels by category
- **Channel list** (right): View channels in the selected category
- **Search**: Type in the search box to find channels by name
- **Double-click** a channel to start playing

### Player Window
- **Play/Pause (⏸/▶)**: Toggle playback
- **Stop (⏹)**: Stop playback
- **Volume slider**: Adjust volume
- **Mute (🔇)**: Toggle mute
- **Fullscreen (⛶)**: Toggle fullscreen mode
- **Keyboard shortcuts**:
  - `Space`: Play/Pause
  - `F`: Toggle fullscreen
  - `M`: Toggle mute
  - `Escape`: Exit fullscreen

### Menu Options
- **File > Refresh Channels**: Manually refresh channels from repositories
- **View > Show All Channels**: Show all channels in the current category
- **View > Show Working Only**: Show only validated working channels

## Project Structure

```
tv_viewer_project/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── config.py              # Configuration settings
├── channels.json          # Cached working channels (auto-generated)
├── ui/
│   ├── __init__.py
│   ├── main_window.py     # Main application window
│   └── player_window.py   # Video player window
├── core/
│   ├── __init__.py
│   ├── channel_manager.py # Channel discovery and validation
│   ├── stream_checker.py  # Background stream validation
│   └── repository.py      # IPTV repository handlers
└── utils/
    ├── __init__.py
    └── helpers.py         # Utility functions
```

## Configuration

Edit `config.py` to customize:
- Window sizes
- Request timeouts
- IPTV repository URLs
- Refresh intervals

## Troubleshooting

### "VLC is not available" error
- Make sure VLC media player is installed on your system
- On Windows, ensure VLC is in your PATH or install the 64-bit version if using 64-bit Python
- Run `pip install python-vlc` to install the Python bindings

### Channels not loading
- Check your internet connection
- Try clicking "File > Refresh Channels"
- Some channels may be geo-restricted in your region

### Video not playing
- Ensure VLC is properly installed
- Try a different channel - some streams may be temporarily offline
- Check if the channel is marked as "Working" in the status column

## License

MIT License - Feel free to use and modify as needed.

## Credits

- Uses [IPTV-org](https://github.com/iptv-org/iptv) community playlists
- Built with [python-vlc](https://pypi.org/project/python-vlc/) for video playback

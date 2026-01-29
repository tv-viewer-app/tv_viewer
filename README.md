# TV Viewer

A cross-platform IPTV streaming application built with Python and CustomTkinter.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Android-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Version](https://img.shields.io/badge/Version-1.3.0-orange.svg)

## Features

- 🌍 **Auto-discover IPTV repositories** - Fetches channels from 80+ configurable repositories
- ✅ **Background channel validation** - Validates streams with low CPU priority
- 📂 **Categorized channel list** - Channels organized by category or country
- 📺 **Media type filtering** - Filter by TV, Radio, or All
- 🎬 **Embedded video player** - VLC-powered player with hardware acceleration
- 💾 **Persistent cache** - Saves working channels for faster startup
- 🎨 **Windows 11 Fluent Design** - Modern dark theme interface
- 🖼️ **Thumbnail previews** - Captures and caches channel thumbnails
- 📱 **Android support** - Mobile app for Samsung Galaxy S24 Ultra and other devices
- 🔒 **No login required** - Just start and watch

## Downloads

| Platform | Download |
|----------|----------|
| Windows 11 | `dist/TV_Viewer.exe` (24 MB) |
| Android | Build via GitHub Actions (see [android/README.md](android/README.md)) |

## Quick Start

### Windows (Easiest)
1. Download `TV_Viewer.exe` from `dist/` folder
2. Double-click to run
3. Install VLC if prompted

### From Source
```bash
# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

## Documentation

| Document | Description |
|----------|-------------|
| [CHANGELOG.md](CHANGELOG.md) | Version history and changes |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and design |
| [SUPPORT_GUIDE.md](SUPPORT_GUIDE.md) | Troubleshooting guide |
| [PERFORMANCE.md](PERFORMANCE.md) | Performance optimization guide |
| [API.md](API.md) | API reference for developers |

## Requirements

- Python 3.9 or higher
- VLC media player installed on your system
- Required Python packages (see requirements.txt)

## Installation

1. **Install VLC Media Player**
   - Windows: Download from [videolan.org](https://www.videolan.org/vlc/)
   - Linux: `sudo apt install vlc`

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

## Usage

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `Space` | Play/Pause |
| `F` | Toggle fullscreen |
| `M` | Toggle mute |
| `Escape` | Exit fullscreen |

### Status Icons
| Icon | Meaning |
|------|---------|
| ✓ | Channel is working |
| ✗ | Channel is offline |
| ◌ | Still checking |

## Project Structure

```
tv_viewer_project/
├── main.py                 # Application entry point
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── dist/TV_Viewer.exe      # Windows executable
├── android/                # Android app source
├── tests/                  # Automated tests
├── ui/                     # User interface modules
├── core/                   # Core business logic
└── utils/                  # Utility functions
```

## Building

### Windows EXE
```bash
pyinstaller --onefile --windowed --name "TV_Viewer" --icon "tv_viewer.ico" main.py
```

### Android APK
```bash
cd android
buildozer android debug
```

## Validation

Run post-build validation before releases:
```bash
python tests/validate_build.py
```

## Troubleshooting

See [SUPPORT_GUIDE.md](SUPPORT_GUIDE.md) for detailed troubleshooting.

### Quick Fixes
- **VLC not found**: Install VLC from [videolan.org](https://www.videolan.org/vlc/)
- **No channels**: Check internet connection, click "Refresh"
- **Stream not playing**: Try another channel - some may be offline

## License

MIT License - Feel free to use and modify as needed.

## Credits

- [IPTV-org](https://github.com/iptv-org/iptv) community playlists
- [python-vlc](https://pypi.org/project/python-vlc/) for video playback
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for modern UI

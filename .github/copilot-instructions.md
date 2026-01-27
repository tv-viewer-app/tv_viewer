# TV Viewer Project - Copilot Instructions

## Project Overview
Cross-platform IPTV streaming application built with Python and tkinter.

## Tech Stack
- **Language**: Python 3.8+
- **UI Framework**: tkinter (cross-platform)
- **Video Playback**: VLC (python-vlc)
- **HTTP Requests**: requests, aiohttp
- **Data Storage**: JSON files

## Project Structure
```
tv_viewer_project/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── config.py              # Configuration settings
├── channels.json          # Cached working channels
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

## Key Features
1. Auto-discover IPTV repositories on startup
2. Background channel validation
3. Categorized channel list
4. Separate video player window with controls
5. Persistent channel cache for faster startup
6. No login required

## Development Guidelines
- Use async/await for network operations
- Validate streams in background threads
- Store working channels in channels.json
- Support both Windows and Linux

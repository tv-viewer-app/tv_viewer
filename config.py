"""Configuration settings for TV Viewer application.

This module contains all configurable parameters for the TV Viewer IPTV application.
Settings are organized into categories for easy maintenance.

Performance Tuning:
    - MAX_CONCURRENT_CHECKS: Lower = less CPU/bandwidth, higher = faster scanning
    - STREAM_CHECK_TIMEOUT: Lower = faster failures, higher = more reliable detection
    - REQUEST_TIMEOUT: Network timeout for repository fetching

Memory Management:
    - Thumbnail cache is stored in THUMBNAILS_DIR
    - Channel cache in CHANNELS_FILE reduces startup time
    - External config in CHANNELS_CONFIG_FILE for user customization
"""

import os
import json

# =============================================================================
# Application Metadata
# =============================================================================
APP_NAME = "TV Viewer"
APP_VERSION = "2.3.3"

# =============================================================================
# File Paths
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHANNELS_FILE = os.path.join(BASE_DIR, "channels.json")
CHANNELS_CONFIG_FILE = os.path.join(BASE_DIR, "channels_config.json")
THUMBNAILS_DIR = os.path.join(BASE_DIR, "thumbnails")

# Create thumbnails directory if it doesn't exist
if not os.path.exists(THUMBNAILS_DIR):
    os.makedirs(THUMBNAILS_DIR)

# =============================================================================
# Network Settings (Performance Tuning)
# =============================================================================
# Timeout for fetching repository playlists (seconds)
# Lower values fail faster but may miss slow servers
REQUEST_TIMEOUT = 15

# Timeout for validating individual streams (seconds)
# Balance between speed and accuracy - most working streams respond within 3s
STREAM_CHECK_TIMEOUT = 5

# Maximum concurrent stream checks
# Lower = less CPU/bandwidth, higher = faster but more resource usage
# Recommended: 25-35 for normal use, 5 for low-end systems
MAX_CONCURRENT_CHECKS = 30

# Batch size for stream checking (memory optimization)
# Lower = less memory per batch, but more GC cycles
SCAN_BATCH_SIZE = 100

# Delay between scan requests in seconds (CPU throttling)
# Semaphore handles concurrency; this is just a brief yield
SCAN_REQUEST_DELAY = 0.005

# Delay between batches in seconds (prevents CDN rate limiting)
SCAN_BATCH_DELAY = 0.5

# Skip re-scanning channels checked within this many minutes
SCAN_SKIP_MINUTES = 30

# =============================================================================
# Thumbnail Settings
# =============================================================================
THUMBNAIL_WIDTH = 64
THUMBNAIL_HEIGHT = 36
THUMBNAIL_CAPTURE_TIMEOUT = 5  # Seconds to wait for frame capture

# =============================================================================
# UI Settings
# =============================================================================
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700
PLAYER_WIDTH = 800
PLAYER_HEIGHT = 500

# =============================================================================
# Content Filtering
# =============================================================================
# Adult/NSFW channels are hidden by default. Set to True to include them.
SHOW_ADULT_CONTENT = False

# =============================================================================
# Supabase Analytics & Shared DB (anon key — public, protected by RLS)
# =============================================================================
SUPABASE_URL = os.environ.get('SUPABASE_URL',
    'https://cdtxpefohpwtusmqengu.supabase.co')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNkdHhwZWZvaHB3dHVzbXFlbmd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI0NzE4MzYsImV4cCI6MjA4ODA0NzgzNn0.FuzUDNIfxlGHptAZ0vWT4_8BDDEcy9CcSCY3te7_wMo')


def load_external_config():
    """Load repositories and custom channels from external JSON file."""
    global SHOW_ADULT_CONTENT
    default_repos = [
        "https://iptv-org.github.io/iptv/index.m3u",
        "https://iptv-org.github.io/iptv/index.country.m3u",
    ]
    default_custom = []
    default_adult = []
    
    if os.path.exists(CHANNELS_CONFIG_FILE):
        try:
            with open(CHANNELS_CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                repos = data.get('repositories', default_repos)
                custom = data.get('custom_channels', default_custom)
                adult = data.get('adult_repositories', default_adult)
                # Load persisted adult content preference
                if 'show_adult_content' in data:
                    SHOW_ADULT_CONTENT = bool(data['show_adult_content'])
                # Only include adult sources when enabled
                if SHOW_ADULT_CONTENT and adult:
                    repos = repos + adult
                print(f"Loaded external config: {len(repos)} repositories, {len(custom)} custom channels")
                return repos, custom
        except Exception as e:
            print(f"Error loading external config: {e}")
    
    return default_repos, default_custom


# Load from external config file
IPTV_REPOSITORIES, CUSTOM_CHANNELS = load_external_config()

# Media type - TV or Radio
MEDIA_TYPES = ["TV", "Radio", "All"]

# Categories to organize channels
DEFAULT_CATEGORIES = [
    "General",
    "News",
    "Sports",
    "Entertainment",
    "Movies",
    "Music",
    "Kids",
    "Documentary",
    "Education",
    "Lifestyle",
    "Comedy",
    "Classic",
    "Series",
    "Religious",
    "Radio",
    "Other"
]

# Refresh interval for channel checking (in seconds)
CHANNEL_REFRESH_INTERVAL = 300  # 5 minutes

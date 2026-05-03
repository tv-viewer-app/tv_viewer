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
APP_VERSION = "2.9.0"

# =============================================================================
# File Paths
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHANNELS_FILE = os.path.join(BASE_DIR, "channels.json")
CHANNELS_CONFIG_FILE = os.path.join(BASE_DIR, "channels_config.json")
THUMBNAILS_DIR = os.path.join(BASE_DIR, "thumbnails")

# Create thumbnails directory if it doesn't exist
# Fall back gracefully on permission errors (Bug #86)
try:
    if not os.path.exists(THUMBNAILS_DIR):
        os.makedirs(THUMBNAILS_DIR)
except (OSError, PermissionError):
    import tempfile
    THUMBNAILS_DIR = os.path.join(tempfile.gettempdir(), "tv_viewer_thumbnails")
    try:
        os.makedirs(THUMBNAILS_DIR, exist_ok=True)
    except (OSError, PermissionError):
        THUMBNAILS_DIR = tempfile.gettempdir()

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
# Telemetry & Analytics  (Issues #65, #79, #114)
# =============================================================================
# Telemetry is OFF by default.  It can be turned on in three ways:
#   1. The user opts in via the first-run consent dialog or Settings → Privacy
#   2. An environment variable:  TELEMETRY_ENABLED=true / 1 / yes
# The first-run dialog writes to config.TELEMETRY_ENABLED at runtime.
TELEMETRY_ENABLED = os.environ.get('TELEMETRY_ENABLED', '').lower() in ('true', '1', 'yes')

# Issue #170 — additional consent flags written by the first-run privacy
# dialog (utils/consent.py).  All default OFF; environment variables can
# force them on for headless/CI scenarios.
ONLINE_DB_ENABLED = os.environ.get('ONLINE_DB_ENABLED', '').lower() in ('true', '1', 'yes')
GEO_IP_ENABLED = os.environ.get('GEO_IP_ENABLED', '').lower() in ('true', '1', 'yes')

# =============================================================================
# Supabase Analytics & Shared DB
# =============================================================================
# NOTE: The Supabase anon key is INTENTIONALLY public. It is a client-side
# anonymous key that only allows operations permitted by Row Level Security
# (RLS) policies (e.g., INSERT into analytics_events, SELECT from
# channel_health). It cannot read, update, or delete protected data.
# This is the standard Supabase architecture for public-facing apps.
# See: https://supabase.com/docs/guides/api/api-keys
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')


def load_external_config():
    """Load repositories and custom channels from external JSON file.
    
    Adult repositories are loaded but only included at runtime based on
    parental controls (is_over_18). The ``include_adult`` parameter lets
    callers decide at fetch-time.
    """
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
                # Load persisted first-run / onboarding state
                global CONSENT_ACCEPTED, ONBOARDING_COMPLETED
                CONSENT_ACCEPTED = data.get('consent_accepted', False)
                ONBOARDING_COMPLETED = data.get('onboarding_completed', False)
                # Adult repos are stored but NOT merged here — callers use
                # parental_controls.is_over_18 to decide at runtime.
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

# =============================================================================
# First-Run / Onboarding State
# =============================================================================
# Defaults — load_external_config() may have already set these via 'global'
CONSENT_ACCEPTED = globals().get('CONSENT_ACCEPTED', False)
ONBOARDING_COMPLETED = globals().get('ONBOARDING_COMPLETED', False)

# Refresh interval for channel checking (in seconds)
CHANNEL_REFRESH_INTERVAL = 300  # 5 minutes

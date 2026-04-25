"""Privacy-first usage telemetry to Supabase.

Tracks anonymous, aggregate usage patterns:
- App starts (country from locale, platform, version)
- Channel plays (country, category — NO channel names or URLs)
- Channel failures (country, category, error type)
- Feature usage (map, scan, search, favorites, fullscreen)
- Favorites (add/remove with hashed URL)
- Session end (duration, engagement depth)

Privacy guarantees:
- No PII: no usernames, IPs, emails, or device identifiers
- No channel names or URLs (only hashed URL for dedup)
- Anonymous device ID (random UUID, no hardware fingerprint)
- User can opt out via config (TELEMETRY_ENABLED = False)
- Fire-and-forget: never blocks UI, silently drops on failure

Supabase table: analytics_events
  id (uuid, auto), event_type (text), event_data (jsonb),
  app_version (text), platform (text), created_at (timestamptz)
"""

import asyncio
import hashlib
import locale
import logging
import os
import platform
import ssl
import sys
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import certifi
except ImportError:
    certifi = None

# Import Supabase config
try:
    import config as _cfg
    _SUPABASE_URL = _cfg.SUPABASE_URL
    _SUPABASE_KEY = _cfg.SUPABASE_ANON_KEY
    _APP_VERSION = _cfg.APP_VERSION
    _TELEMETRY_ENABLED = getattr(_cfg, 'TELEMETRY_ENABLED', False)
except (ImportError, AttributeError):
    _SUPABASE_URL = ''
    _SUPABASE_KEY = ''
    _APP_VERSION = 'unknown'
    _TELEMETRY_ENABLED = False

_TABLE = 'analytics_events'
_PLATFORM = 'windows' if sys.platform == 'win32' else sys.platform
_DEVICE_ID_FILE = os.path.join(
    os.path.expanduser('~'), '.tv_viewer_device_id'  # Shared with analytics.py
)

# Rate limiting: max events per type per session
_EVENT_COUNTS: Dict[str, int] = {}
_MAX_PER_TYPE = 500

# Bounded thread pool replaces thread-per-event (Bug #123)
_EXECUTOR = ThreadPoolExecutor(max_workers=3, thread_name_prefix='telemetry')


def _get_device_id() -> str:
    """Get or create anonymous device ID (random UUID, no hardware info)."""
    try:
        if os.path.exists(_DEVICE_ID_FILE):
            with open(_DEVICE_ID_FILE, 'r') as f:
                return f.read().strip()
        did = str(uuid.uuid4())
        # Security: Create file with restricted permissions (owner-only read/write)
        fd = os.open(_DEVICE_ID_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.write(fd, did.encode('utf-8'))
        finally:
            os.close(fd)
        return did
    except Exception:
        return 'anonymous'


def _get_country() -> str:
    """Get country from system locale (no IP geolocation)."""
    try:
        loc = locale.getlocale()
        if loc and loc[0] and '_' in loc[0]:
            return loc[0].split('_')[1].upper()
    except Exception:
        pass
    return 'XX'


def _hash(value: str) -> str:
    """SHA256 hash for deduplication without exposing raw values."""
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


_DEVICE_ID = _get_device_id()
_COUNTRY = _get_country()


def _get_ssl_context() -> ssl.SSLContext:
    """Create SSL context with system CA bundle for Supabase connections."""
    if certifi is not None:
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    else:
        ssl_ctx = ssl.create_default_context()
    return ssl_ctx


def is_configured() -> bool:
    """Check if telemetry backend is available and user has not opted out."""
    return bool(_TELEMETRY_ENABLED and aiohttp and _SUPABASE_URL and _SUPABASE_KEY)


async def _send_event(event_type: str, event_data: Dict[str, Any]):
    """Send a single telemetry event to Supabase (async, fire-and-forget)."""
    if not is_configured():
        return

    # Rate limit per event type
    count = _EVENT_COUNTS.get(event_type, 0)
    if count >= _MAX_PER_TYPE:
        return
    _EVENT_COUNTS[event_type] = count + 1

    payload = {
        'event_type': event_type,
        'event_data': event_data,  # Pass dict directly; aiohttp json= handles serialization
        'app_version': _APP_VERSION,
        'platform': _PLATFORM,
        'device_id': _DEVICE_ID,
        'country': _COUNTRY,
    }

    try:
        url = f'{_SUPABASE_URL}/rest/v1/{_TABLE}'
        headers = {
            'apikey': _SUPABASE_KEY,
            'Authorization': f'Bearer {_SUPABASE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal',
        }
        ssl_ctx = _get_ssl_context()
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(
                url, json=payload, headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status not in (200, 201):
                    logger.debug(f'Telemetry: {resp.status}')
    except Exception:
        pass  # Never crash on telemetry failure


def track(event_type: str, event_data: Optional[Dict[str, Any]] = None):
    """Fire-and-forget telemetry event (non-blocking, thread-safe).

    Uses a bounded ThreadPoolExecutor (max 3 workers) to prevent
    unbounded thread creation.  Respects the TELEMETRY_ENABLED config
    flag — set it to False in config.py to opt out completely.

    Args:
        event_type: One of: app_start, channel_play, channel_fail,
                    feature_use, scan_start, scan_complete
        event_data: Dict of anonymous event properties
    """
    if not is_configured():
        return

    data = event_data or {}

    def _fire():
        try:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(_send_event(event_type, data))
            finally:
                loop.close()
        except Exception:
            pass

    try:
        _EXECUTOR.submit(_fire)
    except RuntimeError:
        pass  # Executor shut down — app is exiting


# ─── Convenience helpers ───

def track_app_start():
    """Track app launch."""
    track('app_start', {
        'os': platform.system(),
        'os_version': platform.version()[:30],
        'python': platform.python_version(),
    })


def track_channel_play(channel: Dict[str, Any]):
    """Track channel play (NO name or URL — only country/category)."""
    track('channel_play', {
        'country': channel.get('country', 'Unknown'),
        'category': channel.get('category', 'Other'),
        'url_hash': _hash(channel.get('url', '')),
    })


def track_channel_fail(channel: Dict[str, Any], error: str = ''):
    """Track channel failure (NO name or URL)."""
    track('channel_fail', {
        'country': channel.get('country', 'Unknown'),
        'category': channel.get('category', 'Other'),
        'url_hash': _hash(channel.get('url', '')),
        'error': error[:100] if error else '',
    })


def track_feature(feature: str):
    """Track feature usage (e.g. 'map_open', 'scan_start', 'fullscreen')."""
    track('feature_use', {'feature': feature})


def track_scan_complete(total: int, working: int, duration_sec: float = 0):
    """Track scan completion stats."""
    track('scan_complete', {
        'total': total,
        'working': working,
        'failed': total - working,
        'duration_sec': round(duration_sec, 1),
    })


def track_favorite(channel: Dict[str, Any], action: str = 'add'):
    """Track favorite add/remove (NO name or URL — only hashed URL)."""
    track('favorite', {
        'url_hash': _hash(channel.get('url', '')),
        'action': action,
        'country': channel.get('country', 'Unknown'),
        'category': channel.get('category', 'Other'),
    })


def track_session_end(duration_sec: float = 0, channels_played: int = 0,
                      channels_failed: int = 0):
    """Track session end with engagement depth."""
    track('session_end', {
        'session_duration_s': round(duration_sec),
        'channels_played': channels_played,
        'channels_failed': channels_failed,
    })

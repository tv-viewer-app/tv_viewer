"""PrivateBin integration for sharing scan results.

SECURITY NOTE (SEC-004): Upload functionality is disabled because the PrivateBin
v2 protocol requires client-side AES-256-GCM encryption before upload. The
previous implementation sent data compressed but unencrypted. Use SharedDb
approach instead for cross-platform channel status sharing.
"""

import json
import base64
import hashlib
import os
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import zlib

from utils.logger import get_logger

logger = get_logger(__name__)

# PrivateBin configuration
PRIVATEBIN_URL = "https://privatebin.info"
PASTE_EXPIRY = "4hour"
SETTINGS_FILE = "privatebin_cache.json"

# SEC-004: Upload disabled — requires AES-256-GCM encryption implementation
_UPLOAD_ENABLED = False


def _get_settings_path() -> str:
    """Get path to settings file."""
    import config
    return os.path.join(os.path.dirname(config.CHANNELS_FILE), SETTINGS_FILE)


def _load_settings() -> Dict[str, Any]:
    """Load PrivateBin settings from file."""
    settings_path = _get_settings_path()
    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading PrivateBin settings: {e}")
    return {"enabled": False, "paste_id": None, "paste_key": None, "timestamp": None}


def _save_settings(settings: Dict[str, Any]):
    """Save PrivateBin settings to file."""
    settings_path = _get_settings_path()
    try:
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving PrivateBin settings: {e}")


def is_enabled() -> bool:
    """Check if PrivateBin sharing is enabled."""
    if not _UPLOAD_ENABLED:
        return False
    return _load_settings().get("enabled", False)


def set_enabled(enabled: bool):
    """Enable or disable PrivateBin sharing."""
    if not _UPLOAD_ENABLED:
        logger.warning("PrivateBin upload is disabled (SEC-004: requires encryption)")
        return
    settings = _load_settings()
    settings["enabled"] = enabled
    _save_settings(settings)
    logger.info(f"PrivateBin sharing {'enabled' if enabled else 'disabled'}")


def upload_scan_results(channels: List[Dict[str, Any]]) -> Optional[str]:
    """Upload scan results to PrivateBin.
    
    DISABLED (SEC-004): Returns None. PrivateBin v2 requires AES-256-GCM
    client-side encryption which is not yet implemented.
    """
    logger.warning("PrivateBin upload disabled (SEC-004: unencrypted data transfer)")
    return None


def get_recent_scan_results() -> Optional[Dict[str, Any]]:
    """
    Check for and retrieve recent scan results from PrivateBin.
    
    Returns:
        Scan data if a valid paste exists (<4 hours old), None otherwise
    """
    if not is_enabled():
        return None
    
    settings = _load_settings()
    paste_id = settings.get("paste_id")
    timestamp_str = settings.get("timestamp")
    
    if not paste_id or not timestamp_str:
        return None
    
    # Check if paste is still valid (less than 4 hours old)
    try:
        paste_time = datetime.fromisoformat(timestamp_str)
        if datetime.now() - paste_time > timedelta(hours=4):
            logger.info("PrivateBin paste expired (>4 hours old)")
            return None
    except Exception:
        return None
    
    # Fetch paste from PrivateBin
    try:
        import aiohttp
        import asyncio
    except ImportError:
        return None
    
    async def _fetch():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{PRIVATEBIN_URL}/?{paste_id}",
                    headers={"Accept": "application/json", "X-Requested-With": "JSONHttpRequest"}
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get("status") == 0:
                            ct = result.get("ct", "")
                            # Decode and decompress
                            compressed = base64.b64decode(ct)
                            data_json = zlib.decompress(compressed).decode('utf-8')
                            return json.loads(data_json)
            return None
        except Exception as e:
            logger.error(f"Error fetching from PrivateBin: {e}")
            return None
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_fetch())
        loop.close()
        
        if result:
            logger.info(f"Retrieved scan results from PrivateBin ({len(result.get('channels', []))} channels)")
        return result
    except Exception as e:
        logger.error(f"Failed to fetch paste: {e}")
        return None


def get_non_working_urls(scan_data: Dict[str, Any]) -> set:
    """
    Extract URLs of non-working channels from scan data.
    
    Args:
        scan_data: Scan results from PrivateBin
        
    Returns:
        Set of URLs that were not working
    """
    non_working = set()
    for ch in scan_data.get("channels", []):
        if ch.get("is_working") is False:
            url = ch.get("url", "")
            if url:
                non_working.add(url)
    return non_working

"""PrivateBin integration for sharing scan results."""

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
PASTE_EXPIRY = "4hour"  # Expire after 4 hours
SETTINGS_FILE = "privatebin_cache.json"


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
    return _load_settings().get("enabled", False)


def set_enabled(enabled: bool):
    """Enable or disable PrivateBin sharing."""
    settings = _load_settings()
    settings["enabled"] = enabled
    _save_settings(settings)
    logger.info(f"PrivateBin sharing {'enabled' if enabled else 'disabled'}")


def upload_scan_results(channels: List[Dict[str, Any]]) -> Optional[str]:
    """
    Upload scan results to PrivateBin.
    
    Args:
        channels: List of channel dictionaries with scan results
        
    Returns:
        Paste URL if successful, None otherwise
    """
    if not is_enabled():
        return None
    
    try:
        import aiohttp
        import asyncio
    except ImportError:
        logger.error("aiohttp required for PrivateBin integration")
        return None
    
    # Prepare scan data - only include status info
    scan_data = {
        "timestamp": datetime.now().isoformat(),
        "app_version": "1.4.0",
        "channels": []
    }
    
    for ch in channels:
        scan_data["channels"].append({
            "url": ch.get("url", ""),
            "name": ch.get("name", ""),
            "is_working": ch.get("is_working"),
            "last_scanned": ch.get("last_scanned", "")
        })
    
    # Convert to JSON
    data_json = json.dumps(scan_data, ensure_ascii=False)
    
    async def _upload():
        try:
            # Compress data
            compressed = zlib.compress(data_json.encode('utf-8'))
            data_b64 = base64.b64encode(compressed).decode('ascii')
            
            # Create paste data
            paste_data = {
                "v": 2,
                "ct": data_b64,
                "meta": {
                    "expire": PASTE_EXPIRY,
                    "formatter": "plaintext"
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{PRIVATEBIN_URL}",
                    json=paste_data,
                    headers={"Content-Type": "application/json", "X-Requested-With": "JSONHttpRequest"}
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get("status") == 0:
                            paste_id = result.get("id", "")
                            # NOTE: Don't store deletetoken for security reasons
                            
                            # Save only paste_id and timestamp to settings
                            settings = _load_settings()
                            settings["paste_id"] = paste_id
                            settings["timestamp"] = datetime.now().isoformat()
                            _save_settings(settings)
                            
                            paste_url = f"{PRIVATEBIN_URL}/?{paste_id}"
                            logger.info(f"Uploaded scan results to PrivateBin: {paste_url}")
                            return paste_url
                    
                    logger.error(f"PrivateBin upload failed: {resp.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"PrivateBin upload error: {e}")
            return None
    
    # Run async upload
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_upload())
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Failed to run upload: {e}")
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

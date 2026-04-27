"""Auto-update version checker for TV Viewer.

Checks the latest GitHub release tag on startup and notifies the user
if a newer version is available. Rate-limited to one check per 24 hours.
"""

import json
import os
import time
import threading
import webbrowser

import config

_RELEASES_API = "https://api.github.com/repos/tv-viewer-app/tv_viewer/releases/latest"
_RELEASES_PAGE = "https://github.com/tv-viewer-app/tv_viewer/releases"
_STATE_FILE = os.path.join(config.BASE_DIR, ".update_check.json")
_CHECK_INTERVAL = 24 * 3600  # 24 hours in seconds


def _parse_version(version_str: str):
    """Parse '2.6.4' into tuple of ints."""
    parts = version_str.lstrip("v").split(".")
    result = []
    for p in parts[:3]:
        try:
            result.append(int(p))
        except (ValueError, TypeError):
            result.append(0)
    while len(result) < 3:
        result.append(0)
    return tuple(result)


def _load_state() -> dict:
    """Load last check state from disk."""
    try:
        if os.path.exists(_STATE_FILE):
            with open(_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_state(state: dict):
    """Save check state to disk."""
    try:
        with open(_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass


def check_for_update_async(callback):
    """Check for updates in a background thread.
    
    Args:
        callback: Function(latest_version: str) called on the main thread
                  if a newer version is available. Called with None if up-to-date.
    """
    def _check():
        try:
            state = _load_state()
            last_check = state.get("last_check", 0)
            dismissed = state.get("dismissed_version", "")
            
            # Rate-limit
            if time.time() - last_check < _CHECK_INTERVAL:
                return
            
            import requests
            resp = requests.get(
                _RELEASES_API,
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=10,
            )
            
            # Save timestamp regardless of result
            state["last_check"] = time.time()
            _save_state(state)
            
            if resp.status_code != 200:
                return
            
            data = resp.json()
            tag = data.get("tag_name", "")
            latest = _parse_version(tag)
            current = _parse_version(config.APP_VERSION)
            
            if latest > current and tag.lstrip("v") != dismissed:
                callback(tag.lstrip("v"))
        except Exception as e:
            print(f"Update check failed (non-critical): {e}")
    
    thread = threading.Thread(target=_check, daemon=True)
    thread.start()


def dismiss_version(version: str):
    """Dismiss the update notification for a specific version."""
    state = _load_state()
    state["dismissed_version"] = version
    _save_state(state)


def open_releases_page():
    """Open the GitHub releases page in the default browser."""
    webbrowser.open(_RELEASES_PAGE)

"""Watch history / recently played tracker for TV Viewer.

Tracks recently played channels with play counts and timestamps.
Thread-safe, with debounced auto-save to avoid excessive disk writes.
"""

import json
import os
import threading
import time
from typing import Dict, List, Optional, Any

from utils.logger import get_logger
import config

logger = get_logger(__name__)

HISTORY_FILENAME = "watch_history.json"
DEFAULT_MAX_ENTRIES = 50
SAVE_DEBOUNCE_SECONDS = 2.0


class WatchHistory:
    """Manages watch history with thread-safe, debounced persistence.

    Stores recently played channels in a JSON file inside config.BASE_DIR.
    Each entry contains:
        - name, url, country, category
        - last_played  (epoch timestamp)
        - play_count   (int)

    At most *max_entries* are kept; the oldest by last_played are dropped
    when the limit is exceeded.
    """

    def __init__(
        self,
        filepath: Optional[str] = None,
        max_entries: int = DEFAULT_MAX_ENTRIES,
    ):
        self._filepath = filepath or os.path.join(config.BASE_DIR, HISTORY_FILENAME)
        self._max_entries = max_entries
        self._lock = threading.Lock()
        self._entries: Dict[str, Dict[str, Any]] = {}  # keyed by URL
        self._save_timer: Optional[threading.Timer] = None
        self._dirty = False
        self._load()

    # ── Public API ────────────────────────────────────────────────────

    def record_play(self, channel: dict) -> None:
        """Record (or update) a channel play in history.

        *channel* must have at least a ``url`` key.  ``name``, ``country``
        and ``category`` are optional but recommended.
        """
        url = channel.get("url", "")
        if not url:
            return

        with self._lock:
            existing = self._entries.get(url)
            now = time.time()

            if existing:
                existing["play_count"] = existing.get("play_count", 0) + 1
                existing["last_played"] = now
                # Update mutable metadata in case it changed
                existing["name"] = channel.get("name", existing.get("name", ""))
                existing["country"] = channel.get("country", existing.get("country", ""))
                existing["category"] = channel.get("category", existing.get("category", ""))
            else:
                self._entries[url] = {
                    "name": channel.get("name", ""),
                    "url": url,
                    "country": channel.get("country", ""),
                    "category": channel.get("category", ""),
                    "last_played": now,
                    "play_count": 1,
                }

            self._enforce_limit()
            self._dirty = True

        self._schedule_save()

    def get_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return up to *limit* entries sorted by last_played descending."""
        with self._lock:
            entries = list(self._entries.values())
        entries.sort(key=lambda e: e.get("last_played", 0), reverse=True)
        return entries[:limit]

    def get_most_played(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return up to *limit* entries sorted by play_count descending."""
        with self._lock:
            entries = list(self._entries.values())
        entries.sort(key=lambda e: e.get("play_count", 0), reverse=True)
        return entries[:limit]

    def remove(self, url: str) -> None:
        """Remove a specific entry by URL."""
        with self._lock:
            if url in self._entries:
                del self._entries[url]
                self._dirty = True
        self._schedule_save()

    def clear(self) -> None:
        """Remove all history entries."""
        with self._lock:
            self._entries.clear()
            self._dirty = True
        self._schedule_save()

    # ── Persistence ───────────────────────────────────────────────────

    def _load(self) -> None:
        """Load history from disk."""
        try:
            if os.path.exists(self._filepath):
                with open(self._filepath, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                entries_list = data if isinstance(data, list) else data.get("entries", [])
                for entry in entries_list:
                    url = entry.get("url", "")
                    if url:
                        self._entries[url] = entry
                self._enforce_limit()
                logger.info(
                    "Loaded %d watch history entries from %s",
                    len(self._entries),
                    self._filepath,
                )
        except Exception as exc:
            logger.error("Failed to load watch history: %s", exc)
            self._entries = {}

    def _save(self) -> None:
        """Write history to disk (called by debounce timer)."""
        with self._lock:
            if not self._dirty:
                return
            entries = list(self._entries.values())
            self._dirty = False

        try:
            data = {"entries": entries}
            # Atomic-ish write: write to temp then rename
            tmp_path = self._filepath + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
            # os.replace is atomic on most OSes
            os.replace(tmp_path, self._filepath)
            logger.debug("Saved %d watch history entries", len(entries))
        except Exception as exc:
            logger.error("Failed to save watch history: %s", exc)

    def _schedule_save(self) -> None:
        """Debounce saves — schedule a write after SAVE_DEBOUNCE_SECONDS."""
        with self._lock:
            if self._save_timer is not None:
                self._save_timer.cancel()
            self._save_timer = threading.Timer(SAVE_DEBOUNCE_SECONDS, self._save)
            self._save_timer.daemon = True
            self._save_timer.start()

    def flush(self) -> None:
        """Force an immediate save (e.g. on app shutdown)."""
        with self._lock:
            if self._save_timer is not None:
                self._save_timer.cancel()
                self._save_timer = None
        self._save()

    # ── Internal helpers ──────────────────────────────────────────────

    def _enforce_limit(self) -> None:
        """Drop oldest entries when over *max_entries*.  Caller must hold lock."""
        if len(self._entries) <= self._max_entries:
            return
        # Sort by last_played ascending → oldest first
        sorted_urls = sorted(
            self._entries,
            key=lambda u: self._entries[u].get("last_played", 0),
        )
        excess = len(self._entries) - self._max_entries
        for url in sorted_urls[:excess]:
            del self._entries[url]

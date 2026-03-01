"""Anonymous, privacy-first analytics service backed by Supabase REST API.

Collects lightweight, anonymous usage telemetry (app launches, stream
failures, scan stats, crashes) for improving TV Viewer.  No PII is ever
collected — channel URLs are SHA-256 hashed, and the only identifier is a
random UUID stored locally.

The service is **auto-enabled** when ``SUPABASE_URL`` and
``SUPABASE_ANON_KEY`` environment variables are set (same pattern as
:mod:`utils.shared_db`).

Database table (Supabase)::

    analytics_events
      id            — bigint, auto-increment (primary key)
      device_id     — uuid (anonymous install identifier)
      event_type    — text
      event_data    — jsonb
      app_version   — text
      platform      — text ('windows')
      created_at    — timestamptz (default now())

Usage::

    from utils.analytics import analytics

    # During app startup
    await analytics.initialize()
    await analytics.track_app_launch()

    # During playback
    await analytics.track_channel_play('http://example.com/stream.m3u8')

    # On errors
    await analytics.track_channel_fail('http://...', 'timeout')

    # Before exit
    await analytics.flush()
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import sys
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import aiohttp
except ImportError:
    aiohttp = None  # type: ignore[assignment]

from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Supabase configuration — loaded from environment variables (SEC-003)
# ---------------------------------------------------------------------------
SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY: str = os.environ.get("SUPABASE_ANON_KEY", "")
TABLE_NAME: str = "analytics_events"

# Feature flag — automatically enabled when env vars are set.
ENABLED: bool = bool(SUPABASE_URL and SUPABASE_ANON_KEY)

# Flush when the queue reaches this size.
MAX_QUEUE_SIZE: int = 20

# Persistent file that stores the anonymous device UUID.
_DEVICE_ID_PATH: Path = Path.home() / ".tv_viewer_analytics_id"

# App version — resolved once at import time.
try:
    import config as _cfg
    _APP_VERSION: str = getattr(_cfg, "APP_VERSION", "unknown")
except Exception:
    _APP_VERSION = "unknown"

_PLATFORM: str = "windows" if sys.platform == "win32" else platform.system().lower()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash_url(url: str) -> str:
    """Return the hex SHA-256 digest of *url*."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def _load_or_create_device_id() -> str:
    """Load the anonymous device UUID from disk, or create one on first run."""
    try:
        if _DEVICE_ID_PATH.exists():
            stored = _DEVICE_ID_PATH.read_text(encoding="utf-8").strip()
            if stored:
                return stored
    except Exception:
        pass

    device_id = str(uuid.uuid4())
    try:
        _DEVICE_ID_PATH.parent.mkdir(parents=True, exist_ok=True)
        _DEVICE_ID_PATH.write_text(device_id, encoding="utf-8")
    except Exception as exc:
        logger.warning("Failed to persist analytics device ID: %s", exc)
    return device_id


# ---------------------------------------------------------------------------
# AnalyticsService
# ---------------------------------------------------------------------------

class AnalyticsService:
    """Singleton analytics collector that batches events to Supabase.

    All public methods are fail-safe — exceptions are logged but never
    propagated to the caller so that analytics can never crash the app.
    """

    _instance: Optional["AnalyticsService"] = None

    def __new__(cls) -> "AnalyticsService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False  # type: ignore[attr-defined]
        return cls._instance

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        # Guard against re-init on repeated __init__ calls from __new__.
        if getattr(self, "_initialized", False):
            return
        self._initialized: bool = False
        self._device_id: str = ""
        self._queue: List[Dict[str, Any]] = []

    async def initialize(self) -> None:
        """Load/generate device ID.  Safe to call multiple times."""
        if self._initialized:
            return
        try:
            self._device_id = _load_or_create_device_id()
            self._initialized = True

            if self.is_configured:
                logger.info(
                    "Analytics initialised — device=%s, platform=%s, version=%s",
                    self._device_id,
                    _PLATFORM,
                    _APP_VERSION,
                )
            else:
                logger.info("Analytics disabled (Supabase env vars not set)")
        except Exception as exc:
            logger.warning("Analytics initialisation failed: %s", exc)
            self._initialized = True  # don't block callers

    @property
    def is_configured(self) -> bool:
        """``True`` when Supabase credentials look valid."""
        return (
            ENABLED
            and aiohttp is not None
            and SUPABASE_URL != "YOUR_SUPABASE_PROJECT_URL"
            and SUPABASE_ANON_KEY != "YOUR_SUPABASE_ANON_KEY"
        )

    @property
    def queue_length(self) -> int:
        """Number of events waiting to be flushed."""
        return len(self._queue)

    # ------------------------------------------------------------------
    # Generic event tracking
    # ------------------------------------------------------------------

    async def track_event(
        self, event_type: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Enqueue an analytics event.  Auto-flushes at *MAX_QUEUE_SIZE*."""
        if not self._initialized:
            await self.initialize()
        if not self.is_configured:
            return

        try:
            event: Dict[str, Any] = {
                "device_id": self._device_id,
                "event_type": event_type,
                "event_data": data or {},
                "app_version": _APP_VERSION,
                "platform": _PLATFORM,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._queue.append(event)
            logger.debug(
                "Analytics queued event: %s (queue=%d)",
                event_type,
                len(self._queue),
            )

            if len(self._queue) >= MAX_QUEUE_SIZE:
                await self.flush()
        except Exception as exc:
            logger.warning("Failed to queue analytics event '%s': %s", event_type, exc)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    async def track_app_launch(self) -> None:
        """Record an app-launch event with platform metadata."""
        await self.track_event("app_launch", {
            "platform_os": _PLATFORM,
            "python_version": platform.python_version(),
            "app_version": _APP_VERSION,
        })

    async def track_channel_play(self, url: str) -> None:
        """Record that a channel was played (*url* is SHA-256 hashed)."""
        await self.track_event("channel_play", {
            "url_hash": _hash_url(url),
        })

    async def track_channel_fail(self, url: str, error: str) -> None:
        """Record a stream-play failure (*url* is SHA-256 hashed)."""
        await self.track_event("channel_fail", {
            "url_hash": _hash_url(url),
            "error_code": error,
        })

    async def track_scan_complete(
        self,
        working: int,
        failed: int,
        duration_seconds: float,
    ) -> None:
        """Record the result of a channel-validation scan."""
        await self.track_event("scan_complete", {
            "working_count": working,
            "failed_count": failed,
            "duration_ms": int(duration_seconds * 1000),
        })

    async def track_crash(
        self,
        error: BaseException,
        tb: Optional[Any] = None,
    ) -> None:
        """Record an uncaught exception (first stack-trace line only)."""
        first_line = ""
        try:
            if tb is not None:
                lines = traceback.format_tb(tb)
                if lines:
                    first_line = lines[-1].strip().split("\n")[0]
            elif error.__traceback__ is not None:
                lines = traceback.format_tb(error.__traceback__)
                if lines:
                    first_line = lines[-1].strip().split("\n")[0]
        except Exception:
            pass

        error_msg = str(error)
        if len(error_msg) > 200:
            error_msg = error_msg[:200]

        await self.track_event("app_crash", {
            "error_type": type(error).__name__,
            "error_message": error_msg,
            "stack_first_line": first_line,
        })
        # Flush immediately — the process may be about to exit.
        await self.flush()

    # ------------------------------------------------------------------
    # Flush
    # ------------------------------------------------------------------

    async def flush(self) -> None:
        """Send all queued events to the Supabase ``analytics_events`` table.

        On failure the events are re-queued (capped at 100 to prevent
        unbounded memory growth).
        """
        if not self._queue or not self.is_configured:
            return

        batch = list(self._queue)
        self._queue.clear()

        try:
            url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"
            headers = {
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=batch,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status in (200, 201):
                        logger.debug(
                            "Analytics flushed %d events successfully",
                            len(batch),
                        )
                    else:
                        body = await response.text()
                        logger.warning(
                            "Analytics flush failed: %d — %s",
                            response.status,
                            body,
                        )
                        self._requeue(batch)
        except Exception as exc:
            logger.warning("Analytics flush error: %s", exc)
            self._requeue(batch)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _requeue(self, events: List[Dict[str, Any]]) -> None:
        """Push failed events back onto the queue (capped at 100)."""
        self._queue = events + self._queue
        if len(self._queue) > 100:
            self._queue = self._queue[-100:]


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
analytics = AnalyticsService()

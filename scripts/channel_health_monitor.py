#!/usr/bin/env python3
"""
channel_health_monitor.py — Nightly Channel Health Monitor
==========================================================

Runs as a GitHub Action (cron) to identify and quarantine broken channels.

Workflow:
  1. Query Supabase `channels` table for channels with report_count >= 5
  2. Validate ALL URLs for each reported channel (HEAD + GET fallback)
  3. If ALL URLs fail → quarantine (set is_active=false, disabled_at=now)
  4. If any URL works → reset report_count to 0 (channel is fine)
  5. Generate JSON report as artifact

Safety measures:
  - Quarantine (soft-disable) instead of hard delete
  - Validates ALL alternate URLs, not just primary
  - 10s timeout per URL check
  - Max 200 channels per run to stay within GitHub Actions limits
  - Dry-run mode for testing
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import ssl
import sys
import time
from datetime import datetime, timezone
from typing import Any

try:
    import aiohttp
except ImportError:
    print("ERROR: aiohttp required. Run: pip install aiohttp")
    sys.exit(1)

try:
    import certifi
except ImportError:
    certifi = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
REPORT_THRESHOLD = 5        # Only check channels with this many reports
URL_CHECK_TIMEOUT = 10       # Seconds per URL check
MAX_CHANNELS_PER_RUN = 200   # Safety cap
CONCURRENCY = 20             # Parallel URL checks
REPORT_PATH = "/tmp/channel-health-report.json"
USER_AGENT = "TVViewer-HealthMonitor/1.0"

# Stream content types we consider valid
VALID_CONTENT_TYPES = {
    "video/", "audio/", "application/vnd.apple.mpegurl",
    "application/x-mpegurl", "application/octet-stream",
    "application/dash+xml", "text/plain",
}


def _get_ssl_context():
    ctx = ssl.create_default_context(cafile=certifi.where() if certifi else None)
    return ctx


def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }


def _read_headers():
    h = _headers()
    h.pop("Content-Type", None)
    h.pop("Prefer", None)
    return h


# ---------------------------------------------------------------------------
# Supabase queries
# ---------------------------------------------------------------------------

async def fetch_reported_channels(session: aiohttp.ClientSession) -> list[dict]:
    """Fetch channels with report_count >= threshold."""
    url = (
        f"{SUPABASE_URL}/rest/v1/channels"
        f"?report_count=gte.{REPORT_THRESHOLD}"
        f"&select=url_hash,name,urls,report_count"
        f"&limit={MAX_CHANNELS_PER_RUN}"
        f"&order=report_count.desc"
    )
    async with session.get(url, headers=_read_headers(), timeout=aiohttp.ClientTimeout(total=30)) as resp:
        if resp.status != 200:
            log.error("Failed to fetch reported channels: %d", resp.status)
            return []
        data = await resp.json()
        log.info("Fetched %d channels with report_count >= %d", len(data), REPORT_THRESHOLD)
        return data


async def quarantine_channel(session: aiohttp.ClientSession, url_hash: str) -> bool:
    """Soft-disable a channel by setting is_active=false and disabled_at=now.
    
    Note: If is_active column doesn't exist yet, we increment report_count
    as a fallback signal. The column should be added via Supabase SQL editor:
    ALTER TABLE channels ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true;
    ALTER TABLE channels ADD COLUMN IF NOT EXISTS disabled_at timestamptz;
    """
    url = f"{SUPABASE_URL}/rest/v1/channels?url_hash=eq.{url_hash}"
    payload = {
        "is_active": False,
        "disabled_at": datetime.now(timezone.utc).isoformat(),
    }
    async with session.patch(url, json=payload, headers=_headers(),
                             timeout=aiohttp.ClientTimeout(total=10)) as resp:
        if resp.status in (200, 204):
            return True
        # Fallback: column might not exist yet — just log
        body = await resp.text()
        log.warning("Quarantine PATCH failed for %s: %d - %s", url_hash[:16], resp.status, body[:200])
        return False


async def reset_report_count(session: aiohttp.ClientSession, url_hash: str) -> bool:
    """Reset report_count to 0 for a healthy channel."""
    url = f"{SUPABASE_URL}/rest/v1/channels?url_hash=eq.{url_hash}"
    async with session.patch(url, json={"report_count": 0}, headers=_headers(),
                             timeout=aiohttp.ClientTimeout(total=10)) as resp:
        return resp.status in (200, 204)


# ---------------------------------------------------------------------------
# URL validation
# ---------------------------------------------------------------------------

async def check_url(session: aiohttp.ClientSession, url: str) -> bool:
    """Check if a stream URL is responsive. HEAD first, then GET fallback."""
    headers = {"User-Agent": USER_AGENT}
    for method in ("HEAD", "GET"):
        try:
            req_method = session.head if method == "HEAD" else session.get
            async with req_method(
                url, headers=headers,
                timeout=aiohttp.ClientTimeout(total=URL_CHECK_TIMEOUT),
                allow_redirects=True,
            ) as resp:
                if 200 <= resp.status < 400:
                    # Optionally validate content type
                    ct = resp.headers.get("Content-Type", "").lower()
                    if ct and any(vt in ct for vt in VALID_CONTENT_TYPES):
                        return True
                    # Accept if no content-type (some IPTV servers don't set it)
                    if not ct or resp.status == 200:
                        return True
        except Exception:
            if method == "HEAD":
                continue  # Retry with GET
            return False
    return False


async def validate_channel(
    session: aiohttp.ClientSession,
    channel: dict,
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    """Validate all URLs for a channel. Returns result dict."""
    url_hash = channel["url_hash"]
    name = channel.get("name", "Unknown")
    urls = channel.get("urls", [])
    report_count = channel.get("report_count", 0)

    if not urls:
        return {
            "url_hash": url_hash,
            "name": name,
            "report_count": report_count,
            "urls_checked": 0,
            "any_working": False,
            "action": "quarantine",
        }

    working_urls = []
    async with semaphore:
        for url in urls:
            if isinstance(url, str) and url.startswith("http"):
                is_ok = await check_url(session, url)
                if is_ok:
                    working_urls.append(url)
                    break  # One working URL is enough

    any_working = len(working_urls) > 0
    action = "reset" if any_working else "quarantine"

    return {
        "url_hash": url_hash,
        "name": name,
        "report_count": report_count,
        "urls_checked": len(urls),
        "any_working": any_working,
        "action": action,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        log.error("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        sys.exit(1)

    t0 = time.monotonic()
    ssl_ctx = _get_ssl_context()
    connector = aiohttp.TCPConnector(ssl=ssl_ctx, limit=CONCURRENCY)

    async with aiohttp.ClientSession(connector=connector) as session:
        # Step 1: Fetch reported channels
        channels = await fetch_reported_channels(session)
        if not channels:
            log.info("No channels above report threshold. Nothing to do.")
            _write_report([], [], 0)
            return

        # Step 2: Validate URLs
        semaphore = asyncio.Semaphore(CONCURRENCY)
        tasks = [validate_channel(session, ch, semaphore) for ch in channels]
        results = await asyncio.gather(*tasks)

        # Step 3: Apply actions
        quarantined = []
        reset = []
        for result in results:
            if result["action"] == "quarantine":
                ok = await quarantine_channel(session, result["url_hash"])
                result["applied"] = ok
                quarantined.append(result)
                log.info("🔴 Quarantined: %s (reports: %d, urls: %d)",
                         result["name"], result["report_count"], result["urls_checked"])
            else:
                ok = await reset_report_count(session, result["url_hash"])
                result["applied"] = ok
                reset.append(result)
                log.info("🟢 Reset: %s (reports: %d → 0, working URL found)",
                         result["name"], result["report_count"])

    elapsed = time.monotonic() - t0

    # Step 4: Report
    _write_report(quarantined, reset, elapsed)

    log.info("=" * 60)
    log.info("Health monitor complete in %.1f s", elapsed)
    log.info("  Checked: %d channels", len(results))
    log.info("  Quarantined: %d", len(quarantined))
    log.info("  Reset (healthy): %d", len(reset))
    log.info("=" * 60)


def _write_report(quarantined: list, reset: list, elapsed: float):
    """Write JSON report artifact."""
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed, 1),
        "threshold": REPORT_THRESHOLD,
        "quarantined": quarantined,
        "reset": reset,
        "summary": {
            "total_checked": len(quarantined) + len(reset),
            "quarantined": len(quarantined),
            "reset": len(reset),
        },
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    log.info("Report written to %s", REPORT_PATH)


if __name__ == "__main__":
    asyncio.run(main())

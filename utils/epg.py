"""EPG (Electronic Program Guide) service backed by XMLTV data.

Fetches XMLTV program guide data from community EPG sources,
parses it, and provides current/next program lookups for channels.

Sources (configurable):
  - iptv-org community EPG mirrors
  - Open-EPG.com country-based guides
  - Custom XMLTV URLs

Usage::

    from utils.epg import epg_service

    # During app startup (async)
    await epg_service.initialize()

    # Get current program for a channel
    program = epg_service.get_current_program(channel_id="BBCOne.uk")
    # → {'title': 'BBC News', 'start': datetime, 'end': datetime, 'desc': '...'}

    # Get full schedule
    schedule = epg_service.get_schedule(channel_id="BBCOne.uk", hours=6)
"""

from __future__ import annotations

import asyncio
import gzip
import json
import logging
import os
import re
import threading
import time
try:
    import defusedxml.ElementTree as ET  # Safe XML parsing (prevents XXE/billion-laughs)
except ImportError:
    import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

try:
    import aiohttp
except ImportError:
    aiohttp = None  # type: ignore[assignment]

from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Default EPG sources — community XMLTV mirrors (verified working May 2026)
DEFAULT_EPG_SOURCES = [
    # epgshare01 — Israeli EPG (Yes/HOT channels, updated daily)
    "https://epgshare01.online/epgshare01/epg_ripper_IL1.xml.gz",
    # epgshare01 — UK Freeview/Sky channels
    "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz",
    # matthuisman/i.mjh.nz — Pluto TV US
    "https://i.mjh.nz/PlutoTV/us.xml.gz",
    # matthuisman/i.mjh.nz — Samsung TV Plus US
    "https://i.mjh.nz/SamsungTVPlus/us.xml.gz",
    # matthuisman/i.mjh.nz — Plex Live TV
    "https://i.mjh.nz/Plex/us.xml.gz",
    # dp247 — UK Freeview EPG
    "https://raw.githubusercontent.com/dp247/Freeview-EPG/master/epg.xml",
]

# Cache settings
EPG_CACHE_FILE = "epg_cache.json"
EPG_CACHE_MAX_AGE_HOURS = 6
EPG_FETCH_TIMEOUT = 60
EPG_MAX_PROGRAMS_PER_CHANNEL = 48  # ~24 hours of 30-min programs


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

# Hebrew/Arabic → English aliases for major Israeli/MENA channels.
# Channel names on the user's side often arrive in their native script, but EPG
# sources (e.g. epgshare01's IL1.xml.gz) publish display names in English. We
# translate before fuzzy-matching so the existing tier-1/tier-2 logic can find
# them.
_LOCALE_CHANNEL_ALIASES: Dict[str, str] = {
    # Israeli channels (Hebrew)
    "ערוץ 14": "Channel 14",
    "ערוץ 13": "Channel 13",
    "ערוץ 12": "Channel 12",
    "ערוץ 11": "Kan 11",
    "ערוץ 10": "Channel 10",
    "ערוץ 9": "Channel 9",
    "ערוץ 24": "Channel 24",
    "ערוץ 20": "Channel 20",
    "כאן 11": "Kan 11",
    "כאן": "Kan 11",
    "קשת 12": "Keshet 12",
    "קשת": "Keshet 12",
    "רשת 13": "Reshet 13",
    "רשת": "Reshet 13",
    "ספורט 1": "Sport 1",
    "ספורט 2": "Sport 2",
    "ספורט 3": "Sport 3",
    "ספורט 4": "Sport 4",
    "ספורט 5": "Sport 5",
    "ספורט": "Sport 1",
    "ynet": "Ynet",
    "ynet news": "Ynetnews",
    "מאקו": "Mako",
    "הכאן חדשות": "Kan News",
    "הכנסת": "Knesset",
    "כנסת": "Knesset",
    "i24 news": "i24NEWS",
}


def _alias_channel(name: str) -> str:
    """Map a localized channel name to its English equivalent if known."""
    if not name:
        return name
    key = name.strip().lower()
    return _LOCALE_CHANNEL_ALIASES.get(key, name)


class EPGProgram:
    """A single TV program in the EPG."""
    __slots__ = ('title', 'start', 'end', 'description', 'category',
                 'channel_id', 'subtitle', 'icon')

    def __init__(self, title: str, start: datetime, end: datetime,
                 channel_id: str = "", description: str = "",
                 category: str = "", subtitle: str = "", icon: str = ""):
        self.title = title
        self.start = start
        self.end = end
        self.channel_id = channel_id
        self.description = description
        self.category = category
        self.subtitle = subtitle
        self.icon = icon

    def is_current(self, now: Optional[datetime] = None) -> bool:
        """Check if this program is currently airing."""
        now = now or datetime.now(timezone.utc)
        return self.start <= now < self.end

    def is_upcoming(self, now: Optional[datetime] = None) -> bool:
        """Check if this program hasn't started yet."""
        now = now or datetime.now(timezone.utc)
        return self.start > now

    @property
    def duration_minutes(self) -> int:
        return int((self.end - self.start).total_seconds() / 60)

    @property
    def progress_percent(self) -> float:
        """Percentage of the program that has elapsed (0-100)."""
        now = datetime.now(timezone.utc)
        if now < self.start:
            return 0.0
        if now >= self.end:
            return 100.0
        total = (self.end - self.start).total_seconds()
        elapsed = (now - self.start).total_seconds()
        return min(100.0, (elapsed / total) * 100) if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'start': self.start.isoformat(),
            'end': self.end.isoformat(),
            'channel_id': self.channel_id,
            'description': self.description,
            'category': self.category,
            'subtitle': self.subtitle,
            'icon': self.icon,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'EPGProgram':
        return cls(
            title=d.get('title', ''),
            start=datetime.fromisoformat(d['start']),
            end=datetime.fromisoformat(d['end']),
            channel_id=d.get('channel_id', ''),
            description=d.get('description', ''),
            category=d.get('category', ''),
            subtitle=d.get('subtitle', ''),
            icon=d.get('icon', ''),
        )


# ---------------------------------------------------------------------------
# XMLTV Parser
# ---------------------------------------------------------------------------

def _parse_xmltv_datetime(dt_str: str) -> Optional[datetime]:
    """Parse XMLTV datetime format: 20250416200000 +0300"""
    if not dt_str:
        return None
    dt_str = dt_str.strip()
    # Common formats: "20250416200000 +0300" or "20250416200000"
    try:
        # Try with timezone offset
        match = re.match(r'(\d{14})\s*([+-]\d{4})?', dt_str)
        if not match:
            return None
        base = match.group(1)
        tz_str = match.group(2)

        dt = datetime.strptime(base, '%Y%m%d%H%M%S')

        if tz_str:
            sign = 1 if tz_str[0] == '+' else -1
            hours = int(tz_str[1:3])
            minutes = int(tz_str[3:5])
            offset = timedelta(hours=sign * hours, minutes=sign * minutes)
            dt = dt.replace(tzinfo=timezone(offset))
        else:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt
    except (ValueError, IndexError):
        return None


def parse_xmltv(xml_content: str) -> Tuple[Dict[str, str], Dict[str, List[EPGProgram]]]:
    """Parse XMLTV content into channel names and program schedules.

    Returns:
        (channel_map, schedules) where:
        - channel_map: {channel_id: display_name}
        - schedules: {channel_id: [EPGProgram, ...]} sorted by start time
    """
    channel_map: Dict[str, str] = {}
    schedules: Dict[str, List[EPGProgram]] = {}

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        logger.debug("Failed to parse XMLTV: %s", e)
        return channel_map, schedules

    # Parse <channel> elements
    for ch_elem in root.findall('.//channel'):
        ch_id = ch_elem.get('id', '')
        if not ch_id:
            continue
        name_elem = ch_elem.find('display-name')
        if name_elem is not None and name_elem.text:
            channel_map[ch_id] = name_elem.text.strip()

    # Parse <programme> elements
    now = datetime.now(timezone.utc)
    cutoff_past = now - timedelta(hours=2)
    cutoff_future = now + timedelta(hours=24)

    for prog_elem in root.findall('.//programme'):
        ch_id = prog_elem.get('channel', '')
        start_str = prog_elem.get('start', '')
        end_str = prog_elem.get('stop', '')

        if not ch_id or not start_str:
            continue

        start = _parse_xmltv_datetime(start_str)
        end = _parse_xmltv_datetime(end_str) if end_str else None

        if not start:
            continue
        if not end:
            end = start + timedelta(minutes=30)  # default 30-min slot

        # Only keep programs within a useful window
        if end < cutoff_past or start > cutoff_future:
            continue

        # Extract metadata
        title = ""
        title_elem = prog_elem.find('title')
        if title_elem is not None and title_elem.text:
            title = title_elem.text.strip()

        desc = ""
        desc_elem = prog_elem.find('desc')
        if desc_elem is not None and desc_elem.text:
            desc = desc_elem.text.strip()[:500]  # cap description length

        category = ""
        cat_elem = prog_elem.find('category')
        if cat_elem is not None and cat_elem.text:
            category = cat_elem.text.strip()

        subtitle = ""
        sub_elem = prog_elem.find('sub-title')
        if sub_elem is not None and sub_elem.text:
            subtitle = sub_elem.text.strip()

        icon = ""
        icon_elem = prog_elem.find('icon')
        if icon_elem is not None:
            icon = icon_elem.get('src', '')

        program = EPGProgram(
            title=title, start=start, end=end, channel_id=ch_id,
            description=desc, category=category, subtitle=subtitle, icon=icon,
        )

        if ch_id not in schedules:
            schedules[ch_id] = []
        schedules[ch_id].append(program)

    # Sort each channel's programs by start time and cap
    for ch_id in schedules:
        schedules[ch_id].sort(key=lambda p: p.start)
        if len(schedules[ch_id]) > EPG_MAX_PROGRAMS_PER_CHANNEL:
            schedules[ch_id] = schedules[ch_id][:EPG_MAX_PROGRAMS_PER_CHANNEL]

    logger.info("Parsed XMLTV: %d channels, %d total programs",
                len(channel_map),
                sum(len(v) for v in schedules.values()))

    return channel_map, schedules


# ---------------------------------------------------------------------------
# EPG Service (singleton)
# ---------------------------------------------------------------------------

class EPGService:
    """Manages EPG data: fetch, parse, cache, and lookup."""

    def __init__(self):
        self._lock = threading.Lock()
        self._init_state_lock = threading.Lock()
        self._channel_map: Dict[str, str] = {}          # epg_id → display_name
        self._schedules: Dict[str, List[EPGProgram]] = {}  # epg_id → [programs]
        self._name_to_epg_id: Dict[str, str] = {}       # lowercase name → epg_id
        self._initialized = False
        self._initializing = False
        self._last_fetch: float = 0
        # When a full-fetch failure happens (all sources returned 0 channels)
        # we set this so subsequent endpoint hits don't re-trigger a fetch
        # storm. Reset on success or when sources change.
        self._last_failed_fetch: float = 0
        self._epg_sources: List[str] = list(DEFAULT_EPG_SOURCES)

        # Load cached data if available
        try:
            self._load_cache()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def initialize(self, sources: Optional[List[str]] = None) -> None:
        """Fetch and parse EPG data from configured sources."""
        with self._init_state_lock:
            if self._initializing:
                return
            self._initializing = True
        try:
            await self._do_initialize(sources)
        finally:
            with self._init_state_lock:
                self._initializing = False

    async def _do_initialize(self, sources: Optional[List[str]] = None) -> None:
        """Internal initialization logic."""
        if sources:
            self._epg_sources = sources

        # Check if cache is fresh enough
        cache_age_hours = (time.time() - self._last_fetch) / 3600
        if self._initialized and cache_age_hours < EPG_CACHE_MAX_AGE_HOURS:
            logger.info("EPG cache still fresh (%.1fh old), skipping fetch", cache_age_hours)
            return

        # Cooldown after a recent total failure — don't hammer upstream
        # sources every time an /api/epg/<channel> request lands.
        EPG_FAILURE_COOLDOWN_SEC = 300  # 5 minutes
        if (self._last_failed_fetch
                and (time.time() - self._last_failed_fetch) < EPG_FAILURE_COOLDOWN_SEC):
            since = int(time.time() - self._last_failed_fetch)
            logger.debug("EPG fetch in cooldown (%ds since last failure), skipping", since)
            return

        if aiohttp is None:
            logger.warning("aiohttp not available — EPG disabled")
            return

        logger.info("Fetching EPG data from %d sources...", len(self._epg_sources))
        all_channels: Dict[str, str] = {}
        all_schedules: Dict[str, List[EPGProgram]] = {}

        # SSL context with certifi (fixes Docker/Alpine cert issues)
        import ssl
        try:
            import certifi
            ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            ssl_ctx = ssl.create_default_context()

        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        headers = {
            "User-Agent": "TVViewer/2.16 EPG-Fetcher",
            # Tell upstream not to wrap the .gz payload in another gzip layer.
            # Some CDNs send Content-Encoding: gzip *on* application/gzip files,
            # which causes aiohttp to auto-decompress before our code can see
            # the raw .gz bytes, producing "compressed file ended before
            # end-of-stream" failures across every source. auto_decompress=False
            # below is the defensive belt; this header is the suspenders.
            "Accept-Encoding": "identity",
        }
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=EPG_FETCH_TIMEOUT),
            headers=headers,
            auto_decompress=False,
        ) as session:
            tasks = [self._fetch_source(session, url) for url in self._epg_sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        for url, result in zip(self._epg_sources, results):
            if isinstance(result, Exception):
                logger.warning("EPG source %s raised %s: %s",
                               url, type(result).__name__, result)
                continue
            channels, schedules = result
            if not channels:
                # _fetch_source already logged the reason at WARNING
                continue
            all_channels.update(channels)
            for ch_id, programs in schedules.items():
                if ch_id in all_schedules:
                    all_schedules[ch_id].extend(programs)
                else:
                    all_schedules[ch_id] = programs

        # Deduplicate and sort
        for ch_id in all_schedules:
            seen = set()
            unique = []
            for p in all_schedules[ch_id]:
                key = (p.title, p.start.isoformat())
                if key not in seen:
                    seen.add(key)
                    unique.append(p)
            unique.sort(key=lambda p: p.start)
            all_schedules[ch_id] = unique[:EPG_MAX_PROGRAMS_PER_CHANNEL]

        with self._lock:
            # Refuse to overwrite a populated in-memory map with an empty
            # result (all sources failed). Without this guard a transient
            # network failure on the next refresh would wipe a working cache.
            if not all_channels and self._channel_map:
                logger.warning(
                    "EPG fetch returned 0 channels — keeping existing %d-channel cache",
                    len(self._channel_map),
                )
                # Mark failure so we apply cooldown to subsequent retries.
                self._last_failed_fetch = time.time()
                return
            self._channel_map = all_channels
            self._schedules = all_schedules
            self._build_name_index()
            self._initialized = bool(all_channels)
            if all_channels:
                self._last_fetch = time.time()
                self._last_failed_fetch = 0  # clear cooldown on success
            else:
                self._last_fetch = 0
                self._last_failed_fetch = time.time()

        logger.info("EPG loaded: %d channels, %d programs",
                     len(all_channels),
                     sum(len(v) for v in all_schedules.values()))

        # Save to cache — only if we actually got data (don't poison disk
        # cache with an empty result that would block future fetches).
        if all_channels:
            try:
                self._save_cache()
            except Exception as e:
                logger.warning("Failed to save EPG cache: %s", e)

    def get_current_program(self, channel_name: str = "",
                             channel_id: str = "") -> Optional[EPGProgram]:
        """Get the currently airing program for a channel."""
        with self._lock:
            epg_id = self._resolve_channel(channel_name, channel_id)
            if not epg_id:
                return None
            programs = list(self._schedules.get(epg_id, []))
        now = datetime.now(timezone.utc)
        for p in programs:
            if p.is_current(now):
                return p
        return None

    def get_next_program(self, channel_name: str = "",
                          channel_id: str = "") -> Optional[EPGProgram]:
        """Get the next upcoming program for a channel."""
        with self._lock:
            epg_id = self._resolve_channel(channel_name, channel_id)
            if not epg_id:
                return None
            programs = list(self._schedules.get(epg_id, []))
        now = datetime.now(timezone.utc)
        for p in programs:
            if p.is_upcoming(now):
                return p
        return None

    def get_schedule(self, channel_name: str = "", channel_id: str = "",
                      hours: int = 6) -> List[EPGProgram]:
        """Get program schedule for a channel within the next N hours."""
        with self._lock:
            epg_id = self._resolve_channel(channel_name, channel_id)
            if not epg_id:
                return []
            programs = list(self._schedules.get(epg_id, []))
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(hours=hours)
        return [p for p in programs if p.end > now and p.start < cutoff]

    def get_now_next(self, channel_name: str = "",
                      channel_id: str = "") -> Tuple[Optional[EPGProgram], Optional[EPGProgram]]:
        """Get current and next program as a tuple (atomic snapshot)."""
        with self._lock:
            epg_id = self._resolve_channel(channel_name, channel_id)
            if not epg_id:
                return (None, None)
            programs = list(self._schedules.get(epg_id, []))
        now = datetime.now(timezone.utc)
        current = None
        upcoming = None
        for p in programs:
            if current is None and p.is_current(now):
                current = p
            elif upcoming is None and p.is_upcoming(now):
                upcoming = p
            if current and upcoming:
                break
        return (current, upcoming)

    @property
    def channel_count(self) -> int:
        return len(self._channel_map)

    @property
    def is_loaded(self) -> bool:
        return self._initialized and bool(self._schedules)

    def get_epg_sources(self) -> List[str]:
        return list(self._epg_sources)

    def set_epg_sources(self, sources: List[str]) -> None:
        self._epg_sources = sources

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_channel(self, name: str, epg_id: str) -> Optional[str]:
        """Resolve a channel name or EPG ID to an EPG channel ID.

        Two-tier matching:
        1. Safe matches (exact, no-space normalization, HD/SD/4K suffix strip,
           country-suffix base): unambiguous — accepted directly.
        2. Aggressive matches (strip trailing ' news', ' tv', ' channel',
           ' live', ' stream'; trailing-word removal): only accepted when the
           stripped key maps to a unique EPG ID. If multiple EPG IDs share the
           same stripped form (e.g., "Discovery Channel" → "Discovery" collides
           with a different "Discovery" feed), we return None rather than guess.
        """
        if epg_id and epg_id in self._schedules:
            return epg_id

        if name:
            # Locale alias: e.g. "ערוץ 14" → "Channel 14" so existing fuzzy
            # logic can match against the English-name EPG index.
            aliased = _alias_channel(name)
            clean = aliased.lower().strip()
            # ── Tier 1: safe lookups ──
            # Direct match
            if clean in self._name_to_epg_id:
                return self._name_to_epg_id[clean]
            # Safe suffix strip (HD/SD/4K variants — no semantic collision risk)
            for suffix in (' hd', ' sd', ' fhd', ' uhd', ' 4k', ' (hd)', ' +1'):
                if clean.endswith(suffix):
                    stripped = clean[: -len(suffix)].strip()
                    if stripped in self._name_to_epg_id:
                        return self._name_to_epg_id[stripped]
            # No-space normalization (e.g., "kan 11" → "kan11")
            no_spaces = re.sub(r'\s+', '', clean)
            if no_spaces != clean and no_spaces in self._name_to_epg_id:
                return self._name_to_epg_id[no_spaces]

            # ── Tier 2: aggressive — only accept if uniquely identified ──
            def _unique_or_none(key: str) -> Optional[str]:
                candidates = self._aggressive_name_to_epg_ids.get(key)
                if candidates and len(candidates) == 1:
                    return next(iter(candidates))
                return None

            # Aggressive suffix strip
            for suffix in (' news', ' tv', ' channel', ' live', ' stream'):
                if clean.endswith(suffix):
                    stripped = clean[: -len(suffix)].strip()
                    hit = _unique_or_none(stripped)
                    if hit:
                        return hit
                    # Also try no-space variant of the stripped form
                    hit = _unique_or_none(re.sub(r'\s+', '', stripped))
                    if hit:
                        return hit
            # Trailing-word removal — only when unique
            words = clean.split()
            for i in range(len(words) - 1, 0, -1):
                partial = ' '.join(words[:i])
                hit = _unique_or_none(partial)
                if hit:
                    return hit
                hit = _unique_or_none(''.join(words[:i]))
                if hit:
                    return hit

        return None

    def _build_name_index(self) -> None:
        """Build lowercase name → EPG ID indices for fuzzy matching.

        Two indices:
        - ``_name_to_epg_id``: for safe (unambiguous) lookups.
        - ``_aggressive_name_to_epg_ids``: maps stripped key → set of EPG IDs.
          Used by tier-2 matching, which only accepts when the set is a singleton.
        """
        self._name_to_epg_id = {}
        self._aggressive_name_to_epg_ids: Dict[str, set] = {}

        def _add_aggressive(key: str, epg_id: str) -> None:
            if not key:
                return
            self._aggressive_name_to_epg_ids.setdefault(key, set()).add(epg_id)

        for epg_id, name in self._channel_map.items():
            clean_name = name.lower().strip()
            self._name_to_epg_id[clean_name] = epg_id
            # Country-suffix base (e.g., "BBC One" from "BBC One.uk")
            if '.' in epg_id:
                base = epg_id.rsplit('.', 1)[0]
                self._name_to_epg_id[base.lower()] = epg_id
            # No-space normalization
            normalized = re.sub(r'\s+', '', clean_name)
            if normalized != clean_name:
                self._name_to_epg_id[normalized] = epg_id
            # Index the EPG ID itself lowercased
            self._name_to_epg_id[epg_id.lower()] = epg_id

            # Aggressive index: also key by partials so unique-match lookups work
            _add_aggressive(clean_name, epg_id)
            _add_aggressive(normalized, epg_id)
            # Add each trailing-word partial as an aggressive candidate
            words = clean_name.split()
            for i in range(len(words) - 1, 0, -1):
                _add_aggressive(' '.join(words[:i]), epg_id)
                _add_aggressive(''.join(words[:i]), epg_id)

    async def _fetch_source(self, session: aiohttp.ClientSession,
                             url: str) -> Tuple[Dict[str, str], Dict[str, List[EPGProgram]]]:
        """Fetch and parse a single EPG source."""
        # Limits raised May 2026: modern community EPG feeds (Pluto/Samsung/Plex)
        # routinely ship 15-30 MB compressed and 80-200 MB decompressed. The old
        # 10/50 MB caps silently dropped every large source, leaving Docker
        # users with no program data at all.
        MAX_EPG_DOWNLOAD = 64 * 1024 * 1024     # 64 MB compressed
        MAX_EPG_DECOMPRESSED = 300 * 1024 * 1024  # 300 MB decompressed

        logger.info("Fetching EPG: %s", url)
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning("EPG fetch failed (HTTP %d): %s", response.status, url)
                    return {}, {}

                # IMPORTANT: stream-read in chunks until EOF rather than
                # ``response.content.read(N)``. The single-arg read can return
                # *fewer* than N bytes on chunked-transfer responses (it
                # returns whatever's in the buffer when the syscall returns),
                # leaving us with a truncated payload that gzip.decompress
                # then rejects with "Compressed file ended before end-of-
                # stream". Looping until EOF gives us the complete body.
                buf = bytearray()
                async for chunk in response.content.iter_chunked(256 * 1024):
                    buf.extend(chunk)
                    if len(buf) > MAX_EPG_DOWNLOAD:
                        logger.warning("EPG source too large (>%d MB): %s",
                                       MAX_EPG_DOWNLOAD // (1024 * 1024), url)
                        return {}, {}
                data = bytes(buf)
                content_length = response.headers.get("Content-Length")
                if content_length and content_length.isdigit():
                    expected = int(content_length)
                    if len(data) < expected:
                        logger.warning(
                            "EPG download truncated for %s: got %d / %d bytes",
                            url, len(data), expected,
                        )
                        return {}, {}
                logger.debug("EPG downloaded %d bytes from %s", len(data), url)

                # Detect gzip by magic bytes rather than trusting the URL or
                # Content-Encoding header — some sources serve raw XML at .gz
                # URLs after a CDN strips the gzip layer, and some servers
                # return gzipped data without setting Content-Encoding.
                is_gzipped = data[:2] == b"\x1f\x8b"
                if is_gzipped:
                    try:
                        data = gzip.decompress(data)
                        if len(data) > MAX_EPG_DECOMPRESSED:
                            logger.warning("EPG decompressed content too large (>%d MB): %s",
                                           MAX_EPG_DECOMPRESSED // (1024 * 1024), url)
                            return {}, {}
                    except Exception as exc:
                        logger.warning(
                            "EPG gzip decompression failed for %s (%d bytes): %s",
                            url, len(data), exc,
                        )
                        return {}, {}
                elif url.endswith(".gz"):
                    # URL claims gzip but bytes aren't gzipped — likely the CDN
                    # already decompressed for us. Treat as plain XML and let
                    # the parser decide if it's valid.
                    logger.debug("EPG source %s served decompressed content despite .gz URL", url)

                xml_content = data.decode('utf-8', errors='replace')
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as exc:
            # Some aiohttp exception subclasses have empty str(exc).
            # Always include the type name so logs are diagnosable.
            detail = str(exc) or repr(exc) or "<no detail>"
            logger.warning("EPG fetch error for %s: %s: %s",
                           url, type(exc).__name__, detail)
            return {}, {}
        except Exception as exc:
            # Catch-all: gzip/IncompleteReadError/etc. can sneak through.
            logger.warning("EPG unexpected error for %s: %s: %s",
                           url, type(exc).__name__, exc or repr(exc))
            return {}, {}

        try:
            channels, schedules = parse_xmltv(xml_content)
        except Exception as exc:
            logger.warning("EPG parse failed for %s: %s", url, exc)
            return {}, {}
        logger.info("EPG fetched %d channels / %d schedules from %s",
                    len(channels), len(schedules), url)
        return channels, schedules

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    def _cache_path(self) -> str:
        # Prefer DATA_DIR env var (Docker volume), fall back to BASE_DIR
        data_dir = os.environ.get("DATA_DIR", "")
        if data_dir:
            return os.path.join(data_dir, EPG_CACHE_FILE)
        try:
            import config
            return os.path.join(config.BASE_DIR, EPG_CACHE_FILE)
        except ImportError:
            return EPG_CACHE_FILE

    def _save_cache(self) -> None:
        """Save EPG data to disk cache."""
        cache = {
            'last_fetch': self._last_fetch,
            'channel_map': self._channel_map,
            'schedules': {
                ch_id: [p.to_dict() for p in programs]
                for ch_id, programs in self._schedules.items()
            },
        }
        path = self._cache_path()
        # Ensure directory exists
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False)
        logger.debug("EPG cache saved to %s", path)

    def _load_cache(self) -> None:
        """Load EPG data from disk cache."""
        path = self._cache_path()
        if not os.path.exists(path):
            return

        with open(path, 'r', encoding='utf-8') as f:
            cache = json.load(f)

        last_fetch = cache.get('last_fetch', 0)
        age_hours = (time.time() - last_fetch) / 3600
        if age_hours > EPG_CACHE_MAX_AGE_HOURS * 2:
            logger.info("EPG cache too old (%.1fh), will re-fetch", age_hours)
            return

        channel_map = cache.get('channel_map', {})
        # Don't trust an empty cache — a previous startup with no network would
        # have written one, and we'd then refuse to re-fetch for 12h. Treat as
        # cache-miss so initialize() will fetch fresh.
        if not channel_map:
            logger.info("EPG cache is empty, ignoring and will fetch fresh")
            try:
                os.remove(path)
            except OSError:
                pass
            return

        self._channel_map = channel_map
        self._schedules = {}
        for ch_id, programs in cache.get('schedules', {}).items():
            self._schedules[ch_id] = [
                EPGProgram.from_dict(p) for p in programs
            ]
        self._build_name_index()
        self._last_fetch = last_fetch
        self._initialized = True

        logger.info("EPG cache loaded: %d channels, %d programs (%.1fh old)",
                     len(self._channel_map),
                     sum(len(v) for v in self._schedules.values()),
                     age_hours)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
epg_service = EPGService()

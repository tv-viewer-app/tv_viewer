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

# Default EPG sources — community XMLTV mirrors
DEFAULT_EPG_SOURCES = [
    # epg.pw community XMLTV guides (country-based, updated daily)
    "https://epg.pw/xmltv/epg_IL.xml.gz",
    "https://epg.pw/xmltv/epg_US.xml.gz",
    "https://epg.pw/xmltv/epg_GB.xml.gz",
    "https://epg.pw/xmltv/epg_DE.xml.gz",
    "https://epg.pw/xmltv/epg_FR.xml.gz",
]

# Cache settings
EPG_CACHE_FILE = "epg_cache.json"
EPG_CACHE_MAX_AGE_HOURS = 6
EPG_FETCH_TIMEOUT = 30
EPG_MAX_PROGRAMS_PER_CHANNEL = 48  # ~24 hours of 30-min programs


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

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
        logger.warning("Failed to parse XMLTV: %s", e)
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
        self._channel_map: Dict[str, str] = {}          # epg_id → display_name
        self._schedules: Dict[str, List[EPGProgram]] = {}  # epg_id → [programs]
        self._name_to_epg_id: Dict[str, str] = {}       # lowercase name → epg_id
        self._initialized = False
        self._last_fetch: float = 0
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
        if sources:
            self._epg_sources = sources

        # Check if cache is fresh enough
        cache_age_hours = (time.time() - self._last_fetch) / 3600
        if self._initialized and cache_age_hours < EPG_CACHE_MAX_AGE_HOURS:
            logger.info("EPG cache still fresh (%.1fh old), skipping fetch", cache_age_hours)
            return

        if aiohttp is None:
            logger.warning("aiohttp not available — EPG disabled")
            return

        logger.info("Fetching EPG data from %d sources...", len(self._epg_sources))
        all_channels: Dict[str, str] = {}
        all_schedules: Dict[str, List[EPGProgram]] = {}

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=EPG_FETCH_TIMEOUT)
        ) as session:
            tasks = [self._fetch_source(session, url) for url in self._epg_sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.warning("EPG source failed: %s", result)
                continue
            channels, schedules = result
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
            self._channel_map = all_channels
            self._schedules = all_schedules
            self._build_name_index()
            self._initialized = True
            self._last_fetch = time.time()

        logger.info("EPG loaded: %d channels, %d programs",
                     len(all_channels),
                     sum(len(v) for v in all_schedules.values()))

        # Save to cache
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
        """Resolve a channel name or EPG ID to an EPG channel ID."""
        if epg_id and epg_id in self._schedules:
            return epg_id

        if name:
            clean = name.lower().strip()
            # Direct match
            if clean in self._name_to_epg_id:
                return self._name_to_epg_id[clean]
            # Fuzzy: try removing common suffixes
            for suffix in [' hd', ' sd', ' fhd', ' uhd', ' 4k', ' (hd)', ' +1']:
                stripped = clean.replace(suffix, '').strip()
                if stripped in self._name_to_epg_id:
                    return self._name_to_epg_id[stripped]

        return None

    def _build_name_index(self) -> None:
        """Build lowercase name → EPG ID index for fuzzy matching."""
        self._name_to_epg_id = {}
        for epg_id, name in self._channel_map.items():
            self._name_to_epg_id[name.lower().strip()] = epg_id
            # Also index without country suffix (e.g., "BBC One" from "BBC One.uk")
            if '.' in epg_id:
                base = epg_id.rsplit('.', 1)[0]
                self._name_to_epg_id[base.lower()] = epg_id

    async def _fetch_source(self, session: aiohttp.ClientSession,
                             url: str) -> Tuple[Dict[str, str], Dict[str, List[EPGProgram]]]:
        """Fetch and parse a single EPG source."""
        MAX_EPG_DOWNLOAD = 10 * 1024 * 1024    # 10 MB compressed
        MAX_EPG_DECOMPRESSED = 50 * 1024 * 1024  # 50 MB decompressed

        logger.debug("Fetching EPG: %s", url)
        async with session.get(url) as response:
            if response.status != 200:
                logger.warning("EPG fetch failed (%d): %s", response.status, url)
                return {}, {}

            data = await response.content.read(MAX_EPG_DOWNLOAD + 1)
            if len(data) > MAX_EPG_DOWNLOAD:
                logger.warning("EPG source too large (>10MB): %s", url)
                return {}, {}

            # Decompress if gzipped
            if url.endswith('.gz') or response.headers.get('Content-Encoding') == 'gzip':
                try:
                    data = gzip.decompress(data)
                    if len(data) > MAX_EPG_DECOMPRESSED:
                        logger.warning("EPG decompressed content too large (>50MB): %s", url)
                        return {}, {}
                except Exception:
                    pass  # might not actually be gzipped

            xml_content = data.decode('utf-8', errors='replace')

        return parse_xmltv(xml_content)

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    def _cache_path(self) -> str:
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

        self._channel_map = cache.get('channel_map', {})
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

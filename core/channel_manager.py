"""Channel manager for organizing and persisting channels.

This module provides centralized channel management with optimized memory usage
and thread-safe operations.

Architecture:
    ChannelManager serves as the single source of truth for channel data.
    It handles loading/saving, fetching, organizing, and validating channels.

Memory Optimization:
    - Uses __slots__ to reduce per-instance memory overhead (~40% savings)
    - Channels stored in single list; categories/countries share references
    - URL-to-index mapping enables O(1) channel lookups
    - In-place updates avoid creating channel copies

Thread Safety:
    - All public methods acquire _lock before modifying state
    - RLock allows reentrant/nested locking
    - StreamChecker runs in separate daemon thread
"""

import threading
import gc
import hashlib
from typing import List, Dict, Any, Optional, Callable, Set
from collections import defaultdict

from utils.helpers import load_json_file, save_json_file, categorize_channel, get_channel_country, get_minimum_age, detect_media_type
from utils.logger import get_logger, redact_url
from utils import supabase_channels
from .repository import RepositoryHandler
from .stream_checker import StreamChecker
import config
from datetime import datetime

# Module logger
logger = get_logger(__name__)


def import_time_str() -> str:
    """Get current timestamp as ISO format string."""
    return datetime.now().isoformat()


# ISO 3166-1 alpha-2 to country name mapping for normalizing tvg-country codes
_ISO_TO_COUNTRY = {
    'AF': 'Afghanistan', 'AL': 'Albania', 'DZ': 'Algeria', 'AR': 'Argentina',
    'AM': 'Armenia', 'AU': 'Australia', 'AT': 'Austria', 'AZ': 'Azerbaijan',
    'BH': 'Bahrain', 'BD': 'Bangladesh', 'BY': 'Belarus', 'BE': 'Belgium',
    'BO': 'Bolivia', 'BA': 'Bosnia', 'BR': 'Brazil', 'BG': 'Bulgaria',
    'CA': 'Canada', 'CL': 'Chile', 'CN': 'China', 'CO': 'Colombia',
    'CR': 'Costa Rica', 'HR': 'Croatia', 'CU': 'Cuba', 'CY': 'Cyprus',
    'CZ': 'Czech Republic', 'DK': 'Denmark', 'DO': 'Dominican Republic',
    'EC': 'Ecuador', 'EG': 'Egypt', 'SV': 'El Salvador', 'EE': 'Estonia',
    'ET': 'Ethiopia', 'FI': 'Finland', 'FR': 'France', 'GE': 'Georgia',
    'DE': 'Germany', 'GH': 'Ghana', 'GR': 'Greece', 'GT': 'Guatemala',
    'HN': 'Honduras', 'HK': 'Hong Kong', 'HU': 'Hungary', 'IS': 'Iceland',
    'IN': 'India', 'ID': 'Indonesia', 'IR': 'Iran', 'IQ': 'Iraq',
    'IE': 'Ireland', 'IL': 'Israel', 'IT': 'Italy', 'JM': 'Jamaica',
    'JP': 'Japan', 'JO': 'Jordan', 'KZ': 'Kazakhstan', 'KE': 'Kenya',
    'KW': 'Kuwait', 'LV': 'Latvia', 'LB': 'Lebanon', 'LY': 'Libya',
    'LT': 'Lithuania', 'LU': 'Luxembourg', 'MY': 'Malaysia', 'MX': 'Mexico',
    'MA': 'Morocco', 'MM': 'Myanmar', 'NP': 'Nepal', 'NL': 'Netherlands',
    'NZ': 'New Zealand', 'NG': 'Nigeria', 'NO': 'Norway', 'OM': 'Oman',
    'PK': 'Pakistan', 'PA': 'Panama', 'PY': 'Paraguay', 'PE': 'Peru',
    'PH': 'Philippines', 'PL': 'Poland', 'PT': 'Portugal', 'QA': 'Qatar',
    'RO': 'Romania', 'RU': 'Russia', 'SA': 'Saudi Arabia', 'RS': 'Serbia',
    'SG': 'Singapore', 'SK': 'Slovakia', 'SI': 'Slovenia', 'ZA': 'South Africa',
    'KR': 'South Korea', 'ES': 'Spain', 'LK': 'Sri Lanka', 'SD': 'Sudan',
    'SE': 'Sweden', 'CH': 'Switzerland', 'SY': 'Syria', 'TW': 'Taiwan',
    'TH': 'Thailand', 'TN': 'Tunisia', 'TR': 'Turkey', 'UA': 'Ukraine',
    'AE': 'UAE', 'GB': 'UK', 'US': 'US', 'UY': 'Uruguay',
    'UZ': 'Uzbekistan', 'VE': 'Venezuela', 'VN': 'Vietnam', 'YE': 'Yemen',
}


def _normalize_country(country_str: str) -> str:
    """Normalize a country string — convert ISO codes to full names."""
    if not country_str:
        return 'Unknown'
    country_str = country_str.strip()
    # If it looks like a 2-letter ISO code, convert it
    if len(country_str) == 2 and country_str.isalpha():
        return _ISO_TO_COUNTRY.get(country_str.upper(), country_str)
    # Handle semicolon-separated country lists (iptv-org format) — take first
    if ';' in country_str:
        first = country_str.split(';')[0].strip()
        if len(first) == 2 and first.isalpha():
            return _ISO_TO_COUNTRY.get(first.upper(), first)
        return first
    return country_str


def _migrate_channel_urls(channel: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate a channel dict to ensure it has both 'url' and 'urls' keys.
    
    v2.1.0: Ensures backward compatibility during the transition to multi-URL
    support. After migration, the channel will have:
      - 'urls': List[str] — all alternate stream URLs
      - 'url': str — the primary URL (urls[working_url_index])
      - 'working_url_index': int — index of the currently active URL
    
    This is safe to call multiple times (idempotent).
    """
    # Already migrated — has a valid urls list
    if 'urls' in channel and isinstance(channel['urls'], list) and channel['urls']:
        # Ensure 'url' stays in sync as primary URL shortcut
        try:
            idx = int(channel.get('working_url_index', 0))
        except (TypeError, ValueError):
            idx = 0
        urls = channel['urls']
        idx = max(0, min(idx, len(urls) - 1))
        channel['working_url_index'] = idx
        channel['url'] = urls[idx]
        return channel
    
    # Legacy format — single 'url' string
    single_url = channel.get('url', '')
    channel['urls'] = [single_url] if single_url else ['']
    channel['working_url_index'] = 0
    # 'url' key already exists (or is set now)
    channel['url'] = channel['urls'][0]
    return channel


def get_channel_url(channel: Dict[str, Any]) -> str:
    """Get the currently active URL for a channel.
    
    v2.1.0: Supports both legacy single-url and new multi-url formats.
    Returns the URL at working_url_index, falling back gracefully.
    """
    urls = channel.get('urls', [channel.get('url', '')])
    if not urls:
        return channel.get('url', '')
    try:
        idx = int(channel.get('working_url_index', 0))
    except (TypeError, ValueError):
        idx = 0
    idx = max(0, min(idx, len(urls) - 1))
    return urls[idx]


import re

# Quality/variant suffixes to strip when consolidating channel names
_QUALITY_SUFFIX = re.compile(
    r'\b(alt\s*\d*|backup|mirror|'
    r'\d{3,4}[pi]|'           # 720p, 1080i, etc
    r'HD|FHD|UHD|4K|SD|'      # Quality labels
    r'h\.?26[45]|hevc|avc|'   # Codecs
    r'mpeg\d?|mp3|aac\+?|flac|mono|stereo|'  # Audio codecs
    r'multi\s*[-_]?\s*audio|'
    r'subtitl\w*|dubbed|subs?|cc|closed\s*cap\w*|'  # Subtitle/dub variants
    r'low|high|med|'
    r'stream\s*\d+|'
    r'v\d+|'                  # v1, v2
    r'option\s*\d+|'
    r'feed\s*\d+|'
    r'\d+k)\s*$',             # Bitrate: 128k, 320k
    re.IGNORECASE
)

# Trailing parenthesized/bracketed annotations to strip
_PAREN_SUFFIX = re.compile(r'\s*[\(\[][^\)\]]*[\)\]]\s*$')

# Pattern to match non-Latin script blocks (Hebrew, Arabic, CJK) separated by dash
_SCRIPT_SEPARATOR = re.compile(
    r'[\u0590-\u05FF\u0600-\u06FF\uFB1D-\uFDFF\uFE70-\uFEFF]+'  # non-Latin block
)
_DASH_SPLIT = re.compile(r'\s+[-–—]\s+')  # " - ", " – ", " — "

# Common country name prefixes that appear as "Country: Channel Name" in M3U sources
_COUNTRY_PREFIXES = {
    'israel', 'usa', 'uk', 'france', 'germany', 'spain', 'italy',
    'brazil', 'india', 'china', 'japan', 'korea', 'russia', 'turkey',
    'mexico', 'canada', 'australia', 'netherlands', 'portugal', 'greece',
    'poland', 'romania', 'hungary', 'chile', 'argentina', 'colombia',
}

# Explicit alias groups: channels that should merge into one multi-URL entry.
# Key = canonical name (lowercase), values = alternative names (lowercase).
# Must match Flutter's _channelAliases in m3u_service.dart.
_CHANNEL_ALIASES: Dict[str, List[str]] = {
    # ── Israeli TV channels ──
    'kan 11': ['kan 11 news', 'kan 11 subtitled', 'kan 11 4k', 'כאן 11',
               'kan 11 israel', 'israel kan 11', 'ערוץ 11', 'כאן'],
    'kan kids': ['kan kids / kan educational', 'kan kids / educational',
                 'kan educational', 'kan edu', 'כאן חינוכית'],
    'kan bet': ['kan reshet bet', 'kan bet / reshet bet',
                'kan israel reshet bet', 'רשת ב', 'reshet bet'],
    'kan moreshet': ['kan israel reshet moreshet 92.5 fm',
                     'kan israel moreshet'],
    'kan gimel': ['כאן גימל', 'kan gimel כאן גימל'],
    'kan tarbut': ['כאן תרבות'],
    'reshet 13': ['reshet 13 alt', 'reshet 13 subtitled',
                  'רשת 13', 'ערוץ 13'],
    'keshet 12': ['super channel 12', 'channel 12', 'קשת 12', 'ערוץ 12'],
    'channel 14': ['now 14', 'ערוץ 14', 'עכשיו 14'],
    'knesset channel': ['ערוץ הכנסת', 'כנסת', 'knesset'],
    'makan 33': ['מכאן', 'makan'],
    'sport 5': ['ספורט 5', 'sport5'],
    'walla': ['וואלה', 'walla tv'],
    'ynet': ['ynet live', 'ynet tv'],
    'hop channel': ['הופ', 'hop!', 'hop! channel'],
    'music 24': ['מיוזיק 24'],
    # ── Israeli radio ──
    'galgalatz': ['גלגלצ', 'גלצ', 'galatz', 'glglz', 'galgalatz 91.8 fm'],
    'eco99fm': ['אקו eco 99fm', '99fm eco', 'eco 99fm'],
    'radio 103fm': ['103fm'],
    'radios 100fm': ['radius 100fm', 'radios 100fm רדיוס'],
    'gali israel': ['גלי ישראל', '94fm רדיו גלי ישראל'],
    'kol israel': ['קול ישראל'],
}

# Build reverse lookup: alias → canonical name
_ALIAS_LOOKUP: Dict[str, str] = {}
for _canonical, _aliases in _CHANNEL_ALIASES.items():
    _ALIAS_LOOKUP[_canonical] = _canonical
    for _alias in _aliases:
        _ALIAS_LOOKUP[_alias] = _canonical


def _normalize_channel_name(name: str) -> str:
    """Strip quality/variant suffixes to get a canonical channel name for grouping.
    
    Multi-pass: strips trailing [...], (...), then known variant words,
    repeating until stable. This handles names like 'CNN (576p) [Not 24/7]'.
    """
    if not name:
        return ''
    normalized = name.strip()
    for _ in range(4):  # max 4 passes to converge
        prev = normalized
        # Strip trailing [...] (schedule/geo notes)
        normalized = _PAREN_SUFFIX.sub('', normalized).strip()
        # Strip trailing known variant words (alt, 720p, HD, subtitled, etc.)
        normalized = _QUALITY_SUFFIX.sub('', normalized).strip()
        # Remove trailing separators
        normalized = normalized.rstrip(' -–—|/')
        if normalized == prev:
            break
    return normalized if normalized else name


def _normalize_name_for_grouping(name: str, country: str) -> str:
    """Advanced normalization for consolidation grouping.
    
    Extends _normalize_channel_name with country-aware rules:
    - Strips non-Latin script portions separated by dash (Hebrew/Arabic aliases)
    - Strips the country name from the channel name when redundant
    - Handles embedded country: "Kan Israel Tarbut" → "Kan Tarbut" (when country=Israel)
    """
    # Step 1: basic quality/variant normalization
    base = _normalize_channel_name(name)
    if not base:
        return ''
    
    # Step 1b: strip common country-code prefixes like "IL: Kan 11" or "US: CNN"
    prefix_match = re.match(r'^([A-Z]{2,3}):\s+(.+)$', base)
    if prefix_match:
        base = prefix_match.group(2).strip()
    # Also strip full country name prefixes like "Israel: Kan 11"
    prefix_match2 = re.match(r'^([A-Za-z]+):\s+(.+)$', base)
    if prefix_match2:
        prefix_word = prefix_match2.group(1).lower()
        if country and prefix_word == country.lower():
            base = prefix_match2.group(2).strip()
        elif prefix_word in _COUNTRY_PREFIXES:
            base = prefix_match2.group(2).strip()
    
    # Step 2: if name has " - " separator, check for non-Latin/Latin halves
    parts = _DASH_SPLIT.split(base)
    if len(parts) >= 2:
        # Keep the part that has the most Latin characters
        latin_parts = []
        for p in parts:
            stripped = p.strip()
            if not stripped:
                continue
            latin_chars = sum(1 for c in stripped if c.isascii() and c.isalpha())
            total_alpha = sum(1 for c in stripped if c.isalpha())
            if total_alpha > 0 and latin_chars / total_alpha > 0.5:
                latin_parts.append(stripped)
        if latin_parts:
            base = latin_parts[0]  # take first Latin-dominant part
    
    # Step 3: strip trailing country name when it matches the channel's country
    if country and country.lower() not in ('unknown', ''):
        country_lower = country.lower()
        base_lower = base.lower()
        # Trailing country: "KAN 11 Israel" → "KAN 11"
        if base_lower.endswith(' ' + country_lower):
            base = base[:-(len(country) + 1)].strip()
        # Embedded country: "Kan Israel Tarbut" → "Kan Tarbut"
        # Only strip if country is in the middle (not first/last word)
        else:
            words = base.split()
            if len(words) >= 3:
                words_lower = [w.lower() for w in words]
                # Check for country name in middle positions (not first or last)
                for i in range(1, len(words) - 1):
                    if words_lower[i] == country_lower:
                        words.pop(i)
                        base = ' '.join(words)
                        break
    
    # Step 4: re-run quality stripping in case country removal exposed suffixes
    base = _normalize_channel_name(base)
    
    # Step 5: check alias mapping for explicit merge groups
    key = base.strip().lower()
    if key in _ALIAS_LOOKUP:
        return _ALIAS_LOOKUP[key]
    
    return base.strip() if base.strip() else _normalize_channel_name(name)


def consolidate_channels(channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge channels with the same base name into single multi-URL entries.
    
    Channels like "Reshet 13 720p", "Reshet 13 alt", "Reshet 13 (רשת 13)"
    are merged into one entry with all their URLs in the 'urls' list.
    
    URL ordering: working URLs first (sorted by response_time_ms),
    then unchecked, then known-failed. The preferred/last-working URL
    is preserved via working_url_index.
    
    Returns a new list; does not modify the originals.
    """
    from collections import OrderedDict
    
    groups: OrderedDict[str, Dict[str, Any]] = OrderedDict()
    # Track per-URL health metadata for priority ordering
    url_health: Dict[str, Dict[str, Any]] = {}
    
    for ch in channels:
        name = ch.get('name', '')
        # Normalize country (fixes None crash + ISO/full-name mismatch)
        country = _normalize_country(ch.get('country') or '')
        # Country-aware name normalization for grouping
        base_name = _normalize_name_for_grouping(name, country)
        # Group key: case-insensitive base name + normalized country
        group_key = f"{base_name.lower()}|{country.lower()}"
        
        # Cross-country merge: merge "Unknown" country with same-named known country
        if group_key not in groups:
            name_lower = base_name.lower()
            if country.lower() == 'unknown':
                # Unknown country -> find existing group with same name + any country
                for existing_key in groups:
                    if existing_key.startswith(name_lower + '|'):
                        group_key = existing_key
                        break
            else:
                # Known country -> absorb existing "unknown" country group
                unknown_key = f"{name_lower}|unknown"
                if unknown_key in groups:
                    # Move unknown group to known-country key
                    groups[group_key] = groups.pop(unknown_key)
                    groups[group_key]['country'] = country
        
        url = ch.get('url', '')
        if not url:
            continue
        
        # Record health info for each URL
        ch_urls = ch.get('urls', [url])
        for u in ch_urls:
            if u and u not in url_health:
                url_health[u] = {
                    'is_working': ch.get('is_working'),
                    'response_time_ms': ch.get('response_time_ms', 9999),
                    'last_checked': ch.get('last_checked', ''),
                }
        
        if group_key not in groups:
            merged = dict(ch)
            merged['name'] = base_name if base_name else name
            urls = list(ch_urls)
            seen = set()
            unique_urls = []
            for u in urls:
                if u and u not in seen:
                    seen.add(u)
                    unique_urls.append(u)
            merged['urls'] = unique_urls
            merged['url'] = unique_urls[0] if unique_urls else ''
            merged['working_url_index'] = ch.get('working_url_index', 0)
            groups[group_key] = merged
        else:
            existing = groups[group_key]
            existing_urls = existing.get('urls', [])
            seen = set(existing_urls)
            
            new_urls = ch.get('urls', [url])
            for u in new_urls:
                if u and u not in seen:
                    seen.add(u)
                    existing_urls.append(u)
            existing['urls'] = existing_urls
            
            # Prefer working status
            if ch.get('is_working') and not existing.get('is_working'):
                existing['is_working'] = True
            
            # Prefer scanned status over pending
            if ch.get('scan_status') == 'scanned' and existing.get('scan_status') != 'scanned':
                existing['scan_status'] = 'scanned'
                if ch.get('last_scanned'):
                    existing['last_scanned'] = ch['last_scanned']
            
            # Fill in missing metadata
            if not existing.get('logo') and ch.get('logo'):
                existing['logo'] = ch['logo']
            if existing.get('category', 'Other') == 'Other' and ch.get('category', 'Other') != 'Other':
                existing['category'] = ch['category']
    
    # Second pass: sort URLs by health (working first, then by response time)
    for merged in groups.values():
        urls = merged.get('urls', [])
        if len(urls) <= 1:
            continue
        
        def _url_sort_key(u):
            h = url_health.get(u, {})
            working = h.get('is_working')
            rt = h.get('response_time_ms', 9999)
            # Sort order: working (0) > unchecked (1) > failed (2), then by response time
            if working is True:
                return (0, rt)
            elif working is None:
                return (1, rt)
            else:
                return (2, rt)
        
        # Preserve the current preferred URL before sorting
        preferred_url = ''
        widx = merged.get('working_url_index', 0)
        if 0 <= widx < len(urls):
            preferred_url = urls[widx]
        
        urls.sort(key=_url_sort_key)
        merged['urls'] = urls
        merged['url'] = urls[0]
        
        # Restore working_url_index to point to the preferred URL
        if preferred_url and preferred_url in urls:
            merged['working_url_index'] = urls.index(preferred_url)
        else:
            merged['working_url_index'] = 0
    
    result = list(groups.values())
    removed = len(channels) - len(result)
    if removed > 0:
        logger.info(f"Channel consolidation: {len(channels)} → {len(result)} ({removed} merged)")
    return result


class ChannelManager:
    """Manages channel discovery, validation, and persistence.
    
    Central coordinator for all channel-related operations with thread-safe
    access and optimized memory usage.
    
    Attributes:
        channels: Master list of all channel dictionaries
        categories: Dict mapping category -> channel list (shared references)
        countries: Dict mapping country -> channel list (shared references)
        group_by: Current grouping mode ('category' or 'country')
        media_type_filter: Current filter ('All', 'TV', or 'Radio')
    """
    
    # __slots__ reduces memory by preventing __dict__ creation
    __slots__ = ('channels', 'categories', 'countries', 'repository_handler', 
                 'stream_checker', '_lock', 'group_by', 'media_type_filter', '_url_to_index',
                 '_on_channels_loaded', '_on_channel_validated', 
                 '_on_validation_complete', '_on_fetch_progress', '_non_working_urls',
                 '_health_cache', '_shutting_down')
    
    def __init__(self):
        """Initialize ChannelManager with empty state."""
        self.channels: List[Dict[str, Any]] = []
        self.categories: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.countries: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.repository_handler = RepositoryHandler()
        self.stream_checker = StreamChecker()
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self.group_by = 'category'
        self.media_type_filter = 'All'
        self._url_to_index: Dict[str, int] = {}  # O(1) URL lookups
        self._non_working_urls: Set[str] = set()  # URLs known to be non-working
        self._health_cache: Dict = {}  # SharedDb health cache from last fetch
        self._shutting_down = False  # Shutdown flag to prevent races (Bug #76)
        
        # Callbacks for UI updates
        self._on_channels_loaded: Optional[Callable[[int], None]] = None
        self._on_channel_validated: Optional[Callable[[Dict[str, Any], int, int], None]] = None
        self._on_validation_complete: Optional[Callable[[], None]] = None
        self._on_fetch_progress: Optional[Callable[[int, int], None]] = None
    
    # Properties for callbacks to maintain compatibility
    @property
    def on_channels_loaded(self):
        return self._on_channels_loaded
    
    @on_channels_loaded.setter
    def on_channels_loaded(self, value):
        self._on_channels_loaded = value
    
    @property
    def on_channel_validated(self):
        return self._on_channel_validated
    
    @on_channel_validated.setter
    def on_channel_validated(self, value):
        self._on_channel_validated = value
    
    @property
    def on_validation_complete(self):
        return self._on_validation_complete
    
    @on_validation_complete.setter
    def on_validation_complete(self, value):
        self._on_validation_complete = value
    
    @property
    def on_fetch_progress(self):
        return self._on_fetch_progress
    
    @on_fetch_progress.setter
    def on_fetch_progress(self, value):
        self._on_fetch_progress = value
    
    def load_cached_channels(self) -> bool:
        """
        Load channels from the cache file.
        
        Returns:
            True if channels were loaded successfully
        """
        try:
            data = load_json_file(config.CHANNELS_FILE)
        except Exception as e:
            logger.error(f"Failed to read channels cache: {e}")
            data = None
        
        if data and 'channels' in data:
            try:
                with self._lock:
                    # Deduplicate by URL (Issue #29)
                    seen_urls = set()
                    unique_channels = []
                    for ch in data['channels']:
                        url = ch.get('url', '')
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            unique_channels.append(ch)
                        elif not url:
                            unique_channels.append(ch)
                    
                    deduped = len(data['channels']) - len(unique_channels)
                    if deduped > 0:
                        logger.info(f"Removed {deduped} duplicate channels from cache")
                    
                    self.channels = unique_channels
                    # Migrate channels to multi-URL format (v2.1.0)
                    for ch in self.channels:
                        _migrate_channel_urls(ch)
                    # Ensure all channels have scan_status field
                    for ch in self.channels:
                        if 'scan_status' not in ch:
                            ch['scan_status'] = 'pending' if ch.get('is_working') is None else 'scanned'
                    self._organize_channels()
                logger.debug(f"Loaded {len(self.channels)} channels from cache")
                return True
            except Exception as e:
                logger.error(f"Corrupted channels cache, resetting: {e}")
                # Backup corrupt file for debugging
                try:
                    import shutil
                    backup_path = config.CHANNELS_FILE + '.corrupt'
                    shutil.copy2(config.CHANNELS_FILE, backup_path)
                    logger.info(f"Corrupt channels file backed up to {backup_path}")
                except Exception:
                    pass
                with self._lock:
                    self.channels = []
                    self._organize_channels()
                return False
        return False
    
    def save_channels(self) -> bool:
        """
        Save current channels to the cache file.
        
        Bug #68: The lock is held while we build a snapshot so background scan
        mutations cannot race with serialization.  We serialize outside the
        lock to avoid holding it during disk I/O.
        
        Returns:
            True if saved successfully
        """
        import copy
        with self._lock:
            # Ensure all channels are migrated to multi-URL format before saving (v2.1.0)
            for ch in self.channels:
                _migrate_channel_urls(ch)
            # Deep-copy channel data under lock so save_json_file works on a
            # consistent snapshot without holding the lock during I/O.
            data = {
                'channels': copy.deepcopy(self.channels),
                'version': config.APP_VERSION,
                'last_updated': import_time_str()
            }
        return save_json_file(config.CHANNELS_FILE, data)
    
    def get_channels_to_scan(self) -> List[Dict[str, Any]]:
        """
        Get channels that need scanning (pending or need revalidation).
        Prioritizes unscanned channels, then rescans working channels.
        Skips channels scanned within SCAN_SKIP_MINUTES.
        Note: Caller should NOT hold self._lock when calling this method.
        """
        with self._lock:
            return self._get_channels_to_scan_internal()
    
    def _get_channels_to_scan_internal(self) -> List[Dict[str, Any]]:
        """
        Internal version that assumes lock is already held.
        Skips channels scanned within SCAN_SKIP_MINUTES.
        If non-working URLs were provided from shared scan, only scan those first.
        """
        from datetime import datetime, timedelta
        skip_threshold = datetime.now() - timedelta(minutes=config.SCAN_SKIP_MINUTES)
        
        def needs_rescan(ch: Dict[str, Any]) -> bool:
            """Check if channel needs rescanning based on last_scanned time."""
            last_scanned = ch.get('last_scanned')
            if not last_scanned:
                return True
            try:
                scan_time = datetime.fromisoformat(last_scanned)
                return scan_time < skip_threshold
            except (ValueError, TypeError):
                return True
        
        # If we have shared non-working URLs, prioritize rescanning those
        if self._non_working_urls:
            # First scan channels known to be non-working
            known_failed = [ch for ch in self.channels 
                          if ch.get('url') in self._non_working_urls]
            # Clear after use - only use for initial scan
            self._non_working_urls.clear()
            if known_failed:
                return known_failed
        
        # First, get channels never scanned
        pending = [ch for ch in self.channels if ch.get('scan_status') == 'pending']
        
        # Then, get working channels for revalidation (only if not recently scanned)
        working = [ch for ch in self.channels 
                  if ch.get('is_working') == True and ch.get('scan_status') == 'scanned'
                  and needs_rescan(ch)]
        
        # Failed channels last (lower priority, only if not recently scanned)
        failed = [ch for ch in self.channels 
                 if ch.get('is_working') == False and ch.get('scan_status') == 'scanned'
                 and needs_rescan(ch)]
        
        return pending + working + failed
    
    def set_non_working_urls(self, urls: Set[str]):
        """Set URLs known to be non-working from shared scan results."""
        with self._lock:
            # Bug #104: Copy the set instead of aliasing caller-owned data
            self._non_working_urls = set(urls)
    
    # Pre-compiled adult content keywords set for O(1) lookup
    _ADULT_KEYWORDS: Set[str] = frozenset({
        'adult', 'xxx', '18+', 'erotic', 'playboy', 'penthouse', 'hustler',
        'vivid', 'spice', 'redlight', 'private tv', 'sexe', 'porn', 'brazzers',
        'naughty', 'pleasure', 'xtreme', 'x-rated', 'xrated', 'mature',
    })
    
    def _is_adult_channel(self, channel: Dict[str, Any]) -> bool:
        """Check if a channel is adult content that should be filtered out.
        
        Uses pre-compiled keyword set for O(1) lookup per keyword.
        """
        name = (channel.get('name') or '').lower()
        category = (channel.get('category') or '').lower()
        url = (channel.get('url') or '').lower()
        
        combined = f"{name} {category} {url}"
        # Early exit on first match
        return any(kw in combined for kw in self._ADULT_KEYWORDS)
    
    def _organize_by_category(self):
        """Organize channels into category buckets."""
        self.categories.clear()
        for channel in self.channels:
            category = categorize_channel(channel)
            channel['category'] = category
            self.categories[category].append(channel)
    
    def _organize_by_country(self):
        """Organize channels into country buckets."""
        self.countries.clear()
        for channel in self.channels:
            country = get_channel_country(channel)
            channel['country'] = country
            channel['country_group'] = country
            self.countries[country].append(channel)
    
    def _organize_channels(self):
        """Organize channels by both category and country, and add age ratings and media type."""
        self.categories.clear()
        self.countries.clear()
        self._url_to_index.clear()
        
        # Filter out adult channels first
        self.channels = [ch for ch in self.channels if not self._is_adult_channel(ch)]
        
        # Consolidate channels with similar names into multi-URL entries
        self.channels = consolidate_channels(self.channels)
        
        total = len(self.channels)
        
        # Pre-allocate category/country dicts to avoid resizing
        categories = self.categories
        countries = self.countries
        url_index = self._url_to_index
        
        for idx, channel in enumerate(self.channels):
            if idx % 5000 == 0 and idx > 0:
                logger.debug(f"Organizing channels: {idx}/{total}...")
            
            # Migrate to multi-URL format if needed (v2.1.0)
            _migrate_channel_urls(channel)
            
            # Build URL index for fast lookups
            url = channel.get('url')
            if url:
                url_index[url] = idx
            
            # Always recalculate category to ensure consistency
            channel['category'] = categorize_channel(channel)
            category = channel['category']
            categories[category].append(channel)
            
            # Add country — always run intelligent lookup first, then fall back
            # to M3U tvg-country. This prevents country-specific M3U files
            # (e.g. countries/il.m3u) from mis-assigning all channels to one country.
            inferred_country = get_channel_country(
                {**channel, 'country': None}  # Force re-detection by name/URL
            )
            if inferred_country and inferred_country != 'Unknown':
                country = inferred_country
            else:
                # Fall back to existing tvg-country from M3U metadata, but only
                # trust full country names — NOT 2-letter ISO codes, which
                # come from country-specific M3U files and indicate broadcast
                # availability, not channel origin.
                existing_country = (channel.get('country') or '').strip()
                if existing_country and existing_country != 'Unknown' and len(existing_country) > 2:
                    country = existing_country
                elif existing_country and len(existing_country) == 2:
                    # 2-letter ISO code from M3U — don't trust, mark Unknown
                    country = 'Unknown'
                else:
                    country = 'Unknown'
            channel['country'] = country
            channel['country_group'] = country
            countries[country].append(channel)
            
            # Add minimum age (only if not set)
            if 'min_age' not in channel:
                channel['min_age'] = get_minimum_age(channel)
            
            # Add media type (only if not set)
            if 'media_type' not in channel:
                channel['media_type'] = detect_media_type(channel)
        
        if total > 0:
            logger.debug(f"Organizing channels: {total}/{total} done.")
    
    def _process_queued_updates(self):
        """Process all queued channel updates in a thread-safe manner."""
        if not hasattr(self.stream_checker, '_update_queue'):
            return
        
        updates = self.stream_checker._update_queue.get_all_updates()
        if not updates:
            return
        
        with self._lock:
            for channel in updates:
                url = channel.get('url')
                if not url:
                    continue
                
                # Use URL index for O(1) lookup
                idx = self._url_to_index.get(url)
                if idx is not None and idx < len(self.channels):
                    ch = self.channels[idx]
                    is_working = channel.get('is_working', False)
                    
                    # Track consecutive failures for auto-hide
                    if is_working:
                        ch['consecutive_failures'] = 0
                    else:
                        ch['consecutive_failures'] = ch.get('consecutive_failures', 0) + 1
                    
                    # Flag slow channels (response > 3s)
                    resp_ms = channel.get('response_time_ms')
                    if resp_ms is not None:
                        ch['response_time_ms'] = resp_ms
                        ch['is_slow'] = resp_ms > 3000
                    
                    # Auto-hide after 3 consecutive scan failures
                    if ch.get('consecutive_failures', 0) >= 3:
                        ch['auto_hidden'] = True
                    elif is_working:
                        ch['auto_hidden'] = False
                    
                    # Update in place - the same object is in categories/countries dicts
                    ch['is_working'] = is_working
                    ch['scan_status'] = 'scanned'
                    ch['last_scanned'] = channel.get('last_scanned')
    
    def get_categories(self) -> List[str]:
        """Get list of all categories with channels (only actual content categories)."""
        from config import DEFAULT_CATEGORIES
        # Only return groups that are actual categories (not countries)
        valid_categories = set(DEFAULT_CATEGORIES)
        return sorted([cat for cat in self.categories.keys() if cat in valid_categories])
    
    def get_countries(self) -> List[str]:
        """Get list of all countries with channels."""
        # Return all countries that have channels (skip empty ones and None keys)
        return sorted([ctry for ctry in self.countries.keys() if ctry and self.countries[ctry]])
    
    def get_groups(self) -> List[str]:
        """Get list of groups based on current grouping mode, filtered by media type."""
        if self.group_by == 'country':
            groups_dict = self.countries
        else:
            groups_dict = self.categories
        
        # Filter groups to only include those with channels matching media type
        if self.media_type_filter == 'All':
            return sorted([g for g in groups_dict.keys() if g and groups_dict[g]])
        
        filtered_groups = []
        for group, channels in groups_dict.items():
            if group and any(ch.get('media_type', 'TV') == self.media_type_filter for ch in channels):
                filtered_groups.append(group)
        return sorted(filtered_groups)
    
    def _filter_by_media_type(self, channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter channels by current media type filter and exclude auto-hidden."""
        result = [ch for ch in channels if not ch.get('auto_hidden', False)]
        if self.media_type_filter == 'All':
            return result
        return [ch for ch in result if ch.get('media_type', 'TV') == self.media_type_filter]
    
    def get_all_channels(self) -> List[Dict[str, Any]]:
        """Get all channels regardless of category/country, filtered by media type."""
        with self._lock:
            return self._filter_by_media_type(self.channels)
    
    def get_channels_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all channels in a specific category, filtered by media type."""
        return self._filter_by_media_type(self.categories.get(category, []))
    
    def get_channels_by_country(self, country: str) -> List[Dict[str, Any]]:
        """Get all channels in a specific country, filtered by media type."""
        return self._filter_by_media_type(self.countries.get(country, []))
    
    def get_channels_by_group(self, group: str) -> List[Dict[str, Any]]:
        """Get channels by current grouping mode, filtered by media type."""
        if self.group_by == 'country':
            return self.get_channels_by_country(group)
        return self.get_channels_by_category(group)
    
    def get_working_channels(self) -> List[Dict[str, Any]]:
        """Get only channels that have been validated as working, filtered by media type."""
        with self._lock:
            channels = [ch for ch in self.channels if ch.get('is_working', False)]
            return self._filter_by_media_type(channels)
    
    def get_working_channels_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get working channels in a specific category, filtered by media type."""
        channels = [
            ch for ch in self.categories.get(category, [])
            if ch.get('is_working', False)
        ]
        return self._filter_by_media_type(channels)
    
    def get_working_channels_by_country(self, country: str) -> List[Dict[str, Any]]:
        """Get working channels in a specific country, filtered by media type."""
        channels = [
            ch for ch in self.countries.get(country, [])
            if ch.get('is_working', False)
        ]
        return self._filter_by_media_type(channels)
    
    def get_working_channels_by_group(self, group: str) -> List[Dict[str, Any]]:
        """Get working channels by current grouping mode."""
        if self.group_by == 'country':
            return self.get_working_channels_by_country(group)
        return self.get_working_channels_by_category(group)
    
    def set_group_by(self, mode: str):
        """Set the grouping mode ('category' or 'country')."""
        if mode in ('category', 'country'):
            self.group_by = mode
    
    def set_media_type(self, media_type: str):
        """Set the media type filter ('All', 'TV', or 'Radio')."""
        if media_type in ('All', 'TV', 'Radio'):
            self.media_type_filter = media_type
    
    async def _fetch_and_update(self):
        """Fetch channels: Supabase first, then M3U repos, contribute back new ones."""
        logger.debug("_fetch_and_update starting...")
        
        def progress(current, total):
            if self.on_fetch_progress:
                self.on_fetch_progress(current, total)
        
        supabase_chs: List[Dict[str, Any]] = []
        m3u_chs: List[Dict[str, Any]] = []
        
        # Step 1: Try Supabase first (fast, pre-consolidated)
        try:
            supabase_chs = await supabase_channels.fetch_channels()
            if supabase_chs:
                logger.info(f"Pulled {len(supabase_chs)} channels from Supabase")
        except Exception as e:
            logger.warning(f"Supabase fetch failed, falling back to M3U: {e}")
        
        # Step 1b: Fetch cached health data from SharedDb
        health_cache = {}
        try:
            from utils.shared_db import SharedDbService
            shared_db = SharedDbService()
            if shared_db.is_configured:
                health_cache = await shared_db.fetch_recent_results()
                if health_cache:
                    logger.info(f"Fetched {len(health_cache)} cached health results from SharedDb")
                    self._health_cache = health_cache  # Cache for stream_checker reuse
        except Exception as e:
            logger.debug(f"SharedDb health fetch failed (non-blocking): {e}")
        
        # Step 2: Fetch from M3U repositories (always, to find new channels)
        try:
            m3u_chs = await self.repository_handler.fetch_all_repositories(progress)
            logger.debug(f"M3U fetch complete, got {len(m3u_chs)} channels")
        except Exception as e:
            logger.error(f"Error fetching M3U repositories: {e}")
        
        # If both failed, nothing to do
        if not supabase_chs and not m3u_chs:
            logger.warning("No channels from Supabase or M3U")
            return
        
        try:
            with self._lock:
                existing_urls = {ch['url']: ch for ch in self.channels}
                merged_channels = []
                seen_urls: Set[str] = set()
                
                # Priority 1: Supabase channels (pre-consolidated, trusted)
                for ch in supabase_chs:
                    url = ch.get('url', '')
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    # Also mark all alternate URLs as seen
                    for u in ch.get('urls', []):
                        seen_urls.add(u)
                    # Preserve local working status if available
                    if url in existing_urls:
                        ex = existing_urls[url]
                        ch['is_working'] = ex.get('is_working')
                        ch['scan_status'] = ex.get('scan_status', 'pending')
                    else:
                        ch['scan_status'] = 'pending'
                    merged_channels.append(ch)
                
                # Priority 2: M3U channels (supplement)
                for channel in m3u_chs:
                    url = channel.get('url', '')
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    if url in existing_urls:
                        existing = existing_urls[url]
                        channel['is_working'] = existing.get('is_working')
                        channel['scan_status'] = existing.get('scan_status', 'pending')
                        channel['min_age'] = existing.get('min_age')
                    else:
                        channel['scan_status'] = 'pending'
                    merged_channels.append(channel)
                
                # Priority 3: Cached channels not in either source
                for url, existing in existing_urls.items():
                    if url not in seen_urls:
                        merged_channels.append(existing)
                        seen_urls.add(url)
                
                # Add custom channels from config
                if hasattr(config, 'CUSTOM_CHANNELS'):
                    for custom in config.CUSTOM_CHANNELS:
                        url = custom.get('url', '')
                        if url and url not in seen_urls:
                            channel = custom.copy()
                            if url in existing_urls:
                                existing = existing_urls[url]
                                channel['is_working'] = existing.get('is_working')
                                channel['scan_status'] = existing.get('scan_status', 'pending')
                            else:
                                channel['scan_status'] = 'pending'
                            merged_channels.append(channel)
                            seen_urls.add(url)
                
                self.channels = merged_channels
                logger.debug(f"Merged channels: {len(self.channels)}")
                self._organize_channels()
                logger.debug("Channels organized")
                
                # Apply health cache AFTER consolidation
                # Health cache only contains working channels (failed are always rescanned)
                # - New/pending channels: mark as working + scanned
                # - Already working channels confirmed by cache: refresh last_scanned
                #   so needs_rescan() skips them (no need to re-validate crowd-confirmed channels)
                # - Failed channels: leave for rescan (may have recovered)
                if health_cache:
                    now_iso = datetime.now().isoformat()
                    new_marked = 0
                    refreshed = 0
                    for ch in self.channels:
                        ch_urls = ch.get('urls', [ch.get('url', '')])
                        found_working = False
                        for u in ch_urls:
                            url_hash = hashlib.sha256(u.encode('utf-8')).hexdigest()
                            if url_hash in health_cache:
                                found_working = True
                                break
                        
                        if not found_working:
                            continue
                        
                        if ch.get('scan_status') != 'scanned':
                            # New/pending channel confirmed working
                            ch['is_working'] = True
                            ch['scan_status'] = 'scanned'
                            ch['last_scanned'] = now_iso
                            new_marked += 1
                        elif ch.get('is_working'):
                            # Already working + confirmed by cache — refresh timestamp
                            ch['last_scanned'] = now_iso
                            refreshed += 1
                        else:
                            # Was failed locally but working in cache — update
                            ch['is_working'] = True
                            ch['last_scanned'] = now_iso
                            refreshed += 1
                    logger.info(
                        f"Health cache: {new_marked} new channels marked, "
                        f"{refreshed} working channels refreshed "
                        f"(out of {len(self.channels)} total)"
                    )
        except Exception as e:
            logger.debug(f"Error merging channels: {e}")
            return
        
        # Step 3: Contribute new M3U channels back to Supabase (background)
        if m3u_chs and supabase_channels.is_configured():
            try:
                new_chs = supabase_channels.diff_channels(supabase_chs, m3u_chs)
                if new_chs:
                    contributed = await supabase_channels.contribute_channels(
                        new_chs, source='iptv-org'
                    )
                    logger.info(f"Contributed {contributed} new channels to Supabase")
            except Exception as e:
                logger.debug(f"Channel contribution failed (non-blocking): {e}")
        
        if self.on_channels_loaded:
            self.on_channels_loaded(len(self.channels))
        logger.debug("_fetch_and_update complete")
    
    def fetch_channels_async(self, callback: Optional[Callable] = None):
        """
        Fetch channels from repositories in background.
        
        Args:
            callback: Optional callback when fetch is complete
        """
        import asyncio
        
        def _run():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._fetch_and_update())
                logger.debug(f"Fetch complete. {len(self.channels)} channels ready. Starting validation...")
            except Exception as e:
                logger.debug(f"Error in fetch: {e}")
                
            finally:
                try:
                    loop.close()
                except Exception:
                    pass
                # Bug #108: Wrap callback in try/except so exceptions don't kill the thread
                try:
                    if callback:
                        callback()
                except Exception as e:
                    logger.error(f"Unhandled exception in fetch callback: {e}", exc_info=True)
                # Start validation after fetching (only unscanned channels)
                try:
                    self.validate_channels_async(rescan_all=False)
                except Exception as e:
                    logger.error(f"Unhandled exception starting validation: {e}", exc_info=True)
        
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
    
    def import_m3u_async(self, m3u_url: str,
                         on_done: Optional[Callable[[int], None]] = None):
        """Import channels from a custom M3U URL, merge, and contribute to Supabase.

        Args:
            m3u_url: URL to an M3U playlist
            on_done: Callback with count of new channels added
        """
        import asyncio

        async def _import():
            try:
                # Fetch and parse the M3U
                new_channels = await self.repository_handler.fetch_single_repository(
                    m3u_url
                )
                if not new_channels:
                    logger.warning(f"No channels found in M3U: {redact_url(m3u_url)}")
                    return 0

                logger.info(f"Parsed {len(new_channels)} channels from custom M3U")

                with self._lock:
                    existing_urls = {ch.get('url', ''): ch for ch in self.channels}
                    added = 0
                    for ch in new_channels:
                        url = ch.get('url', '')
                        if not url or url in existing_urls:
                            continue
                        ch['scan_status'] = 'pending'
                        ch['source'] = 'custom_m3u'
                        self.channels.append(ch)
                        existing_urls[url] = ch
                        added += 1

                    if added:
                        self._organize_channels()
                        self.save_channels()
                        logger.info(f"Added {added} new channels from custom M3U")

                # Contribute to Supabase
                if added and supabase_channels.is_configured():
                    await supabase_channels.contribute_channels(
                        new_channels, source='custom_m3u'
                    )

                return added
            except Exception as e:
                logger.error(f"Custom M3U import failed: {e}")
                return 0

        def _run():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                count = loop.run_until_complete(_import())
                loop.close()
            except Exception as e:
                logger.error(f"Unhandled exception in M3U import thread: {e}", exc_info=True)
                count = 0
            # Bug #108: Wrap callback in try/except so exceptions don't kill the thread
            try:
                if on_done:
                    on_done(count)
            except Exception as e:
                logger.error(f"Unhandled exception in import callback: {e}", exc_info=True)

        threading.Thread(target=_run, daemon=True).start()
    
    def validate_channels_async(self, rescan_all: bool = False):
        """Start validating channels in the background."""
        logger.debug(f"validate_channels_async called, rescan_all={rescan_all}")
        
        # Check if already running
        if self.stream_checker.is_running:
            logger.debug("Stream checker already running, skipping...")
            return
        
        with self._lock:
            if rescan_all:
                channels_to_check = self.channels.copy()
            else:
                channels_to_check = self._get_channels_to_scan_internal()
            
            # Log skip statistics
            total = len(self.channels)
            to_check = len(channels_to_check)
            skipped = total - to_check
            logger.debug(f"Scan skip: {skipped}/{total} channels skipped (scanned within {config.SCAN_SKIP_MINUTES} min)")
        
        logger.debug(f"Channels to check: {len(channels_to_check)}")
        
        if not channels_to_check:
            logger.debug("No channels to scan")
            if self.on_validation_complete:
                self.on_validation_complete()
            return
        
        logger.info(f"Starting validation of {len(channels_to_check)} channels...")
        
        def on_checked(channel: Dict[str, Any], current: int, total: int):
            # Queue the channel update instead of directly modifying
            is_working = channel.get('is_working', False)
            
            # Log progress every 100 channels or at start/end (reduced frequency)
            if current <= 3 or current % 100 == 0 or current == total:
                status = 'Working' if is_working else 'Failed'
                logger.debug(f"[{current}/{total}] {channel.get('name', 'Unknown')[:40]} -> {status}")
            
            # Queue the update for thread-safe processing
            if hasattr(self.stream_checker, '_update_queue'):
                self.stream_checker._update_queue.put_update(channel)
            
            if self._on_channel_validated:
                self._on_channel_validated(channel, current, total)
            
            # Process queued updates and auto-save less frequently (every 200 channels)
            if current % 200 == 0:
                self._process_queued_updates()
                self.save_channels()
        
        def on_complete(results: List[Dict[str, Any]]):
            # Process any remaining queued updates
            self._process_queued_updates()
            
            # Results are already updated via queued processing
            # Just re-organize to rebuild category/country dicts cleanly
            with self._lock:
                self._organize_channels()
            
            # Save to cache
            self.save_channels()
            
            if self._on_validation_complete:
                self._on_validation_complete()
            
            working_count = sum(1 for ch in self.channels if ch.get('is_working'))
            total_count = len(self.channels)
            logger.debug(f"Validation complete: {working_count}/{total_count} channels working")
        
        self.stream_checker.start_background_check(
            channels_to_check,
            on_channel_checked=on_checked,
            on_complete=on_complete,
            prefetched_health_cache=self._health_cache or None
        )
    
    def search_channels(self, query: str) -> List[Dict[str, Any]]:
        """Search for channels with prefix filters and fuzzy matching.
        
        Supports:
            country:US — filter by country
            category:news — filter by category/group
            working: — only working channels
            Plain text — fuzzy substring match on name
        
        Args:
            query: Search query string
            
        Returns:
            List of matching channels
        """
        query = query.strip()
        if not query:
            return []
        
        # Parse prefix filters
        filters = {}
        remaining_parts = []
        for part in query.split():
            if ':' in part:
                key, _, val = part.partition(':')
                key_lower = key.lower()
                if key_lower in ('country', 'category', 'group', 'working'):
                    filters[key_lower] = val.lower()
                    continue
            remaining_parts.append(part)
        
        text_query = ' '.join(remaining_parts).lower()
        
        with self._lock:
            results = []
            for ch in self.channels:
                # Apply prefix filters
                if 'country' in filters:
                    ch_country = (ch.get('country') or '').lower()
                    if filters['country'] not in ch_country:
                        continue
                if 'category' in filters or 'group' in filters:
                    cat_filter = filters.get('category') or filters.get('group', '')
                    ch_group = (ch.get('group') or '').lower()
                    if cat_filter not in ch_group:
                        continue
                if 'working' in filters:
                    if not ch.get('is_working', False):
                        continue
                
                # Text matching (fuzzy: match all words independently)
                if text_query:
                    ch_name = (ch.get('name') or '').lower()
                    words = text_query.split()
                    if all(w in ch_name for w in words):
                        results.append(ch)
                elif filters:
                    # Only prefix filters, no text — include all matching
                    results.append(ch)
            
            return results
    
    def stop(self):
        """Stop all background operations and clean up resources.
        
        Bug #76: Sets shutdown flag and joins checker thread before saving
        to prevent data races between active validation and shutdown save.
        """
        self._shutting_down = True
        
        # Stop the stream checker and wait for its thread to finish
        self.stream_checker.stop()
        if hasattr(self.stream_checker, '_thread') and self.stream_checker._thread:
            self.stream_checker._thread.join(timeout=5)
        
        # Save current state (safe now that checker thread has stopped)
        self.save_channels()
        
        # Clear memory
        with self._lock:
            self.categories.clear()
            self.countries.clear()
            self._url_to_index.clear()
        
        # Force garbage collection
        gc.collect()

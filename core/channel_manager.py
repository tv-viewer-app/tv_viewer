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
from typing import List, Dict, Any, Optional, Callable, Set
from collections import defaultdict

from utils.helpers import load_json_file, save_json_file, categorize_channel, get_channel_country, get_minimum_age, detect_media_type
from utils.logger import get_logger
from .repository import RepositoryHandler
from .stream_checker import StreamChecker
import config
from datetime import datetime

# Module logger
logger = get_logger(__name__)


def import_time_str() -> str:
    """Get current timestamp as ISO format string."""
    return datetime.now().isoformat()


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
                 '_on_validation_complete', '_on_fetch_progress', '_non_working_urls')
    
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
        data = load_json_file(config.CHANNELS_FILE)
        if data and 'channels' in data:
            with self._lock:
                self.channels = data['channels']
                # Ensure all channels have scan_status field
                for ch in self.channels:
                    if 'scan_status' not in ch:
                        ch['scan_status'] = 'pending' if ch.get('is_working') is None else 'scanned'
                self._organize_channels()
            print(f"Loaded {len(self.channels)} channels from cache")
            return True
        return False
    
    def save_channels(self) -> bool:
        """
        Save current channels to the cache file.
        
        Returns:
            True if saved successfully
        """
        with self._lock:
            data = {
                'channels': self.channels,
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
            self._non_working_urls = urls
    
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
        
        total = len(self.channels)
        
        # Pre-allocate category/country dicts to avoid resizing
        categories = self.categories
        countries = self.countries
        url_index = self._url_to_index
        
        for idx, channel in enumerate(self.channels):
            if idx % 5000 == 0 and idx > 0:
                print(f"Organizing channels: {idx}/{total}...")
            
            # Build URL index for fast lookups
            url = channel.get('url')
            if url:
                url_index[url] = idx
            
            # Always recalculate category to ensure consistency
            channel['category'] = categorize_channel(channel)
            category = channel['category']
            categories[category].append(channel)
            
            # Add country - check for None/empty, not just key existence
            existing_country = channel.get('country')
            if not existing_country or existing_country == 'Unknown':
                country = get_channel_country(channel)
                channel['country'] = country
                channel['country_group'] = country
            else:
                country = existing_country
                if 'country_group' not in channel:
                    channel['country_group'] = country
            countries[country].append(channel)
            
            # Add minimum age (only if not set)
            if 'min_age' not in channel:
                channel['min_age'] = get_minimum_age(channel)
            
            # Add media type (only if not set)
            if 'media_type' not in channel:
                channel['media_type'] = detect_media_type(channel)
        
        if total > 0:
            print(f"Organizing channels: {total}/{total} done.")
    
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
        """Filter channels by current media type filter."""
        if self.media_type_filter == 'All':
            return channels
        return [ch for ch in channels if ch.get('media_type', 'TV') == self.media_type_filter]
    
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
        """Fetch channels from repositories and update the list."""
        print("_fetch_and_update starting...")
        
        def progress(current, total):
            if self.on_fetch_progress:
                self.on_fetch_progress(current, total)
        
        try:
            channels = await self.repository_handler.fetch_all_repositories(progress)
            print(f"Repository fetch complete, got {len(channels)} channels")
        except Exception as e:
            logger.error(f"Error fetching repositories: {e}")
            
            return
        
        try:
            with self._lock:
                # Merge with existing, keeping status for known URLs
                existing_urls = {ch['url']: ch for ch in self.channels}
                
                merged_channels = []
                seen_urls = set()
                
                for channel in channels:
                    url = channel.get('url', '')
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    
                    if url in existing_urls:
                        # Keep existing channel data (working status, scan status)
                        existing = existing_urls[url]
                        channel['is_working'] = existing.get('is_working')
                        channel['scan_status'] = existing.get('scan_status', 'pending')
                        channel['min_age'] = existing.get('min_age')
                    else:
                        # New channel - mark as pending
                        channel['scan_status'] = 'pending'
                    
                    merged_channels.append(channel)
                
                # Also keep any cached channels that weren't in the new fetch
                for url, existing in existing_urls.items():
                    if url not in seen_urls:
                        merged_channels.append(existing)
                        seen_urls.add(url)
                
                # Add custom channels from config
                if hasattr(config, 'CUSTOM_CHANNELS'):
                    for custom in config.CUSTOM_CHANNELS:
                        url = custom.get('url', '')
                        if url and url not in seen_urls:
                            # Copy to avoid mutating config
                            channel = custom.copy()
                            if url in existing_urls:
                                existing = existing_urls[url]
                                channel['is_working'] = existing.get('is_working')
                                channel['scan_status'] = existing.get('scan_status', 'pending')
                            else:
                                channel['scan_status'] = 'pending'
                            merged_channels.append(channel)
                            seen_urls.add(url)
                            print(f"Added custom channel: {channel.get('name')}")
                
                self.channels = merged_channels
                print(f"Merged channels: {len(self.channels)}")
                self._organize_channels()
                print("Channels organized")
        except Exception as e:
            print(f"Error merging channels: {e}")
            
            return
        
        if self.on_channels_loaded:
            self.on_channels_loaded(len(channels))
        print("_fetch_and_update complete")
    
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
                print(f"Fetch complete. {len(self.channels)} channels ready. Starting validation...")
            except Exception as e:
                print(f"Error in fetch: {e}")
                
            finally:
                if callback:
                    callback()
                # Start validation after fetching
                self.validate_channels_async()
        
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
    
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
            # Update the channel in our list
            is_working = channel.get('is_working', False)
            
            # Log progress every 100 channels or at start/end (reduced frequency)
            if current <= 3 or current % 100 == 0 or current == total:
                status = 'Working' if is_working else 'Failed'
                logger.debug(f"[{current}/{total}] {channel.get('name', 'Unknown')[:40]} -> {status}")
            
            url = channel.get('url')
            if not url:
                return
            
            with self._lock:
                # Use URL index for O(1) lookup instead of O(n) scan
                idx = self._url_to_index.get(url)
                if idx is not None and idx < len(self.channels):
                    ch = self.channels[idx]
                    # Update in place - the same object is in categories/countries dicts
                    ch['is_working'] = is_working
                    ch['scan_status'] = 'scanned'
                    ch['last_scanned'] = channel.get('last_scanned')
            
            if self._on_channel_validated:
                self._on_channel_validated(channel, current, total)
            
            # Auto-save less frequently (every 200 channels)
            if current % 200 == 0:
                self.save_channels()
        
        def on_complete(results: List[Dict[str, Any]]):
            # Results are already updated in-place via on_checked callback
            # Just re-organize to rebuild category/country dicts cleanly
            with self._lock:
                self._organize_channels()
            
            # Save to cache
            self.save_channels()
            
            if self._on_validation_complete:
                self._on_validation_complete()
            
            working_count = sum(1 for ch in self.channels if ch.get('is_working'))
            total_count = len(self.channels)
            print(f"Validation complete: {working_count}/{total_count} channels working")
        
        self.stream_checker.start_background_check(
            channels_to_check,
            on_channel_checked=on_checked,
            on_complete=on_complete
        )
    
    def search_channels(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for channels by name.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching channels
        """
        query_lower = query.lower()
        with self._lock:
            return [
                ch for ch in self.channels
                if query_lower in ch.get('name', '').lower()
            ]
    
    def stop(self):
        """Stop all background operations and clean up resources."""
        self.stream_checker.stop()
        
        # Save current state
        self.save_channels()
        
        # Clear memory
        with self._lock:
            self.categories.clear()
            self.countries.clear()
            self._url_to_index.clear()
        
        # Force garbage collection
        gc.collect()

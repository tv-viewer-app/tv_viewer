"""Background stream validation checker.

This module provides asynchronous stream validation with optimized CPU and memory usage.

Optimization Notes:
- Uses asyncio with configurable concurrency limits to prevent CPU overload
- Implements adaptive batch processing to reduce memory pressure
- Thread priority is set to low (background) to minimize UI impact
- DNS caching reduces repeated DNS lookups
- Connection pooling with keep-alive for efficient HTTP connections
- Chunked processing with sleep intervals for CPU breathing room

Threading Model:
- Single background thread runs the asyncio event loop
- Semaphore limits concurrent HTTP requests (default: 5)
- Stop event allows graceful cancellation

Memory Optimization:
- Channels modified in-place (no copying)
- Batch processing with GC between batches
- Connection cleanup after each batch
- Minimal object allocation in hot paths
"""

import asyncio
import aiohttp
import threading
import gc
import sys
import ssl
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import config

# SharedDb integration for cross-platform validation result sharing
try:
    from utils.shared_db import SharedDbService, ChannelResult
except ImportError:
    SharedDbService = None
    ChannelResult = None

# Get module logger (use utils.logger for proper file handler)
try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)

# Platform-specific thread priority
if sys.platform == 'win32':
    import ctypes
    THREAD_PRIORITY_BELOW_NORMAL = -1
    THREAD_PRIORITY_LOWEST = -2
    THREAD_PRIORITY_IDLE = -15


class StreamChecker:
    """Checks if IPTV streams are working in the background.
    
    v2.1.1: Smart scanning — only checks primary URL during main scan,
    queues alternatives for background verification. Supports dynamic
    priority reordering based on user interaction.
    
    Attributes:
        _running: Boolean flag indicating if checker is active
        _thread: Background daemon thread for async loop
        _semaphore: Limits concurrent HTTP connections
        _stop_event: Thread-safe flag for graceful shutdown
        _loop: Asyncio event loop running in background thread
        _batch_size: Number of channels to process per batch (memory optimization)
        _request_delay: Delay between requests in seconds (CPU throttling)
        _alt_queue: Channels whose alternative URLs need background checking
        _priority_countries: Countries to scan first (set by user interaction)
    
    Example:
        checker = StreamChecker()
        checker.boost_country('Israel')  # Prioritize user's country
        checker.start_background_check(
            channels,
            on_channel_checked=lambda ch, cur, tot: logger.debug(f"{cur}/{tot}")
        )
    """
    
    __slots__ = ('_running', '_thread', '_semaphore', '_stop_event', '_loop', 
                 '_batch_size', '_request_delay', '_completed', '_session',
                 '_alt_queue', '_priority_countries', '_recently_played',
                 '_paused')
    
    def __init__(self, batch_size: int = None, request_delay: float = None):
        """Initialize StreamChecker with configurable parameters.
        
        Args:
            batch_size: Channels per batch (lower = less memory, slower)
            request_delay: Seconds between requests (higher = less CPU, slower)
        """
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._stop_event = threading.Event()
        self._paused = threading.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._batch_size = batch_size or getattr(config, 'SCAN_BATCH_SIZE', 200)
        self._request_delay = request_delay or getattr(config, 'SCAN_REQUEST_DELAY', 0.02)
        self._completed = 0
        self._session: Optional[aiohttp.ClientSession] = None
        self._alt_queue: List[Dict[str, Any]] = []
        self._priority_countries: List[str] = []
        self._recently_played: List[str] = []
    
    def boost_country(self, country: str):
        """Boost a country to the top of scan priority (called on user interaction)."""
        if not country or country == 'Unknown':
            return
        # Move to front, dedup
        if country in self._priority_countries:
            self._priority_countries.remove(country)
        self._priority_countries.insert(0, country)
        # Keep only top 5
        self._priority_countries = self._priority_countries[:5]
        logger.debug(f"Scan priority countries: {self._priority_countries}")
    
    def boost_channel(self, channel_url: str):
        """Record a recently played channel URL for priority scanning."""
        if channel_url and channel_url not in self._recently_played:
            self._recently_played.insert(0, channel_url)
            self._recently_played = self._recently_played[:20]

    def pause(self):
        """Pause scanning to yield network/CPU to user interaction (e.g. map)."""
        self._paused.set()
        logger.debug("StreamChecker paused")

    def resume(self):
        """Resume scanning after user interaction completes."""
        self._paused.clear()
        logger.debug("StreamChecker resumed")

    @property
    def is_paused(self) -> bool:
        return self._paused.is_set()

    def prioritize_channels(self, channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reorder channels by dynamic priority for scanning.
        
        Priority order:
        1. Recently played channels (highest — user cares about these)
        2. Channels in priority countries (user's active region)
        3. Never-scanned channels
        4. Working channels needing revalidation
        5. Known-failed channels (lowest)
        """
        recently_played = []
        priority_country = []
        never_scanned = []
        working_revalidate = []
        failed = []
        
        priority_set = set(self._priority_countries)
        played_set = set(self._recently_played)
        
        for ch in channels:
            url = ch.get('url', '')
            country = ch.get('country', 'Unknown')
            
            if url in played_set:
                recently_played.append(ch)
            elif country in priority_set:
                priority_country.append(ch)
            elif ch.get('scan_status') == 'pending' or not ch.get('last_scanned'):
                never_scanned.append(ch)
            elif ch.get('is_working'):
                working_revalidate.append(ch)
            else:
                failed.append(ch)
        
        # Sort priority countries by boost order
        if self._priority_countries:
            country_order = {c: i for i, c in enumerate(self._priority_countries)}
            priority_country.sort(key=lambda ch: country_order.get(ch.get('country', ''), 99))
        
        result = recently_played + priority_country + never_scanned + working_revalidate + failed
        if priority_set:
            logger.info(
                f"Scan priority: {len(recently_played)} played, "
                f"{len(priority_country)} priority-country, "
                f"{len(never_scanned)} new, "
                f"{len(working_revalidate)} revalidate, "
                f"{len(failed)} failed"
            )
        return result
    
    @staticmethod
    def _reorder_urls_by_health(
        channels: List[Dict[str, Any]],
        cache: Dict,
        shared_db,
    ):
        """Reorder each channel's URLs so known-working sources come first.
        
        Uses shared health cache to move working URLs to the front of each
        channel's 'urls' list and update 'working_url_index' accordingly.
        """
        reordered = 0
        for ch in channels:
            urls = ch.get('urls', [])
            if len(urls) <= 1:
                continue
            
            # Score each URL: working=0, unchecked=1, failed=2
            scored = []
            for i, url in enumerate(urls):
                cached = shared_db.get_cached_status(url, cache) if shared_db else None
                if cached and cached.status:
                    score = 0  # working
                elif cached and not cached.status:
                    score = 2  # failed
                else:
                    score = 1  # unchecked
                scored.append((score, i, url))
            
            scored.sort(key=lambda x: x[0])
            new_urls = [s[2] for s in scored]
            
            if new_urls != urls:
                ch['urls'] = new_urls
                ch['url'] = new_urls[0]
                ch['working_url_index'] = 0
                reordered += 1
        
        if reordered:
            logger.info(f"Reordered URLs by health for {reordered} multi-source channels")

    async def check_stream(
        self, 
        channel: Dict[str, Any],
        session: aiohttp.ClientSession
    ) -> Dict[str, Any]:
        """
        Smart stream check — only tests the primary (working) URL.
        
        v2.1.1: Instead of iterating all URLs, checks only the workingUrlIndex URL.
        If it fails, marks channel as failed and queues it for background alternative
        checking. This makes the main scan 2-5x faster for multi-URL channels.
        
        Args:
            channel: Channel dictionary with 'url' or 'urls' key
            session: aiohttp session to use
            
        Returns:
            Channel dict with 'is_working', 'working_url_index', and 'last_scanned' updated
        """
        urls = channel.get('urls', [])
        if not urls:
            single_url = channel.get('url', '')
            urls = [single_url] if single_url else []
        
        channel['last_scanned'] = datetime.now().isoformat()
        
        if not urls:
            channel['is_working'] = False
            return channel
        
        # Check only the primary (last-known-working) URL
        primary_idx = channel.get('working_url_index', 0)
        if primary_idx >= len(urls):
            primary_idx = 0
        
        primary_url = urls[primary_idx]
        
        if not primary_url or not isinstance(primary_url, str):
            channel['is_working'] = False
            return channel
        
        if not primary_url.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')):
            channel['is_working'] = False
            return channel
        
        # Non-HTTP streams can't be checked via HTTP — assume working
        if primary_url.startswith(('rtmp://', 'rtsp://')):
            channel['is_working'] = True
            channel['url'] = primary_url
            return channel
        
        try:
            async with self._semaphore:
                is_working = await self._check_single_url(primary_url, session)
                if is_working:
                    channel['is_working'] = True
                    channel['url'] = primary_url
                    return channel
        except Exception:
            pass
        
        # Primary URL failed — if there are alternatives, queue for background check
        if len(urls) > 1:
            self._alt_queue.append(channel)
            logger.debug(f"Queued {channel.get('name', '?')[:30]} for alt-URL check ({len(urls)-1} alternatives)")
        
        channel['is_working'] = False
        return channel
    
    async def _check_alternatives(
        self,
        session: aiohttp.ClientSession,
        on_channel_checked: Optional[Callable] = None,
    ):
        """Background check of alternative URLs for channels whose primary failed.
        
        Runs after the main scan completes. Tries remaining URLs for each
        queued channel and updates working_url_index on success.
        """
        if not self._alt_queue:
            return
        
        alt_count = len(self._alt_queue)
        logger.info(f"Checking alternative URLs for {alt_count} channels...")
        
        resolved = 0
        for channel in self._alt_queue:
            if self._stop_event.is_set():
                break
            
            urls = channel.get('urls', [])
            primary_idx = channel.get('working_url_index', 0)
            
            for idx, url in enumerate(urls):
                if idx == primary_idx:
                    continue  # Already checked
                if not url or not url.startswith(('http://', 'https://')):
                    continue
                
                try:
                    async with self._semaphore:
                        is_working = await self._check_single_url(url, session)
                        if is_working:
                            channel['is_working'] = True
                            channel['working_url_index'] = idx
                            channel['url'] = url
                            resolved += 1
                            break
                except Exception:
                    continue
                
                if self._request_delay > 0:
                    await asyncio.sleep(self._request_delay)
        
        self._alt_queue.clear()
        logger.info(f"Alternative URL check: resolved {resolved}/{alt_count} channels")
    
    async def _check_single_url(
        self,
        url: str,
        session: aiohttp.ClientSession
    ) -> bool:
        """Check if a single URL is accessible. Returns True if working."""
        try:
            # HEAD first — fast, no body download
            async with session.head(url, allow_redirects=True) as response:
                if response.status == 200:
                    ct = (response.content_type or '').lower()
                    # HTML response = error page, not a stream
                    return 'text/html' not in ct
                elif response.status == 405:
                    # HEAD rejected, try GET with Range
                    async with session.get(
                        url,
                        headers={'Range': 'bytes=0-512'},
                        allow_redirects=True
                    ) as get_resp:
                        if get_resp.status in (200, 206):
                            ct = (get_resp.content_type or '').lower()
                            return 'text/html' not in ct
                elif response.status in (301, 302, 303, 307, 308):
                    return True
        except (asyncio.TimeoutError, asyncio.CancelledError):
            pass
        except aiohttp.ClientConnectorError:
            pass
        except aiohttp.ClientError:
            pass
        except ssl.SSLError as e:
            logger.debug(f"SSL error for {url[:40]}: {type(e).__name__}")
        except Exception:
            pass
        return False
    
    async def check_streams_batch(
        self,
        channels: List[Dict[str, Any]],
        on_channel_checked: Optional[Callable[[Dict[str, Any], int, int], None]] = None,
        prefetched_health_cache: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Check multiple streams with smart priority ordering.
        
        v2.1.1 optimizations:
        - Priority ordering: user country > recently played > new > revalidate > failed
        - Primary-URL-only scan (alternatives checked in background pass)
        - SharedDb cache skip for recently-validated channels
        - Batch processing with GC and delays
        
        Args:
            channels: List of channel dictionaries to validate
            on_channel_checked: Optional callback(channel, current, total) for progress
            prefetched_health_cache: Optional pre-fetched SharedDb cache to avoid double fetch
            
        Returns:
            Same list of channels with 'is_working' status updated in-place
        """
        max_concurrent = getattr(config, 'MAX_CONCURRENT_CHECKS', 5)
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._alt_queue = []  # Reset alternative URL queue
        
        timeout = aiohttp.ClientTimeout(
            total=getattr(config, 'STREAM_CHECK_TIMEOUT', 5),
            connect=3,
            sock_read=getattr(config, 'STREAM_CHECK_TIMEOUT', 5)
        )
        
        total = len(channels)
        self._completed = 0
        
        # --- SharedDb: Fetch cached results to skip recently-validated channels ---
        shared_db = None
        shared_db_cache = {}
        channels_to_validate = channels
        try:
            if SharedDbService is not None:
                shared_db = SharedDbService()
                # Reuse prefetched cache if available, otherwise fetch fresh
                if prefetched_health_cache:
                    shared_db_cache = prefetched_health_cache
                    logger.info(f"SharedDb: Reusing {len(shared_db_cache)} prefetched health results")
                elif shared_db.is_configured:
                    shared_db_cache = await shared_db.fetch_recent_results()
                else:
                    # Not configured — try local cache fallback
                    shared_db_cache = SharedDbService.load_local_cache()
                if shared_db_cache:
                        channels_to_validate = []
                        skipped = 0
                        for ch in channels:
                            url = ch.get('url', '')
                            if url and shared_db.should_skip_validation(url, shared_db_cache):
                                ch['is_working'] = True
                                ch['last_scanned'] = datetime.now().isoformat()
                                skipped += 1
                                self._completed += 1
                                if on_channel_checked:
                                    try:
                                        on_channel_checked(ch, self._completed, total)
                                    except Exception:
                                        pass
                            else:
                                channels_to_validate.append(ch)
                        if skipped > 0:
                            logger.info(
                                f"SharedDb: Skipped {skipped}/{total} channels "
                                f"with cached working status"
                            )
                        # Sort multi-URL channels: put known-working URLs first
                        self._reorder_urls_by_health(channels_to_validate, shared_db_cache, shared_db)
        except Exception as e:
            logger.warning(f"SharedDb: Failed to fetch cached results: {e}")
            channels_to_validate = channels
            self._completed = 0
        # --- End SharedDb fetch ---
        
        # Apply dynamic priority ordering
        channels_to_validate = self.prioritize_channels(channels_to_validate)
        
        async def check_with_callback(channel: Dict[str, Any], session: aiohttp.ClientSession):
            """Check single channel with callback notification."""
            if self._stop_event.is_set():
                return channel
            
            result = await self.check_stream(channel, session)
            
            if self._request_delay > 0:
                await asyncio.sleep(self._request_delay)
            
            self._completed += 1
            
            if on_channel_checked:
                try:
                    on_channel_checked(result, self._completed, total)
                except Exception:
                    pass
            
            return result
        
        connector = aiohttp.TCPConnector(
            limit=max_concurrent,
            limit_per_host=3,
            force_close=False,
            enable_cleanup_closed=True,
            ttl_dns_cache=600,
            use_dns_cache=True,
            keepalive_timeout=30,
        )
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            self._session = session
            
            for i in range(0, len(channels_to_validate), self._batch_size):
                if self._stop_event.is_set():
                    break
                
                # Wait while paused (map open, user interaction)
                while self._paused.is_set() and not self._stop_event.is_set():
                    await asyncio.sleep(0.5)
                    
                batch = channels_to_validate[i:i + self._batch_size]
                tasks = [check_with_callback(ch, session) for ch in batch]
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Stream results to Supabase per-batch
                if shared_db is not None and shared_db.is_configured:
                    try:
                        await shared_db.upload_batch_inline(batch, session)
                    except Exception as e:
                        logger.warning(f"SharedDb: Upload batch failed: {e}")
                
                gc.collect(0)
                
                batch_delay = getattr(config, 'SCAN_BATCH_DELAY', 0.5)
                await asyncio.sleep(batch_delay)
            
            # Phase 2: Check alternative URLs for failed channels
            if not self._stop_event.is_set():
                await self._check_alternatives(session, on_channel_checked)
            
            self._session = None
        
        return channels
    
    def start_background_check(
        self,
        channels: List[Dict[str, Any]],
        on_channel_checked: Optional[Callable[[Dict[str, Any], int, int], None]] = None,
        on_complete: Optional[Callable[[List[Dict[str, Any]]], None]] = None,
        prefetched_health_cache: Optional[Dict] = None
    ):
        """Start checking streams in a background thread with low priority.
        
        This method spawns a daemon thread to run the async validation loop.
        The thread is set to below-normal priority to minimize impact on UI.
        
        Args:
            channels: List of channel dictionaries to validate
            on_channel_checked: Optional callback(channel, current, total) per channel
            on_complete: Optional callback(results) when validation finishes
            prefetched_health_cache: Optional pre-fetched SharedDb cache to avoid double fetch
        """
        if self._running:
            logger.debug("Stream checker already running")
            return
        
        self._stop_event.clear()
        
        def _run():
            """Background thread main function."""
            # Set thread to low priority for background processing
            self._set_thread_priority()
            
            self._running = True
            try:
                # Create new event loop for this thread
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
                
                # Run the async batch check
                results = self._loop.run_until_complete(
                    self.check_streams_batch(
                        channels, on_channel_checked,
                        prefetched_health_cache=prefetched_health_cache
                    )
                )
                
                # Call completion callback if not stopped
                if on_complete and not self._stop_event.is_set():
                    on_complete(results)
                    
            except Exception as e:
                logger.error(f"Error in background stream check: {e}")
            finally:
                # Proper cleanup of asyncio resources
                self._cleanup_loop()
                self._running = False
                # Full GC after validation completes
                gc.collect()
        
        # Create and start daemon thread
        self._thread = threading.Thread(
            target=_run, 
            daemon=True,
            name="StreamChecker-Background"
        )
        self._thread.start()
    
    def _set_thread_priority(self):
        """Set current thread to low priority for background processing.
        
        Bug #95 / #122: Removed os.nice() — it raises the nice value of the
        entire process, not just the calling thread.  On Windows we use the
        per-thread SetThreadPriority API instead.  On Unix there is no portable
        per-thread nice, so we skip priority adjustment.
        """
        try:
            if sys.platform == 'win32':
                # Windows: Set thread priority to below normal
                handle = ctypes.windll.kernel32.GetCurrentThread()
                ctypes.windll.kernel32.SetThreadPriority(handle, THREAD_PRIORITY_BELOW_NORMAL)
            # Unix: intentionally no-op — os.nice() affects the whole process
        except Exception:
            pass  # Silently continue if priority cannot be set
    
    def _cleanup_loop(self):
        """Clean up asyncio event loop resources."""
        if self._loop:
            try:
                # Cancel any pending tasks
                pending = asyncio.all_tasks(self._loop)
                for task in pending:
                    task.cancel()
                if pending:
                    self._loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
            except Exception:
                pass
            finally:
                try:
                    self._loop.close()
                except Exception:
                    pass
                self._loop = None
    
    def stop(self):
        """Stop the background checker."""
        self._stop_event.set()
        self._running = False
        # Cancel loop if running
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
    
    @property
    def is_running(self) -> bool:
        """Check if the stream checker is currently running."""
        return self._running

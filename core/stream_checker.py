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

# Get module logger
logger = logging.getLogger(__name__)

# Platform-specific thread priority
if sys.platform == 'win32':
    import ctypes
    THREAD_PRIORITY_BELOW_NORMAL = -1
    THREAD_PRIORITY_LOWEST = -2
    THREAD_PRIORITY_IDLE = -15


class StreamChecker:
    """Checks if IPTV streams are working in the background.
    
    This class manages asynchronous HTTP validation of IPTV streams with
    optimizations for CPU, memory, and network efficiency.
    
    Attributes:
        _running: Boolean flag indicating if checker is active
        _thread: Background daemon thread for async loop
        _semaphore: Limits concurrent HTTP connections
        _stop_event: Thread-safe flag for graceful shutdown
        _loop: Asyncio event loop running in background thread
        _batch_size: Number of channels to process per batch (memory optimization)
        _request_delay: Delay between requests in seconds (CPU throttling)
    
    Example:
        checker = StreamChecker()
        checker.start_background_check(
            channels,
            on_channel_checked=lambda ch, cur, tot: logger.debug(f"{cur}/{tot}")
        )
    """
    
    __slots__ = ('_running', '_thread', '_semaphore', '_stop_event', '_loop', 
                 '_batch_size', '_request_delay', '_completed', '_session')
    
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
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._batch_size = batch_size or getattr(config, 'SCAN_BATCH_SIZE', 200)
        self._request_delay = request_delay or getattr(config, 'SCAN_REQUEST_DELAY', 0.02)
        self._completed = 0
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def check_stream(
        self, 
        channel: Dict[str, Any],
        session: aiohttp.ClientSession
    ) -> Dict[str, Any]:
        """
        Check if a single stream is accessible - optimized for minimal CPU.
        
        Args:
            channel: Channel dictionary with 'url' key
            session: aiohttp session to use
            
        Returns:
            Channel dict with 'is_working' and 'last_scanned' keys updated in-place
        """
        url = channel.get('url', '')
        # Update in-place to reduce memory allocation
        channel['is_working'] = False
        channel['last_scanned'] = datetime.now().isoformat()
        
        if not url:
            return channel
        
        # Security: Validate URL scheme
        if not url.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')):
            return channel
        
        # Security: Skip file:// and other dangerous schemes
        if url.startswith(('file://', 'javascript:', 'data:')):
            return channel
        
        try:
            async with self._semaphore:
                # Just check if we can connect and get headers - fastest method
                async with session.head(url, allow_redirects=True) as response:
                    if response.status == 200:
                        channel['is_working'] = True
                    elif response.status == 405:
                        # HEAD not allowed, try GET with minimal range
                        async with session.get(
                            url, 
                            headers={'Range': 'bytes=0-512'},
                            allow_redirects=True
                        ) as get_response:
                            channel['is_working'] = get_response.status in (200, 206)
                    elif response.status in (301, 302, 303, 307, 308):
                        # Redirect - consider as potentially working
                        channel['is_working'] = True
        except (asyncio.TimeoutError, asyncio.CancelledError):
            pass  # Timeout or cancelled - expected for unreachable streams
        except aiohttp.ClientConnectorError:
            pass  # Connection error - stream unreachable
        except aiohttp.ClientError:
            pass  # Other client errors - stream issues
        except ssl.SSLError as e:
            logger.debug(f"SSL error for {url[:40]}: {type(e).__name__}")
        except Exception:
            pass  # Silently handle other errors in background scan
        
        return channel
    
    async def check_streams_batch(
        self,
        channels: List[Dict[str, Any]],
        on_channel_checked: Optional[Callable[[Dict[str, Any], int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """Check multiple streams concurrently with optimized resource usage.
        
        This method implements several optimizations:
        - Semaphore-limited concurrency prevents resource exhaustion
        - Batch processing reduces memory pressure
        - DNS caching reduces repeated lookups
        - Connection pooling with per-host limits
        - Adaptive delays prevent CPU saturation
        
        Args:
            channels: List of channel dictionaries to validate
            on_channel_checked: Optional callback(channel, current, total) for progress
            
        Returns:
            Same list of channels with 'is_working' status updated in-place
        """
        max_concurrent = getattr(config, 'MAX_CONCURRENT_CHECKS', 5)
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
        timeout = aiohttp.ClientTimeout(
            total=getattr(config, 'STREAM_CHECK_TIMEOUT', 5),
            connect=3,  # Fast connection timeout
            sock_read=getattr(config, 'STREAM_CHECK_TIMEOUT', 5)
        )
        
        total = len(channels)
        self._completed = 0
        
        async def check_with_callback(channel: Dict[str, Any], session: aiohttp.ClientSession):
            """Check single channel with callback notification."""
            # Check for stop signal before processing
            if self._stop_event.is_set():
                return channel
            
            result = await self.check_stream(channel, session)
            
            # CPU breathing room - yield control
            if self._request_delay > 0:
                await asyncio.sleep(self._request_delay)
            
            self._completed += 1
            
            if on_channel_checked:
                try:
                    on_channel_checked(result, self._completed, total)
                except Exception:
                    pass  # Don't let callback errors stop the scan
            
            return result
        
        # Optimized connection pooling - fewer connections = less resource usage
        connector = aiohttp.TCPConnector(
            limit=max_concurrent,        # Total connection limit
            limit_per_host=2,            # Prevent overwhelming single servers
            force_close=True,            # Close connections after use
            enable_cleanup_closed=True,  # Clean up closed connections
            ttl_dns_cache=600,           # Cache DNS for 10 minutes
            use_dns_cache=True,          # Enable DNS caching
        )
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            self._session = session
            
            # Process in smaller batches to reduce memory pressure
            for i in range(0, len(channels), self._batch_size):
                if self._stop_event.is_set():
                    break
                    
                batch = channels[i:i + self._batch_size]
                
                # Create tasks for this batch only
                tasks = [check_with_callback(ch, session) for ch in batch]
                
                # Gather with return_exceptions to continue on individual failures
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Memory optimization: trigger generation-0 GC between batches
                gc.collect(0)
                
                # CPU breathing room between batches
                await asyncio.sleep(0.1)
            
            self._session = None
        
        return channels
    
    def start_background_check(
        self,
        channels: List[Dict[str, Any]],
        on_channel_checked: Optional[Callable[[Dict[str, Any], int, int], None]] = None,
        on_complete: Optional[Callable[[List[Dict[str, Any]]], None]] = None
    ):
        """Start checking streams in a background thread with low priority.
        
        This method spawns a daemon thread to run the async validation loop.
        The thread is set to below-normal priority to minimize impact on UI.
        
        Args:
            channels: List of channel dictionaries to validate
            on_channel_checked: Optional callback(channel, current, total) per channel
            on_complete: Optional callback(results) when validation finishes
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
                    self.check_streams_batch(channels, on_channel_checked)
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
        """Set current thread to low priority for background processing."""
        try:
            if sys.platform == 'win32':
                # Windows: Set thread priority to below normal
                handle = ctypes.windll.kernel32.GetCurrentThread()
                ctypes.windll.kernel32.SetThreadPriority(handle, THREAD_PRIORITY_BELOW_NORMAL)
            else:
                # Unix: Set nice value (higher = lower priority)
                import os
                os.nice(10)
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

"""IPTV Repository handler for fetching channel lists."""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, Callable
from utils.helpers import parse_m3u
from utils.logger import get_logger
import config

logger = get_logger(__name__)


class RepositoryHandler:
    """Handles fetching and parsing IPTV repository playlists."""
    
    # Allowed URL schemes for security
    ALLOWED_SCHEMES = ('http://', 'https://')
    
    def __init__(self):
        self.repositories = config.IPTV_REPOSITORIES.copy()
        self._session: Optional[aiohttp.ClientSession] = None
    
    def _validate_url(self, url: str) -> bool:
        """Validate URL for security."""
        if not url:
            return False
        url_lower = url.lower().strip()
        return url_lower.startswith(self.ALLOWED_SCHEMES)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
            # Security: Enable SSL verification for HTTPS connections
            connector = aiohttp.TCPConnector(limit=10)
            self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self._session
    
    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def fetch_repository(self, url: str) -> List[Dict[str, Any]]:
        """
        Fetch and parse a single repository URL.
        
        Args:
            url: M3U playlist URL
            
        Returns:
            List of channel dictionaries
        """
        # Security: Validate URL
        if not self._validate_url(url):
            logger.debug(f"Invalid or unsafe URL: {url}")
            return []
        
        try:
            session = await self._get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text(errors='replace')
                    # Security: Limit content size to prevent memory issues
                    if len(content) > 50 * 1024 * 1024:  # 50MB limit
                        logger.debug(f"Content too large from {url}")
                        return []
                    channels = parse_m3u(content)
                    logger.debug(f"Fetched {len(channels)} channels from {url}")
                    return channels
                else:
                    logger.debug(f"Failed to fetch {url}: HTTP {response.status}")
        except asyncio.TimeoutError:
            logger.debug(f"Timeout fetching {url}")
        except aiohttp.ClientError as e:
            logger.debug(f"Error fetching {url}: {e}")
        except Exception as e:
            logger.debug(f"Unexpected error fetching {url}: {e}")
        
        return []
    
    async def fetch_all_repositories(
        self, 
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch channels from all configured repositories.
        
        Args:
            progress_callback: Optional callback(current, total) for progress updates
            
        Returns:
            Combined list of all channels (with duplicates removed)
        """
        all_channels = []
        seen_urls: set = set()
        
        total = len(self.repositories)
        
        try:
            for i, repo_url in enumerate(self.repositories):
                channels = await self.fetch_repository(repo_url)
                
                # Deduplicate based on URL
                for channel in channels:
                    url = channel.get('url', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_channels.append(channel)
                
                if progress_callback:
                    progress_callback(i + 1, total)
        finally:
            # Always close session when done
            await self.close()
        
        logger.debug(f"Total unique channels fetched: {len(all_channels)}")
        return all_channels
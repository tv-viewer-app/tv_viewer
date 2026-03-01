"""Shared database service for syncing channel validation results.

This module provides Supabase integration for sharing channel validation results
across platforms (Android Flutter + Windows Python).

Features:
    - Anonymous access (no user accounts required)
    - Privacy-first: URLs are hashed with SHA256
    - Cross-platform compatibility
    - Efficient: Batch operations and 24h cache to skip re-scanning

Database Schema:
    - url_hash (TEXT, PRIMARY KEY): SHA256 hash of channel URL
    - status (TEXT): 'working' or 'failed'
    - last_checked (TIMESTAMP): Last validation timestamp
    - response_time_ms (INTEGER): Response time in milliseconds

Usage:
    # Fetch recent results before scanning
    db = SharedDbService()
    cache = await db.fetch_recent_results()
    
    # Check if channel should be skipped
    if db.should_skip_validation(channel_url, cache):
        # Skip validation, use cached result
        pass
    
    # Upload results after scanning
    results = [
        ChannelResult(url='http://...', is_working=True, response_time_ms=150),
        ChannelResult(url='http://...', is_working=False),
    ]
    await db.upload_results(results)
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, NamedTuple
from dataclasses import dataclass, asdict

try:
    import aiohttp
except ImportError:
    aiohttp = None
    logging.warning("aiohttp not installed - shared database features will be disabled")

# Get module logger
logger = logging.getLogger(__name__)

# Supabase configuration
# TODO: Replace with your actual Supabase project URL and anon key
# Get these from: https://app.supabase.com/project/_/settings/api
SUPABASE_URL = 'YOUR_SUPABASE_PROJECT_URL'
SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY'
TABLE_NAME = 'channel_status'

# Feature flag to enable/disable shared database
# Set to False if you don't want to use the shared database
ENABLED = False  # TODO: Set to True after Supabase setup

# Cache duration - only fetch results checked within last 24 hours
CACHE_DURATION_HOURS = 24


@dataclass
class ChannelResult:
    """Result of a channel validation check."""
    url: str
    is_working: bool
    last_checked: datetime
    response_time_ms: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'url': self.url,
            'is_working': self.is_working,
            'last_checked': self.last_checked.isoformat(),
            'response_time_ms': self.response_time_ms,
        }


@dataclass
class ChannelStatusResult:
    """Cached channel status from shared database."""
    status: bool
    last_checked: datetime
    response_time_ms: Optional[int] = None


class SharedDbService:
    """Service for syncing channel validation results with Supabase.
    
    This service provides methods to fetch and upload channel validation results
    to a shared Supabase database for cross-platform synchronization.
    
    Attributes:
        supabase_url: Supabase project URL
        supabase_key: Supabase anonymous API key
        table_name: Name of the database table
        enabled: Whether the service is enabled
    """
    
    def __init__(
        self,
        supabase_url: str = SUPABASE_URL,
        supabase_key: str = SUPABASE_ANON_KEY,
        table_name: str = TABLE_NAME,
        enabled: bool = ENABLED,
    ):
        """Initialize the SharedDbService.
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anonymous API key
            table_name: Database table name
            enabled: Whether the service is enabled
        """
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.table_name = table_name
        self.enabled = enabled
        
    @staticmethod
    def _hash_url(url: str) -> str:
        """Hash a URL with SHA256 for privacy.
        
        Args:
            url: The URL to hash
            
        Returns:
            Hexadecimal SHA256 hash string
        """
        return hashlib.sha256(url.encode('utf-8')).hexdigest()
    
    @property
    def is_configured(self) -> bool:
        """Check if the service is properly configured.
        
        Returns:
            True if configured and enabled, False otherwise
        """
        return (
            self.enabled and
            aiohttp is not None and
            self.supabase_url != 'YOUR_SUPABASE_PROJECT_URL' and
            self.supabase_key != 'YOUR_SUPABASE_ANON_KEY'
        )
    
    async def fetch_recent_results(self) -> Dict[str, ChannelStatusResult]:
        """Fetch recent channel validation results from shared database.
        
        Fetches all channel statuses that were checked within the last 24 hours.
        
        Returns:
            Dictionary mapping url_hash to ChannelStatusResult
            Returns empty dict if service is disabled or fetch fails
        """
        if not self.is_configured:
            logger.debug('SharedDbService: Service not configured or disabled')
            return {}
        
        try:
            logger.info('Fetching recent channel results from shared database...')
            
            # Calculate timestamp for 24 hours ago
            cutoff_time = (
                datetime.utcnow() - timedelta(hours=CACHE_DURATION_HOURS)
            ).isoformat()
            
            # Build query URL
            url = f'{self.supabase_url}/rest/v1/{self.table_name}'
            params = {
                'last_checked': f'gte.{cutoff_time}',
                'select': 'url_hash,status,last_checked,response_time_ms',
            }
            
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = {}
                        
                        for item in data:
                            url_hash = item['url_hash']
                            status = item['status'] == 'working'
                            last_checked = datetime.fromisoformat(
                                item['last_checked'].replace('Z', '+00:00')
                            )
                            response_time_ms = item.get('response_time_ms')
                            
                            results[url_hash] = ChannelStatusResult(
                                status=status,
                                last_checked=last_checked,
                                response_time_ms=response_time_ms,
                            )
                        
                        logger.info(
                            f'Fetched {len(results)} recent channel results from shared database'
                        )
                        return results
                    else:
                        logger.warning(
                            f'Failed to fetch shared database results: {response.status}'
                        )
                        return {}
                        
        except Exception as e:
            logger.error(f'Error fetching from shared database: {e}', exc_info=True)
            return {}  # Return empty dict on error - don't block the app
    
    async def upload_results(self, results: List[ChannelResult]) -> bool:
        """Upload channel validation results to shared database.
        
        Performs a batch upsert operation (insert or update on conflict).
        
        Args:
            results: List of ChannelResult objects to upload
            
        Returns:
            True if upload succeeded, False otherwise
        """
        if not self.is_configured:
            logger.debug('SharedDbService: Service not configured or disabled')
            return False
        
        if not results:
            logger.debug('SharedDbService: No results to upload')
            return True
        
        try:
            logger.info(f'Uploading {len(results)} channel results to shared database...')
            
            # Prepare batch payload
            payload = [
                {
                    'url_hash': self._hash_url(result.url),
                    'status': 'working' if result.is_working else 'failed',
                    'last_checked': result.last_checked.isoformat(),
                    'response_time_ms': result.response_time_ms,
                }
                for result in results
            ]
            
            # Upsert to Supabase (insert or update on conflict)
            url = f'{self.supabase_url}/rest/v1/{self.table_name}'
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json',
                'Prefer': 'resolution=merge-duplicates',  # Upsert on conflict
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status in (200, 201):
                        logger.info(
                            f'Successfully uploaded {len(results)} channel results'
                        )
                        return True
                    else:
                        error_body = await response.text()
                        logger.warning(
                            f'Failed to upload results: {response.status} - {error_body}'
                        )
                        return False
                        
        except Exception as e:
            logger.error(f'Error uploading to shared database: {e}', exc_info=True)
            return False  # Don't block on upload failure
    
    def get_cached_status(
        self,
        url: str,
        cache: Dict[str, ChannelStatusResult]
    ) -> Optional[ChannelStatusResult]:
        """Get cached status for a specific URL.
        
        Args:
            url: The channel URL to look up
            cache: Dictionary of cached results from fetch_recent_results()
            
        Returns:
            ChannelStatusResult if available and recent, None otherwise
        """
        url_hash = self._hash_url(url)
        return cache.get(url_hash)
    
    def should_skip_validation(
        self,
        url: str,
        cache: Dict[str, ChannelStatusResult]
    ) -> bool:
        """Check if a channel should be skipped based on cached results.
        
        Only skips validation if:
        - Channel is in cache
        - Status is 'working'
        - Last checked within CACHE_DURATION_HOURS
        
        Args:
            url: The channel URL to check
            cache: Dictionary of cached results from fetch_recent_results()
            
        Returns:
            True if validation should be skipped, False otherwise
        """
        cached = self.get_cached_status(url, cache)
        
        if cached is None:
            return False
        
        # Only skip if it's working and recently checked
        age = datetime.utcnow() - cached.last_checked
        return cached.status and age < timedelta(hours=CACHE_DURATION_HOURS)


# Example usage
if __name__ == '__main__':
    import asyncio
    
    async def main():
        """Example usage of SharedDbService."""
        db = SharedDbService()
        
        if not db.is_configured:
            print("Service not configured. Please set SUPABASE_URL, SUPABASE_ANON_KEY, and ENABLED=True")
            return
        
        # Fetch recent results
        print("Fetching recent results...")
        cache = await db.fetch_recent_results()
        print(f"Found {len(cache)} cached results")
        
        # Example: Upload results
        test_results = [
            ChannelResult(
                url='http://example.com/stream1.m3u8',
                is_working=True,
                last_checked=datetime.utcnow(),
                response_time_ms=150,
            ),
            ChannelResult(
                url='http://example.com/stream2.m3u8',
                is_working=False,
                last_checked=datetime.utcnow(),
            ),
        ]
        
        print(f"Uploading {len(test_results)} test results...")
        success = await db.upload_results(test_results)
        print(f"Upload {'succeeded' if success else 'failed'}")
    
    asyncio.run(main())

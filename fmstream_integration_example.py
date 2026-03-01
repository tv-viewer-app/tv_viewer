"""Example integration of FMStream into channel manager.

This module demonstrates how to integrate FMStream radio stations
into the existing channel management system.
"""

import logging
from typing import List, Dict, Any, Optional
from utils.fmstream import fetch_fmstream_stations

logger = logging.getLogger(__name__)


class ChannelManagerWithFMStream:
    """Extended channel manager with FMStream support.
    
    This is an example implementation showing how to integrate
    FMStream radio stations with existing M3U channels.
    """
    
    def __init__(self, enable_fmstream: bool = True):
        """Initialize the channel manager.
        
        Args:
            enable_fmstream: Whether to enable FMStream source
        """
        self.enable_fmstream = enable_fmstream
        self.channels: List[Dict[str, Any]] = []
        self.fmstream_url = 'http://fmstream.org'
        self.fmstream_max_stations = 1000
    
    def load_all_channels(
        self,
        m3u_repositories: List[str],
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """Load channels from all sources (M3U + FMStream).
        
        Args:
            m3u_repositories: List of M3U repository URLs
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of all channels with duplicates removed
        """
        all_channels = []
        
        # Step 1: Load M3U channels
        logger.info(f"Loading channels from {len(m3u_repositories)} M3U repositories")
        if progress_callback:
            progress_callback(0, 100, "Loading M3U channels...")
        
        m3u_channels = self._load_m3u_channels(m3u_repositories)
        all_channels.extend(m3u_channels)
        
        logger.info(f"Loaded {len(m3u_channels)} channels from M3U sources")
        
        # Step 2: Load FMStream radio stations (optional)
        if self.enable_fmstream:
            if progress_callback:
                progress_callback(50, 100, "Loading FMStream radio stations...")
            
            try:
                fmstream_channels = fetch_fmstream_stations(
                    url=self.fmstream_url,
                    existing_channels=all_channels,  # Deduplicate against M3U
                    max_stations=self.fmstream_max_stations
                )
                
                all_channels.extend(fmstream_channels)
                logger.info(f"Loaded {len(fmstream_channels)} radio stations from FMStream")
                
            except Exception as e:
                logger.error(f"Error loading FMStream channels: {e}")
                # Continue with M3U channels only
        
        # Step 3: Final deduplication and sorting
        if progress_callback:
            progress_callback(90, 100, "Deduplicating channels...")
        
        unique_channels = self._deduplicate_channels(all_channels)
        
        if progress_callback:
            progress_callback(100, 100, "Complete!")
        
        logger.info(f"Total unique channels: {len(unique_channels)}")
        
        self.channels = unique_channels
        return unique_channels
    
    def _load_m3u_channels(self, repositories: List[str]) -> List[Dict[str, Any]]:
        """Load channels from M3U repositories.
        
        This is a placeholder - replace with actual M3U loading logic.
        
        Args:
            repositories: List of M3U repository URLs
            
        Returns:
            List of channel dictionaries
        """
        # TODO: Implement actual M3U loading
        # from utils.helpers import parse_m3u
        # channels = []
        # for repo_url in repositories:
        #     content = fetch_m3u(repo_url)
        #     channels.extend(parse_m3u(content))
        # return channels
        
        return []
    
    def _deduplicate_channels(self, channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate channels by URL.
        
        When duplicates are found, keeps the one with:
        1. Higher bitrate (for radio)
        2. Better resolution (for TV)
        3. More complete metadata
        
        Args:
            channels: List of channel dictionaries
            
        Returns:
            Deduplicated list of channels
        """
        url_to_channel = {}
        
        for channel in channels:
            url = channel.get('url', '').strip().lower()
            if not url:
                continue
            
            existing = url_to_channel.get(url)
            
            if existing is None:
                # First occurrence
                url_to_channel[url] = channel
            else:
                # Duplicate found - keep the better one
                if self._should_replace_channel(existing, channel):
                    url_to_channel[url] = channel
        
        return list(url_to_channel.values())
    
    def _should_replace_channel(
        self,
        existing: Dict[str, Any],
        new: Dict[str, Any]
    ) -> bool:
        """Determine if new channel should replace existing one.
        
        Args:
            existing: Existing channel
            new: New channel candidate
            
        Returns:
            True if new channel should replace existing
        """
        # For radio, prefer higher bitrate
        if existing.get('media_type') == 'Radio':
            existing_bitrate = existing.get('bitrate', 0)
            new_bitrate = new.get('bitrate', 0)
            
            if new_bitrate > existing_bitrate:
                return True
            elif new_bitrate < existing_bitrate:
                return False
        
        # For TV, prefer higher resolution
        # (resolution comparison logic would go here)
        
        # Compare metadata completeness
        existing_score = self._metadata_score(existing)
        new_score = self._metadata_score(new)
        
        return new_score > existing_score
    
    def _metadata_score(self, channel: Dict[str, Any]) -> int:
        """Calculate metadata completeness score.
        
        Args:
            channel: Channel dictionary
            
        Returns:
            Score (higher is better)
        """
        score = 0
        
        if channel.get('name') and channel['name'] != 'Unknown':
            score += 2
        if channel.get('category'):
            score += 1
        if channel.get('country'):
            score += 1
        if channel.get('language'):
            score += 1
        if channel.get('logo'):
            score += 1
        if channel.get('bitrate'):
            score += 1
        
        return score
    
    def get_radio_channels(self) -> List[Dict[str, Any]]:
        """Get all radio channels.
        
        Returns:
            List of radio channels
        """
        return [
            ch for ch in self.channels
            if ch.get('media_type') == 'Radio'
        ]
    
    def get_tv_channels(self) -> List[Dict[str, Any]]:
        """Get all TV channels.
        
        Returns:
            List of TV channels
        """
        return [
            ch for ch in self.channels
            if ch.get('media_type') == 'TV'
        ]
    
    def get_channels_by_country(self, country: str) -> List[Dict[str, Any]]:
        """Get channels from a specific country.
        
        Args:
            country: Country name or code
            
        Returns:
            List of channels from that country
        """
        return [
            ch for ch in self.channels
            if ch.get('country', '').lower() == country.lower()
        ]
    
    def get_channels_by_genre(self, genre: str) -> List[Dict[str, Any]]:
        """Get channels of a specific genre/category.
        
        Args:
            genre: Genre/category name
            
        Returns:
            List of channels in that genre
        """
        return [
            ch for ch in self.channels
            if ch.get('category', '').lower() == genre.lower()
        ]
    
    def search_channels(self, query: str) -> List[Dict[str, Any]]:
        """Search channels by name.
        
        Args:
            query: Search query
            
        Returns:
            List of matching channels
        """
        query_lower = query.lower()
        return [
            ch for ch in self.channels
            if query_lower in ch.get('name', '').lower()
        ]


def example_usage():
    """Example usage of ChannelManagerWithFMStream."""
    
    # Initialize manager with FMStream enabled
    manager = ChannelManagerWithFMStream(enable_fmstream=True)
    
    # M3U repositories
    repositories = [
        'https://iptv-org.github.io/iptv/index.m3u',
        'https://iptv-org.github.io/iptv/index.country.m3u',
    ]
    
    # Progress callback
    def on_progress(current, total, message):
        percent = (current / total) * 100
        print(f"[{percent:3.0f}%] {message}")
    
    # Load all channels
    print("Loading channels...")
    channels = manager.load_all_channels(
        m3u_repositories=repositories,
        progress_callback=on_progress
    )
    
    print(f"\nTotal channels loaded: {len(channels)}")
    
    # Get statistics
    radio_channels = manager.get_radio_channels()
    tv_channels = manager.get_tv_channels()
    
    print(f"Radio channels: {len(radio_channels)}")
    print(f"TV channels: {len(tv_channels)}")
    
    # Search examples
    bbc_channels = manager.search_channels('BBC')
    print(f"\nBBC channels: {len(bbc_channels)}")
    for ch in bbc_channels[:5]:
        print(f"  - {ch['name']} ({ch.get('media_type', 'Unknown')})")
    
    # Filter by country
    uk_channels = manager.get_channels_by_country('UK')
    print(f"\nUK channels: {len(uk_channels)}")
    
    # Filter by genre
    music_channels = manager.get_channels_by_genre('Music')
    print(f"Music channels: {len(music_channels)}")


if __name__ == '__main__':
    example_usage()

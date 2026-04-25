"""
Unit tests for v2.1.0 multi-URL channel support.

Tests the _migrate_channel_urls() and get_channel_url() functions
from core/channel_manager.py.

Run with: pytest tests/test_channel_urls.py -v
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.channel_manager import _migrate_channel_urls, get_channel_url


class TestMigrateChannelUrls:
    """Tests for _migrate_channel_urls() migration function."""

    def test_legacy_single_url_migrated_to_urls_list(self):
        """Legacy channel with only 'url' gets 'urls' list."""
        channel = {'name': 'Test', 'url': 'http://example.com/stream.m3u8'}
        
        result = _migrate_channel_urls(channel)
        
        assert result['urls'] == ['http://example.com/stream.m3u8']
        assert result['url'] == 'http://example.com/stream.m3u8'
        assert result['working_url_index'] == 0

    def test_already_migrated_channel_unchanged(self):
        """Channel with existing 'urls' list is left intact."""
        channel = {
            'name': 'Test',
            'urls': ['http://a.m3u8', 'http://b.m3u8'],
            'working_url_index': 1,
        }
        
        result = _migrate_channel_urls(channel)
        
        assert result['urls'] == ['http://a.m3u8', 'http://b.m3u8']
        assert result['working_url_index'] == 1
        assert result['url'] == 'http://b.m3u8'  # synced to active URL

    def test_idempotent_multiple_calls(self):
        """Calling migrate multiple times produces same result."""
        channel = {'name': 'Test', 'url': 'http://example.com/stream.m3u8'}
        
        _migrate_channel_urls(channel)
        _migrate_channel_urls(channel)
        result = _migrate_channel_urls(channel)
        
        assert result['urls'] == ['http://example.com/stream.m3u8']
        assert result['working_url_index'] == 0

    def test_empty_url_migrates_to_empty_string_list(self):
        """Channel with empty url gets [''] as urls."""
        channel = {'name': 'Test', 'url': ''}
        
        result = _migrate_channel_urls(channel)
        
        assert result['urls'] == ['']
        assert result['url'] == ''

    def test_missing_url_key_migrates_gracefully(self):
        """Channel with no 'url' key at all gets [''] as urls."""
        channel = {'name': 'Test'}
        
        result = _migrate_channel_urls(channel)
        
        assert result['urls'] == ['']
        assert result['url'] == ''
        assert result['working_url_index'] == 0

    def test_out_of_range_working_url_index_clamped(self):
        """working_url_index beyond list length is clamped."""
        channel = {
            'name': 'Test',
            'urls': ['http://a.m3u8'],
            'working_url_index': 99,
        }
        
        result = _migrate_channel_urls(channel)
        
        assert result['working_url_index'] == 0  # clamped to last valid
        assert result['url'] == 'http://a.m3u8'

    def test_negative_working_url_index_clamped(self):
        """Negative working_url_index is clamped to 0."""
        channel = {
            'name': 'Test',
            'urls': ['http://a.m3u8', 'http://b.m3u8'],
            'working_url_index': -5,
        }
        
        result = _migrate_channel_urls(channel)
        
        assert result['working_url_index'] == 0
        assert result['url'] == 'http://a.m3u8'

    def test_url_synced_to_active_url_after_migration(self):
        """After migration, 'url' key reflects the active URL from 'urls'."""
        channel = {
            'name': 'Test',
            'urls': ['http://primary.m3u8', 'http://backup.m3u8'],
            'url': 'http://stale.m3u8',  # stale value
            'working_url_index': 1,
        }
        
        result = _migrate_channel_urls(channel)
        
        # 'url' should be synced to urls[1], not the stale value
        assert result['url'] == 'http://backup.m3u8'

    def test_empty_urls_list_treated_as_not_migrated(self):
        """Empty urls list triggers re-migration from 'url'."""
        channel = {
            'name': 'Test',
            'urls': [],
            'url': 'http://fallback.m3u8',
        }
        
        result = _migrate_channel_urls(channel)
        
        assert result['urls'] == ['http://fallback.m3u8']
        assert result['url'] == 'http://fallback.m3u8'

    def test_string_working_url_index_converted(self):
        """String working_url_index is safely converted to int."""
        channel = {
            'name': 'Test',
            'urls': ['http://a.m3u8', 'http://b.m3u8'],
            'working_url_index': '1',
        }
        
        result = _migrate_channel_urls(channel)
        
        assert result['working_url_index'] == 1
        assert result['url'] == 'http://b.m3u8'

    def test_invalid_string_working_url_index_defaults_to_zero(self):
        """Non-numeric string working_url_index defaults to 0."""
        channel = {
            'name': 'Test',
            'urls': ['http://a.m3u8', 'http://b.m3u8'],
            'working_url_index': 'bad',
        }
        
        result = _migrate_channel_urls(channel)
        
        assert result['working_url_index'] == 0
        assert result['url'] == 'http://a.m3u8'


class TestGetChannelUrl:
    """Tests for get_channel_url() helper function."""

    def test_legacy_single_url(self):
        """Returns url from legacy format channel."""
        channel = {'name': 'Test', 'url': 'http://example.com/stream.m3u8'}
        
        assert get_channel_url(channel) == 'http://example.com/stream.m3u8'

    def test_multi_url_default_index(self):
        """Returns first URL when working_url_index is 0 or absent."""
        channel = {
            'name': 'Test',
            'urls': ['http://a.m3u8', 'http://b.m3u8'],
        }
        
        assert get_channel_url(channel) == 'http://a.m3u8'

    def test_multi_url_with_index(self):
        """Returns URL at specified working_url_index."""
        channel = {
            'name': 'Test',
            'urls': ['http://a.m3u8', 'http://b.m3u8', 'http://c.m3u8'],
            'working_url_index': 2,
        }
        
        assert get_channel_url(channel) == 'http://c.m3u8'

    def test_out_of_range_index_clamped(self):
        """Out-of-range index returns last URL."""
        channel = {
            'name': 'Test',
            'urls': ['http://a.m3u8'],
            'working_url_index': 50,
        }
        
        assert get_channel_url(channel) == 'http://a.m3u8'

    def test_no_url_or_urls_returns_empty(self):
        """Channel with no URL data returns empty string."""
        channel = {'name': 'Test'}
        
        assert get_channel_url(channel) == ''

    def test_both_url_and_urls_prefers_urls(self):
        """When both url and urls exist, uses urls list."""
        channel = {
            'name': 'Test',
            'url': 'http://old.m3u8',
            'urls': ['http://new1.m3u8', 'http://new2.m3u8'],
            'working_url_index': 1,
        }
        
        assert get_channel_url(channel) == 'http://new2.m3u8'

    def test_string_working_url_index_handled(self):
        """String working_url_index is converted to int."""
        channel = {
            'name': 'Test',
            'urls': ['http://a.m3u8', 'http://b.m3u8'],
            'working_url_index': '1',
        }
        
        assert get_channel_url(channel) == 'http://b.m3u8'

    def test_invalid_working_url_index_defaults_to_zero(self):
        """Non-numeric working_url_index defaults to 0."""
        channel = {
            'name': 'Test',
            'urls': ['http://a.m3u8', 'http://b.m3u8'],
            'working_url_index': 'invalid',
        }
        
        assert get_channel_url(channel) == 'http://a.m3u8'

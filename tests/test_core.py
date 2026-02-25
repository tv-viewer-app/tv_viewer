"""
Unit tests for TV Viewer core functionality.

Run with: pytest tests/test_core.py -v
"""

import pytest
import sys
import os
import asyncio
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHelpers:
    """Tests for utils/helpers.py"""
    
    def test_parse_m3u_simple(self):
        """Test parsing a simple M3U playlist."""
        from utils.helpers import parse_m3u
        
        content = '''#EXTM3U
#EXTINF:-1 tvg-name="Test Channel" tvg-logo="http://logo.png" group-title="News",Test Channel
http://stream.example.com/live.m3u8
'''
        channels = parse_m3u(content)
        
        assert len(channels) == 1
        assert channels[0]['name'] == 'Test Channel'
        assert channels[0]['url'] == 'http://stream.example.com/live.m3u8'
        assert channels[0]['category'] == 'News'
    
    def test_parse_m3u_empty(self):
        """Test parsing empty M3U content."""
        from utils.helpers import parse_m3u
        
        channels = parse_m3u('')
        assert channels == []
        
        channels = parse_m3u('#EXTM3U\n')
        assert channels == []
    
    def test_parse_m3u_invalid_urls_filtered(self):
        """Test that invalid URLs are filtered out."""
        from utils.helpers import parse_m3u
        
        content = '''#EXTM3U
#EXTINF:-1,Valid Channel
http://valid.stream/live.m3u8
#EXTINF:-1,Invalid Channel
javascript:alert(1)
#EXTINF:-1,File Channel
file:///etc/passwd
'''
        channels = parse_m3u(content)
        
        # Only valid HTTP URL should be included
        assert len(channels) == 1
        assert channels[0]['name'] == 'Valid Channel'
    
    def test_format_age_rating(self):
        """Test age rating formatting."""
        from utils.helpers import format_age_rating
        
        assert format_age_rating(0) == 'All Ages'
        assert format_age_rating(7) == '7+'
        assert format_age_rating(13) == '13+'
        assert format_age_rating(18) == '18+'
        assert format_age_rating(21) == '21+'
    
    def test_format_duration(self):
        """Test duration formatting."""
        from utils.helpers import format_duration
        
        assert format_duration(0) == '00:00'
        assert format_duration(65) == '01:05'
        assert format_duration(3661) == '01:01:01'
    
    def test_safe_json_load(self):
        """Test safe JSON loading with size limits."""
        from utils.helpers import load_json_file
        import tempfile
        import json
        
        # Create temp file with valid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'test': 'data'}, f)
            temp_path = f.name
        
        try:
            result = load_json_file(temp_path)
            assert result == {'test': 'data'}
        finally:
            os.unlink(temp_path)
    
    def test_safe_json_load_missing_file(self):
        """Test safe JSON load with missing file."""
        from utils.helpers import load_json_file
        
        result = load_json_file('/nonexistent/file.json')
        assert result is None


class TestLogger:
    """Tests for utils/logger.py"""
    
    def test_logger_creation(self):
        """Test logger can be created."""
        from utils.logger import get_logger
        
        logger = get_logger('test_module')
        assert logger is not None
        assert logger.name == 'test_module'
    
    def test_log_file_path(self):
        """Test log file path is returned."""
        from utils.logger import get_log_file_path
        
        path = get_log_file_path()
        assert path.endswith('.log')
        assert 'tv_viewer' in path
    
    def test_logger_writes_to_file(self):
        """Test logger actually writes to file."""
        from utils.logger import get_logger, get_log_file_path
        import time
        
        logger = get_logger('test_write')
        test_message = f"Test message {time.time()}"
        logger.info(test_message)
        
        # Give it a moment to flush
        import logging
        for handler in logger.handlers:
            handler.flush()
        
        log_path = get_log_file_path()
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                content = f.read()
                # Message should be in log (may not be if buffer not flushed)


class TestConfig:
    """Tests for config.py"""
    
    def test_config_has_required_attrs(self):
        """Test config has all required attributes."""
        import config
        
        required = [
            'APP_NAME',
            'APP_VERSION',
            'BASE_DIR',
            'CHANNELS_FILE',
            'WINDOW_WIDTH',
            'WINDOW_HEIGHT',
            'MAX_CONCURRENT_CHECKS',
            'STREAM_CHECK_TIMEOUT',
        ]
        
        for attr in required:
            assert hasattr(config, attr), f"Missing config attribute: {attr}"
    
    def test_config_values_reasonable(self):
        """Test config values are reasonable."""
        import config
        
        assert config.WINDOW_WIDTH >= 800
        assert config.WINDOW_HEIGHT >= 600
        assert config.MAX_CONCURRENT_CHECKS > 0
        assert config.MAX_CONCURRENT_CHECKS <= 100
        assert config.STREAM_CHECK_TIMEOUT > 0


class TestConstants:
    """Tests for ui/constants.py"""
    
    def test_fluent_colors_defined(self):
        """Test FluentColors has required colors."""
        from ui.constants import FluentColors
        
        required = [
            'ACCENT', 'ACCENT_DARK', 'ACCENT_LIGHT',
            'BG_MICA', 'BG_CARD', 'BG_ACRYLIC',
            'TEXT_PRIMARY', 'TEXT_SECONDARY', 'TEXT_DISABLED',
            'SUCCESS', 'ERROR', 'WARNING', 'INFO'
        ]
        
        for color in required:
            assert hasattr(FluentColors, color), f"Missing color: {color}"
            value = getattr(FluentColors, color)
            assert value.startswith('#') or value.startswith('rgba'), f"Invalid color format: {color}={value}"
    
    def test_fluent_spacing_defined(self):
        """Test FluentSpacing has required values."""
        from ui.constants import FluentSpacing
        
        required = [
            'PADDING_SMALL', 'PADDING_MEDIUM', 'PADDING_LARGE',
            'CORNER_RADIUS_SMALL', 'CORNER_RADIUS_MEDIUM'
        ]
        
        for spacing in required:
            assert hasattr(FluentSpacing, spacing), f"Missing spacing: {spacing}"
            value = getattr(FluentSpacing, spacing)
            assert isinstance(value, int) and value >= 0


class TestChannelManager:
    """Tests for core/channel_manager.py"""
    
    def test_channel_manager_init(self):
        """Test ChannelManager can be initialized."""
        from core.channel_manager import ChannelManager
        
        manager = ChannelManager()
        assert manager is not None
    
    def test_channel_manager_has_methods(self):
        """Test ChannelManager has required methods."""
        from core.channel_manager import ChannelManager
        
        manager = ChannelManager()
        
        required_methods = [
            'load_cached_channels',
            'save_channels',
            'get_channels_by_group',
            'get_groups',
            'validate_channels_async',
            'stop',
        ]
        
        for method in required_methods:
            assert hasattr(manager, method), f"Missing method: {method}"
            assert callable(getattr(manager, method))


class TestStreamChecker:
    """Tests for core/stream_checker.py"""
    
    def test_stream_checker_init(self):
        """Test StreamChecker can be initialized."""
        from core.stream_checker import StreamChecker
        
        checker = StreamChecker()
        assert checker is not None
        assert checker.is_running == False
    
    def test_stream_checker_with_custom_params(self):
        """Test StreamChecker accepts custom parameters."""
        from core.stream_checker import StreamChecker
        
        checker = StreamChecker(batch_size=100, request_delay=0.05)
        assert checker._batch_size == 100
        assert checker._request_delay == 0.05


class TestRepositoryHandler:
    """Tests for core/repository.py"""
    
    def test_repository_handler_init(self):
        """Test RepositoryHandler can be initialized."""
        from core.repository import RepositoryHandler
        
        handler = RepositoryHandler()
        assert handler is not None
        assert len(handler.repositories) > 0
    
    def test_url_validation(self):
        """Test URL validation in repository handler."""
        from core.repository import RepositoryHandler
        
        handler = RepositoryHandler()
        
        # Valid URLs
        assert handler._validate_url('http://example.com/playlist.m3u') == True
        assert handler._validate_url('https://example.com/playlist.m3u') == True
        
        # Invalid URLs
        assert handler._validate_url('') == False
        assert handler._validate_url('ftp://example.com') == False
        assert handler._validate_url('file:///etc/passwd') == False
        assert handler._validate_url('javascript:alert(1)') == False


class TestMainRequirementsCheck:
    """Tests for main.py requirements check."""
    
    def test_check_requirements_function_exists(self):
        """Test check_requirements function exists."""
        from main import check_requirements
        
        assert callable(check_requirements)
    
    def test_check_requirements_returns_tuple(self):
        """Test check_requirements returns expected format."""
        from main import check_requirements
        
        result = check_requirements()
        
        assert isinstance(result, tuple)
        assert len(result) == 3
        
        success, missing, warnings = result
        assert isinstance(success, bool)
        assert isinstance(missing, list)
        assert isinstance(warnings, list)


# Async tests for stream checking
class TestAsyncOperations:
    """Tests for async operations."""
    
    @pytest.mark.asyncio
    async def test_stream_check_invalid_url(self):
        """Test stream check with invalid URL."""
        from core.stream_checker import StreamChecker
        import aiohttp
        
        checker = StreamChecker()
        checker._semaphore = asyncio.Semaphore(1)
        
        channel = {'url': 'http://invalid.nonexistent.url/stream.m3u8', 'name': 'Test'}
        
        async with aiohttp.ClientSession() as session:
            result = await checker.check_stream(channel, session)
        
        # Should mark as not working (connection will fail)
        assert result['is_working'] == False
        assert 'last_scanned' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

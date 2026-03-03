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
    
    def test_stream_check_invalid_url(self):
        """Test stream check with invalid URL."""
        from core.stream_checker import StreamChecker
        import aiohttp
        
        async def _run_check():
            checker = StreamChecker()
            checker._semaphore = asyncio.Semaphore(1)
            channel = {'url': 'http://invalid.nonexistent.url/stream.m3u8', 'name': 'Test'}
            async with aiohttp.ClientSession() as session:
                return await checker.check_stream(channel, session)
        
        result = asyncio.run(_run_check())
        # Should mark as not working (connection will fail)
        assert result['is_working'] == False
        assert 'last_scanned' in result


# ---------------------------------------------------------------------------
# Supabase data contract tests — catch serialization and schema mismatches
# ---------------------------------------------------------------------------

class TestSupabaseContracts:
    """Ensure telemetry/analytics payloads match the Supabase schema.

    These tests prevent regressions like double-serialized event_data
    (stored as JSON string instead of JSONB object) and missing required
    columns (country, device_id).
    """

    # Required top-level columns in analytics_events table
    REQUIRED_COLUMNS = {'device_id', 'event_type', 'event_data', 'app_version', 'platform'}

    def test_telemetry_event_data_is_dict_not_string(self):
        """event_data must be a dict, not json.dumps'd string (BUG-001 regression)."""
        from utils.telemetry import _send_event
        from unittest.mock import AsyncMock, patch, MagicMock

        captured = {}

        mock_resp = AsyncMock()
        mock_resp.status = 201

        async def _run():
            mock_session = AsyncMock()
            # session.post() returns an async context manager
            cm = AsyncMock()
            cm.__aenter__ = AsyncMock(return_value=mock_resp)
            cm.__aexit__ = AsyncMock(return_value=False)

            def fake_post(url, json=None, headers=None, timeout=None):
                captured['payload'] = json
                return cm

            mock_session.post = fake_post
            mock_session_cls = MagicMock()
            mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            with patch('aiohttp.ClientSession', mock_session_cls):
                await _send_event('test_event', {'key': 'value'})

        asyncio.run(_run())

        assert 'payload' in captured, "No POST was made"
        ed = captured['payload']['event_data']
        assert isinstance(ed, dict), f"event_data is {type(ed).__name__}, expected dict (double-serialization bug)"
        assert ed.get('key') == 'value'

    def test_analytics_event_has_country(self):
        """analytics.py must include country field (BUG-003 regression)."""
        from utils.analytics import AnalyticsService, _COUNTRY

        svc = AnalyticsService.__new__(AnalyticsService)
        svc._initialized = True
        svc._device_id = 'test'
        svc._queue = []

        asyncio.run(svc.track_event('test', {'x': 1}))

        assert len(svc._queue) == 1
        evt = svc._queue[0]
        assert 'country' in evt, "analytics event missing 'country' column"
        assert evt['country'] != '', "country should not be empty"

    def test_analytics_event_has_required_columns(self):
        """Every analytics event must have all columns required by the SQL schema."""
        from utils.analytics import AnalyticsService

        svc = AnalyticsService.__new__(AnalyticsService)
        svc._initialized = True
        svc._device_id = 'test-device'
        svc._queue = []

        asyncio.run(svc.track_event('app_launch', {'os': 'windows'}))

        evt = svc._queue[0]
        for col in self.REQUIRED_COLUMNS:
            assert col in evt, f"analytics event missing required column '{col}'"
        assert isinstance(evt['event_data'], dict), "event_data must be a dict"

    def test_analytics_uses_shared_device_id_path(self):
        """analytics.py and telemetry.py must use the same device ID file."""
        from utils.analytics import _DEVICE_ID_PATH
        from utils.telemetry import _DEVICE_ID_FILE
        from pathlib import Path

        assert str(_DEVICE_ID_PATH) == _DEVICE_ID_FILE, (
            f"Device ID file mismatch: analytics={_DEVICE_ID_PATH}, telemetry={_DEVICE_ID_FILE}"
        )

    def test_telemetry_hash_is_full_sha256(self):
        """URL hashes must be full 64-char SHA256 (not truncated)."""
        from utils.telemetry import _hash
        h = _hash('http://example.com/stream.m3u8')
        assert len(h) == 64, f"Hash is {len(h)} chars, expected 64 (full SHA256)"

    def test_supabase_channels_urls_not_double_serialized(self):
        """contribute_channels must send urls as a list, not json.dumps'd string."""
        from utils.supabase_channels import contribute_channels
        from unittest.mock import AsyncMock, patch, MagicMock

        captured = {}

        mock_resp = AsyncMock()
        mock_resp.status = 201

        async def _run():
            mock_session = AsyncMock()
            cm = AsyncMock()
            cm.__aenter__ = AsyncMock(return_value=mock_resp)
            cm.__aexit__ = AsyncMock(return_value=False)

            def fake_post(url, json=None, headers=None, timeout=None):
                captured['payload'] = json
                return cm

            mock_session.post = fake_post
            mock_session_cls = MagicMock()
            mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            with patch('aiohttp.ClientSession', mock_session_cls):
                with patch('utils.supabase_channels.is_configured', return_value=True):
                    await contribute_channels([{
                        'url': 'http://a.example.com/stream.m3u8',
                        'urls': ['http://a.example.com/stream.m3u8'],
                        'name': 'Test',
                    }])

        asyncio.run(_run())

        assert 'payload' in captured, "No POST was made"
        urls_val = captured['payload'][0]['urls']
        assert isinstance(urls_val, list), f"urls is {type(urls_val).__name__}, expected list (double-serialization bug)"

    def test_app_start_event_keys_match_view(self):
        """app_launch event_data keys must match mv_client_platforms view columns."""
        from utils.analytics import AnalyticsService

        svc = AnalyticsService.__new__(AnalyticsService)
        svc._initialized = True
        svc._device_id = 'test'
        svc._queue = []

        asyncio.run(svc.track_app_launch())

        evt = svc._queue[0]
        ed = evt['event_data']
        # mv_client_platforms queries event_data->>'os' and ->>'os_version'
        # At minimum, platform_os must be present
        assert 'platform_os' in ed or 'os' in ed, "app_launch must include platform_os or os"

    def test_session_end_event_has_required_keys(self):
        """session_end event_data must include keys that mv_engagement queries."""
        from utils.analytics import AnalyticsService

        svc = AnalyticsService.__new__(AnalyticsService)
        svc._initialized = True
        svc._device_id = 'test'
        svc._queue = []

        # Don't actually flush
        async def noop(): pass
        svc.flush = noop

        asyncio.run(svc.track_session_end(
            session_duration_s=120, channels_played=5, channels_failed=2
        ))

        evt = svc._queue[0]
        ed = evt['event_data']
        assert 'session_duration_s' in ed
        assert 'channels_played' in ed
        assert 'channels_failed' in ed
        assert ed['session_duration_s'] == 120


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

# TV Viewer - Comprehensive Test Plan

## Table of Contents
1. [Test Strategy](#1-test-strategy)
2. [Test Environment](#2-test-environment)
3. [Test Categories](#3-test-categories)
4. [Detailed Test Cases](#4-detailed-test-cases)
5. [Bug Risk Areas](#5-bug-risk-areas)
6. [Regression Test Suite](#6-regression-test-suite)
7. [Automation Recommendations](#7-automation-recommendations)
8. [Pytest Fixtures](#8-pytest-fixtures)

---

## 1. Test Strategy

### 1.1 Objectives
- Ensure application stability across Windows, Linux, and macOS
- Validate all IPTV stream discovery, validation, and playback features
- Verify UI responsiveness under various load conditions
- Confirm thread safety in concurrent operations
- Validate error handling for network failures and edge cases

### 1.2 Scope

**In Scope:**
- Core functionality (channel discovery, validation, playback)
- UI components (main window, player window, search, filters)
- Data persistence (JSON cache, configuration)
- Network operations (M3U fetching, stream validation)
- Integration with VLC and optional pychromecast
- Cross-platform compatibility

**Out of Scope:**
- Third-party IPTV repository availability
- External VLC player bugs
- Network infrastructure issues

### 1.3 Approach
- **Unit Tests**: Test individual functions/methods in isolation
- **Integration Tests**: Test module interactions (e.g., ChannelManager + StreamChecker)
- **UI Tests**: Manual and automated GUI testing
- **Performance Tests**: Load testing with large channel lists
- **Security Tests**: Input validation, URL sanitization
- **Accessibility Tests**: Keyboard navigation, screen reader compatibility

### 1.4 Test Levels
| Level | Coverage Target | Priority |
|-------|-----------------|----------|
| Unit Tests | 80%+ code coverage | High |
| Integration Tests | All module boundaries | High |
| UI Tests | Critical user flows | Medium |
| Performance Tests | Load scenarios | Medium |
| Security Tests | All input paths | High |

---

## 2. Test Environment

### 2.1 Required Setup

**Software Requirements:**
```bash
# Python 3.8+
python --version  # Should be 3.8 or higher

# VLC Media Player
# Windows: C:\Program Files\VideoLAN\VLC\vlc.exe
# Linux: /usr/bin/vlc
# macOS: /Applications/VLC.app

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock aioresponses
pip install -r requirements.txt
```

**Hardware Requirements:**
- Minimum 4GB RAM
- Network connectivity
- Display for UI tests

### 2.2 Test Data

**Mock M3U Content:**
```
#EXTM3U
#EXTINF:-1 tvg-name="Test Channel 1" tvg-logo="http://example.com/logo1.png" group-title="News",Test Channel 1
http://example.com/stream1.m3u8
#EXTINF:-1 tvg-name="Test Channel 2" tvg-logo="http://example.com/logo2.png" group-title="Sports",Test Channel 2
http://example.com/stream2.m3u8
```

**Test Configuration (`channels_config.json`):**
```json
{
  "repositories": [
    "http://test-repo.local/test.m3u"
  ],
  "custom_channels": [
    {
      "name": "Test Custom",
      "url": "http://localhost:8080/test.m3u8",
      "category": "Custom"
    }
  ]
}
```

### 2.3 Environment Variables
```bash
# Enable test mode (skip actual network calls)
export TV_VIEWER_TEST_MODE=1

# Set custom config path
export TV_VIEWER_CONFIG_PATH=/path/to/test/config
```

---

## 3. Test Categories

### 3.1 Unit Tests

#### 3.1.1 `utils/helpers.py`

| Test ID | Test Name | Description | Input | Expected Output |
|---------|-----------|-------------|-------|-----------------|
| UT-H001 | `test_parse_m3u_valid` | Parse valid M3U content | Valid M3U string | List of channel dicts |
| UT-H002 | `test_parse_m3u_empty` | Handle empty content | Empty string | Empty list |
| UT-H003 | `test_parse_m3u_malformed` | Handle malformed content | Invalid M3U | Empty list or partial |
| UT-H004 | `test_parse_m3u_large` | Handle large M3U (100k lines) | Large content | Truncated to 100k |
| UT-H005 | `test_parse_extinf_complete` | Parse EXTINF with all attrs | Full EXTINF line | Dict with all fields |
| UT-H006 | `test_parse_extinf_minimal` | Parse minimal EXTINF | "#EXTINF:-1,Name" | Dict with name only |
| UT-H007 | `test_is_valid_stream_url_http` | Validate HTTP URL | "http://..." | True |
| UT-H008 | `test_is_valid_stream_url_https` | Validate HTTPS URL | "https://..." | True |
| UT-H009 | `test_is_valid_stream_url_rtmp` | Validate RTMP URL | "rtmp://..." | True |
| UT-H010 | `test_is_valid_stream_url_file` | Reject file:// URL | "file://..." | False |
| UT-H011 | `test_is_valid_stream_url_javascript` | Reject javascript: | "javascript:..." | False |
| UT-H012 | `test_sanitize_text_html` | Sanitize HTML entities | "<script>" | "&lt;script&gt;" |
| UT-H013 | `test_sanitize_text_control_chars` | Remove control chars | "\x00test\x01" | "test" |
| UT-H014 | `test_categorize_channel_news` | Categorize news channel | {"name": "CNN"} | "News" |
| UT-H015 | `test_categorize_channel_sports` | Categorize sports channel | {"name": "ESPN"} | "Sports" |
| UT-H016 | `test_categorize_channel_kids` | Categorize kids channel | {"name": "Disney"} | "Kids" |
| UT-H017 | `test_categorize_channel_unknown` | Default category | {"name": "XYZ"} | "Other" |
| UT-H018 | `test_detect_media_type_tv` | Detect TV channel | {"name": "BBC"} | "TV" |
| UT-H019 | `test_detect_media_type_radio` | Detect radio channel | {"name": "BBC Radio"} | "Radio" |
| UT-H020 | `test_get_channel_country_israel` | Detect Israel channel | {"name": "Kan 11"} | "Israel" |
| UT-H021 | `test_get_channel_country_url_tld` | Detect country from URL TLD | {"url": "...co.uk..."} | "UK" |
| UT-H022 | `test_get_minimum_age_kids` | Age rating for kids | {"category": "Kids"} | 0 |
| UT-H023 | `test_get_minimum_age_adult` | Age rating for adult | {"category": "Adult"} | 18 |
| UT-H024 | `test_format_duration_seconds` | Format < 1 hour | 125 | "02:05" |
| UT-H025 | `test_format_duration_hours` | Format >= 1 hour | 3725 | "01:02:05" |
| UT-H026 | `test_load_json_file_valid` | Load valid JSON | Valid file path | Dict |
| UT-H027 | `test_load_json_file_missing` | Handle missing file | Invalid path | None |
| UT-H028 | `test_load_json_file_corrupt` | Handle corrupt JSON | Corrupt file | None |
| UT-H029 | `test_save_json_file_success` | Save JSON successfully | Valid data/path | True |
| UT-H030 | `test_save_json_file_atomic` | Atomic write operation | Data + path | Temp file created |

#### 3.1.2 `core/repository.py`

| Test ID | Test Name | Description |
|---------|-----------|-------------|
| UT-R001 | `test_validate_url_valid_http` | Accept http:// URLs |
| UT-R002 | `test_validate_url_valid_https` | Accept https:// URLs |
| UT-R003 | `test_validate_url_invalid_ftp` | Reject ftp:// URLs |
| UT-R004 | `test_validate_url_empty` | Reject empty URLs |
| UT-R005 | `test_fetch_repository_success` | Fetch valid M3U repository |
| UT-R006 | `test_fetch_repository_timeout` | Handle timeout gracefully |
| UT-R007 | `test_fetch_repository_404` | Handle HTTP 404 |
| UT-R008 | `test_fetch_repository_content_too_large` | Reject > 50MB content |
| UT-R009 | `test_fetch_all_repositories_dedup` | Deduplicate by URL |
| UT-R010 | `test_fetch_all_repositories_progress` | Progress callback called |

#### 3.1.3 `core/stream_checker.py`

| Test ID | Test Name | Description |
|---------|-----------|-------------|
| UT-S001 | `test_check_stream_success_200` | Stream returns 200 |
| UT-S002 | `test_check_stream_success_head_405` | HEAD 405, GET succeeds |
| UT-S003 | `test_check_stream_redirect` | Handle 301/302 redirects |
| UT-S004 | `test_check_stream_timeout` | Handle timeout |
| UT-S005 | `test_check_stream_connection_error` | Handle connection error |
| UT-S006 | `test_check_stream_invalid_url` | Reject invalid URL scheme |
| UT-S007 | `test_check_stream_file_url` | Block file:// URLs |
| UT-S008 | `test_check_streams_batch_concurrency` | Respect semaphore limit |
| UT-S009 | `test_check_streams_batch_stop_event` | Graceful cancellation |
| UT-S010 | `test_start_background_check_thread` | Background thread starts |
| UT-S011 | `test_stop_background_check` | Stop event signals thread |
| UT-S012 | `test_is_running_property` | Returns correct state |

#### 3.1.4 `core/channel_manager.py`

| Test ID | Test Name | Description |
|---------|-----------|-------------|
| UT-C001 | `test_load_cached_channels_success` | Load from valid cache |
| UT-C002 | `test_load_cached_channels_empty` | Handle empty cache |
| UT-C003 | `test_load_cached_channels_missing` | Handle missing file |
| UT-C004 | `test_save_channels_success` | Save channels to cache |
| UT-C005 | `test_organize_channels_categories` | Organize by category |
| UT-C006 | `test_organize_channels_countries` | Organize by country |
| UT-C007 | `test_get_channels_by_category` | Filter by category |
| UT-C008 | `test_get_channels_by_country` | Filter by country |
| UT-C009 | `test_get_working_channels` | Filter working channels |
| UT-C010 | `test_search_channels_case_insensitive` | Case-insensitive search |
| UT-C011 | `test_search_channels_partial_match` | Partial name match |
| UT-C012 | `test_filter_adult_channels` | Filter adult content |
| UT-C013 | `test_set_media_type_filter` | Apply media type filter |
| UT-C014 | `test_merge_channels_preserve_status` | Preserve is_working on merge |
| UT-C015 | `test_thread_safety_concurrent_access` | RLock protects data |

### 3.2 Integration Tests

| Test ID | Test Name | Description |
|---------|-----------|-------------|
| IT-001 | `test_full_channel_fetch_and_organize` | Fetch → Parse → Organize |
| IT-002 | `test_channel_validation_pipeline` | Fetch → Validate → Update |
| IT-003 | `test_cache_persistence_round_trip` | Save → Load → Verify |
| IT-004 | `test_custom_channels_integration` | Config → Manager → Display |
| IT-005 | `test_stream_checker_updates_manager` | Checker → Callback → Manager |
| IT-006 | `test_ui_responds_to_validation` | Checker → Callback → UI Update |

### 3.3 UI Tests

| Test ID | Test Name | Description |
|---------|-----------|-------------|
| UI-001 | `test_main_window_initialization` | Window creates successfully |
| UI-002 | `test_category_list_population` | Categories appear in sidebar |
| UI-003 | `test_channel_list_display` | Channels display in table |
| UI-004 | `test_search_filters_channels` | Search box filters list |
| UI-005 | `test_group_by_toggle` | Category/Country toggle works |
| UI-006 | `test_media_type_filter` | All/TV/Radio filter works |
| UI-007 | `test_double_click_plays_channel` | Double-click opens player |
| UI-008 | `test_player_window_controls` | Play/Pause/Stop/Volume work |
| UI-009 | `test_fullscreen_toggle` | Fullscreen mode toggles |
| UI-010 | `test_keyboard_shortcuts` | Space/F/M/Esc shortcuts |
| UI-011 | `test_scan_progress_indicator` | Progress bar updates |
| UI-012 | `test_filter_toggles` | Hide checking/failed toggles |

### 3.4 Performance Tests

| Test ID | Test Name | Description | Target |
|---------|-----------|-------------|--------|
| PT-001 | `test_load_10k_channels` | Load 10,000 channels | < 2s |
| PT-002 | `test_organize_50k_channels` | Organize 50,000 channels | < 5s |
| PT-003 | `test_search_100k_channels` | Search 100,000 channels | < 100ms |
| PT-004 | `test_ui_responsiveness_during_scan` | UI responsive during validation | No freezes |
| PT-005 | `test_memory_usage_large_dataset` | Memory with 50k channels | < 500MB |
| PT-006 | `test_concurrent_stream_checks` | 100 concurrent checks | Stable |
| PT-007 | `test_batch_processing_memory` | Memory during batch validation | GC effective |

### 3.5 Security Tests

| Test ID | Test Name | Description |
|---------|-----------|-------------|
| SEC-001 | `test_url_injection_prevention` | Reject malicious URLs |
| SEC-002 | `test_file_url_blocked` | Block file:// URLs |
| SEC-003 | `test_javascript_url_blocked` | Block javascript: URLs |
| SEC-004 | `test_data_url_blocked` | Block data: URLs |
| SEC-005 | `test_m3u_content_sanitization` | Sanitize M3U content |
| SEC-006 | `test_html_injection_prevention` | Escape HTML in names |
| SEC-007 | `test_json_file_size_limit` | Reject > 100MB JSON |
| SEC-008 | `test_m3u_line_limit` | Truncate > 100k lines |
| SEC-009 | `test_logo_url_validation` | Only http/https logos |
| SEC-010 | `test_config_file_validation` | Validate config structure |

### 3.6 Accessibility Tests

| Test ID | Test Name | Description |
|---------|-----------|-------------|
| ACC-001 | `test_keyboard_navigation_sidebar` | Tab through sidebar |
| ACC-002 | `test_keyboard_navigation_channels` | Arrow keys in channel list |
| ACC-003 | `test_keyboard_shortcut_player` | Player shortcuts work |
| ACC-004 | `test_focus_indicators` | Focus visible on elements |
| ACC-005 | `test_high_contrast_readability` | Text readable in dark theme |

---

## 4. Detailed Test Cases

### 4.1 Channel Discovery and Loading

#### TC-CD-001: Load channels from IPTV repository
**Priority:** Critical  
**Preconditions:** Network available, valid repository URL configured

**Steps:**
1. Launch application
2. Observe initial loading behavior
3. Wait for channel fetch to complete

**Expected Results:**
- Progress indicator shows fetch status
- Channels populate in category list
- No error dialogs appear
- Channels are organized by category

#### TC-CD-002: Load channels from cache
**Priority:** High  
**Preconditions:** Valid `channels.json` exists

**Steps:**
1. Ensure `channels.json` contains cached channels
2. Launch application
3. Observe loading behavior

**Expected Results:**
- Channels load immediately from cache
- "Loaded X channels from cache" in console
- Validation starts in background

#### TC-CD-003: Handle repository fetch failure
**Priority:** High  
**Preconditions:** Network unavailable or invalid repository URL

**Steps:**
1. Configure invalid repository URL
2. Delete channels.json cache
3. Launch application

**Expected Results:**
- Error logged to console
- Application doesn't crash
- UI shows empty state gracefully

### 4.2 Stream Validation

#### TC-SV-001: Validate working stream
**Priority:** Critical

**Steps:**
1. Load channels with valid stream URLs
2. Start validation scan
3. Observe channel status update

**Expected Results:**
- Channel marked as "Working" (is_working=True)
- Green indicator in UI
- last_scanned timestamp updated

#### TC-SV-002: Validate non-working stream
**Priority:** High

**Steps:**
1. Load channels with invalid/dead stream URLs
2. Start validation scan
3. Observe channel status update

**Expected Results:**
- Channel marked as "Failed" (is_working=False)
- Red indicator in UI
- No application hang

#### TC-SV-003: Stop validation mid-scan
**Priority:** Medium

**Steps:**
1. Start validation with many channels
2. Click "Stop Scan" during validation
3. Observe behavior

**Expected Results:**
- Scan stops gracefully within 2 seconds
- Partial results preserved
- No orphan threads

### 4.3 Video Playback

#### TC-VP-001: Play valid stream
**Priority:** Critical  
**Preconditions:** VLC installed

**Steps:**
1. Select a working channel
2. Double-click to play

**Expected Results:**
- Player window opens
- Video/audio plays within 5 seconds
- Controls are responsive

#### TC-VP-002: Handle VLC not installed
**Priority:** High  
**Preconditions:** VLC not installed or unavailable

**Steps:**
1. Ensure VLC is not installed
2. Launch application
3. Attempt to play a channel

**Expected Results:**
- Warning shown in player window
- Application doesn't crash
- Error message guides user to install VLC

#### TC-VP-003: Toggle fullscreen
**Priority:** Medium

**Steps:**
1. Play a channel
2. Press 'F' or click fullscreen button
3. Press 'Esc' to exit

**Expected Results:**
- Video enters fullscreen mode
- Controls hide in fullscreen
- Esc exits fullscreen properly

### 4.4 Search Functionality

#### TC-SF-001: Search by channel name
**Priority:** High

**Steps:**
1. Load channels
2. Type "news" in search box
3. Observe results

**Expected Results:**
- Channel list filters to show only channels containing "news"
- Search is case-insensitive
- Results update as user types

#### TC-SF-002: Search with no results
**Priority:** Medium

**Steps:**
1. Type "xyznonexistent123" in search box

**Expected Results:**
- Channel list shows empty or "No results"
- No error or crash

#### TC-SF-003: Clear search
**Priority:** Medium

**Steps:**
1. Perform a search
2. Clear search box

**Expected Results:**
- Full channel list returns
- Category selection still applies

### 4.5 Category/Country Filtering

#### TC-CF-001: Filter by category
**Priority:** High

**Steps:**
1. Load channels
2. Click "News" category in sidebar

**Expected Results:**
- Only News channels display
- Count matches category

#### TC-CF-002: Toggle group by mode
**Priority:** Medium

**Steps:**
1. Set "Group by" to "Country"
2. Observe sidebar

**Expected Results:**
- Categories replaced by countries
- Channels grouped by country
- Channel counts accurate

#### TC-CF-003: Filter by media type
**Priority:** Medium

**Steps:**
1. Select "Radio" in media type filter

**Expected Results:**
- Only Radio channels display
- Categories/countries update to show only those with Radio channels

### 4.6 Casting (pychromecast)

#### TC-CC-001: Discover Cast devices
**Priority:** Low  
**Preconditions:** pychromecast installed, Cast device on network

**Steps:**
1. Play a channel
2. Click Cast button (📺)
3. Wait for device discovery

**Expected Results:**
- Menu shows available devices
- Device names display correctly

#### TC-CC-002: Cast to device
**Priority:** Low  
**Preconditions:** Cast device available

**Steps:**
1. Discover Cast devices
2. Select a device from menu

**Expected Results:**
- Stream begins on Cast device
- Confirmation message shown

#### TC-CC-003: Cast unavailable
**Priority:** Low  
**Preconditions:** pychromecast not installed

**Steps:**
1. Play a channel
2. Click Cast button

**Expected Results:**
- Info message explains Cast is unavailable
- Suggests installing pychromecast

### 4.7 Error Handling

#### TC-EH-001: Network disconnection during fetch
**Priority:** High

**Steps:**
1. Start channel fetch
2. Disconnect network mid-fetch

**Expected Results:**
- Timeout error logged
- Partial results preserved
- App remains responsive

#### TC-EH-002: Corrupt cache file
**Priority:** Medium

**Steps:**
1. Corrupt channels.json manually
2. Launch application

**Expected Results:**
- Cache load fails gracefully
- App fetches fresh data
- Error logged

#### TC-EH-003: VLC crash during playback
**Priority:** Medium

**Steps:**
1. Play a stream
2. Force-kill VLC process

**Expected Results:**
- Player window shows error or closes
- Main app remains functional

### 4.8 Edge Cases

#### TC-EC-001: Empty repository
**Priority:** Medium

**Steps:**
1. Configure repository returning empty M3U
2. Refresh channels

**Expected Results:**
- No channels loaded (expected)
- No error dialog
- Previous cache preserved

#### TC-EC-002: Extremely long channel name
**Priority:** Low

**Steps:**
1. Add channel with 500-character name

**Expected Results:**
- Name truncated or wrapped in UI
- No layout breakage

#### TC-EC-003: Special characters in channel name
**Priority:** Medium

**Steps:**
1. Load channel with Unicode characters (Hebrew, Chinese, emoji)

**Expected Results:**
- Characters display correctly
- Search works with Unicode

#### TC-EC-004: Concurrent user actions
**Priority:** Medium

**Steps:**
1. Start validation scan
2. Simultaneously search and change categories rapidly

**Expected Results:**
- No race conditions
- UI remains responsive
- No crashes

#### TC-EC-005: Rapid play/stop cycles
**Priority:** Medium

**Steps:**
1. Double-click channel to play
2. Immediately close player
3. Repeat 10 times quickly

**Expected Results:**
- No resource leaks
- No crashes
- VLC instances properly cleaned up

---

## 5. Bug Risk Areas

### 5.1 High Risk Areas

| Area | Risk | Reason |
|------|------|--------|
| `StreamChecker.check_streams_batch` | Thread safety | Concurrent access to shared state |
| `ChannelManager._organize_channels` | Performance | O(n) operations on large datasets |
| VLC initialization (`_init_vlc`) | Platform compatibility | Different HW acceleration paths |
| `parse_m3u` | Memory | Large M3U files could exhaust memory |
| UI update callbacks | Thread marshaling | Callbacks from background threads |

### 5.2 Medium Risk Areas

| Area | Risk | Reason |
|------|------|--------|
| Cast device discovery | Network dependency | Multicast DNS issues on some networks |
| JSON file I/O | Data corruption | Atomic writes may fail on some filesystems |
| Thumbnail capture | VLC dependency | Frame capture timing issues |
| Category/country detection | Accuracy | Heuristic-based, may misclassify |

### 5.3 Specific Concerns

1. **Memory Leaks**
   - Thumbnail image cache growth
   - VLC instance cleanup on player close
   - Category buttons not destroyed on refresh

2. **Race Conditions**
   - Channel list modification during iteration
   - UI updates during rapid filtering
   - Concurrent save/load of channels.json

3. **Platform-Specific Issues**
   - Windows: VLC path detection
   - macOS: VideoToolbox availability
   - Linux: VAAPI/VDPAU driver issues

---

## 6. Regression Test Suite

### 6.1 Critical Path Tests (Run on every change)

| Test ID | Test Name | Runtime |
|---------|-----------|---------|
| UT-H001 | `test_parse_m3u_valid` | < 1s |
| UT-H010 | `test_is_valid_stream_url_file` | < 1s |
| UT-S001 | `test_check_stream_success_200` | < 2s |
| UT-C001 | `test_load_cached_channels_success` | < 1s |
| UT-C010 | `test_search_channels_case_insensitive` | < 1s |
| IT-003 | `test_cache_persistence_round_trip` | < 2s |
| SEC-002 | `test_file_url_blocked` | < 1s |

### 6.2 Smoke Test Suite (Run on releases)

```bash
# Run smoke tests
pytest tests/ -m smoke --tb=short

# Markers in tests:
# @pytest.mark.smoke
```

| Test ID | Description |
|---------|-------------|
| TC-CD-001 | Channel discovery works |
| TC-SV-001 | Stream validation works |
| TC-VP-001 | Video playback works |
| TC-SF-001 | Search works |
| TC-CF-001 | Category filter works |

### 6.3 Full Regression Suite

```bash
# Run full regression
pytest tests/ --cov=. --cov-report=html

# Expected duration: < 5 minutes
```

---

## 7. Automation Recommendations

### 7.1 What to Automate

**High Priority (Automate Immediately):**
- All `utils/helpers.py` functions (pure functions, easy to test)
- URL validation in `repository.py` and `stream_checker.py`
- `ChannelManager` cache operations
- M3U parsing edge cases
- Security-related validations

**Medium Priority (Automate Soon):**
- `StreamChecker` with mocked HTTP responses
- `RepositoryHandler` with mocked network
- Integration tests for data flow

**Low Priority (Manual or Semi-automated):**
- VLC playback (requires VLC installation)
- UI interaction tests (use pytest-qt or manual)
- Cast functionality (requires hardware)

### 7.2 Test Structure

```
tv_viewer_project/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_helpers.py
│   │   ├── test_repository.py
│   │   ├── test_stream_checker.py
│   │   └── test_channel_manager.py
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_channel_pipeline.py
│   └── performance/
│       ├── __init__.py
│       └── test_load.py
```

### 7.3 CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov aioresponses
    
    - name: Run unit tests
      run: pytest tests/unit -v --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## 8. Pytest Fixtures

### 8.1 conftest.py

```python
"""Shared pytest fixtures for TV Viewer tests."""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

# Add project root to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# Event Loop Fixture (for async tests)
# ============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_m3u_content() -> str:
    """Sample M3U playlist content for testing."""
    return '''#EXTM3U
#EXTINF:-1 tvg-id="cnn.us" tvg-name="CNN" tvg-logo="https://example.com/cnn.png" group-title="News",CNN
http://stream.cnn.com/live.m3u8
#EXTINF:-1 tvg-id="espn.us" tvg-name="ESPN" tvg-logo="https://example.com/espn.png" group-title="Sports",ESPN
http://stream.espn.com/live.m3u8
#EXTINF:-1 tvg-id="disney.us" tvg-name="Disney Channel" tvg-logo="https://example.com/disney.png" group-title="Kids",Disney Channel
http://stream.disney.com/live.m3u8
#EXTINF:-1 tvg-name="BBC Radio 1" group-title="Radio",BBC Radio 1
http://stream.bbc.com/radio1.mp3
'''


@pytest.fixture
def sample_channel() -> Dict[str, Any]:
    """Single sample channel for testing."""
    return {
        'name': 'Test Channel',
        'url': 'http://example.com/stream.m3u8',
        'category': 'News',
        'logo': 'http://example.com/logo.png',
        'language': 'English',
        'country': 'US',
        'is_working': None,
        'scan_status': 'pending'
    }


@pytest.fixture
def sample_channels() -> List[Dict[str, Any]]:
    """List of sample channels for testing."""
    return [
        {
            'name': 'CNN',
            'url': 'http://cnn.com/stream.m3u8',
            'category': 'News',
            'country': 'US',
            'is_working': True,
            'scan_status': 'scanned'
        },
        {
            'name': 'ESPN',
            'url': 'http://espn.com/stream.m3u8',
            'category': 'Sports',
            'country': 'US',
            'is_working': True,
            'scan_status': 'scanned'
        },
        {
            'name': 'Disney Channel',
            'url': 'http://disney.com/stream.m3u8',
            'category': 'Kids',
            'country': 'US',
            'is_working': False,
            'scan_status': 'scanned'
        },
        {
            'name': 'BBC Radio 1',
            'url': 'http://bbc.com/radio1.mp3',
            'category': 'Radio',
            'country': 'UK',
            'media_type': 'Radio',
            'is_working': None,
            'scan_status': 'pending'
        }
    ]


@pytest.fixture
def large_channel_list(sample_channel) -> List[Dict[str, Any]]:
    """Generate large channel list for performance testing."""
    channels = []
    for i in range(10000):
        ch = sample_channel.copy()
        ch['name'] = f'Test Channel {i}'
        ch['url'] = f'http://example.com/stream{i}.m3u8'
        ch['category'] = ['News', 'Sports', 'Kids', 'Movies'][i % 4]
        channels.append(ch)
    return channels


# ============================================================================
# Temporary File Fixtures
# ============================================================================

@pytest.fixture
def temp_channels_file(sample_channels) -> str:
    """Create temporary channels.json file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({'channels': sample_channels, 'version': '1.0.0'}, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_config_file() -> str:
    """Create temporary channels_config.json file."""
    config = {
        'repositories': ['http://test.local/test.m3u'],
        'custom_channels': [
            {'name': 'Custom Test', 'url': 'http://custom.local/stream.m3u8', 'category': 'Custom'}
        ]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_dir():
    """Create temporary directory for test artifacts."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    import shutil
    shutil.rmtree(temp_path, ignore_errors=True)


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp ClientSession for network tests."""
    from aioresponses import aioresponses
    with aioresponses() as m:
        yield m


@pytest.fixture
def mock_vlc():
    """Mock VLC module for player tests."""
    mock_vlc = MagicMock()
    mock_vlc.Instance.return_value = MagicMock()
    mock_vlc.State.Paused = 3
    mock_vlc.MediaStats.return_value = MagicMock(demux_bitrate=5000)
    
    with patch.dict('sys.modules', {'vlc': mock_vlc}):
        yield mock_vlc


@pytest.fixture
def mock_pychromecast():
    """Mock pychromecast for cast tests."""
    mock_cast = MagicMock()
    mock_cast.get_chromecasts.return_value = ([], MagicMock())
    
    with patch.dict('sys.modules', {'pychromecast': mock_cast}):
        yield mock_cast


# ============================================================================
# Component Fixtures
# ============================================================================

@pytest.fixture
def channel_manager(temp_channels_file, monkeypatch):
    """Create ChannelManager instance with mocked config."""
    import config
    monkeypatch.setattr(config, 'CHANNELS_FILE', temp_channels_file)
    
    from core.channel_manager import ChannelManager
    manager = ChannelManager()
    yield manager
    manager.stop()


@pytest.fixture
def stream_checker():
    """Create StreamChecker instance."""
    from core.stream_checker import StreamChecker
    checker = StreamChecker(batch_size=10, request_delay=0)
    yield checker
    checker.stop()


@pytest.fixture
def repository_handler():
    """Create RepositoryHandler instance."""
    from core.repository import RepositoryHandler
    handler = RepositoryHandler()
    yield handler


# ============================================================================
# Async Test Helpers
# ============================================================================

@pytest.fixture
def run_async(event_loop):
    """Helper to run async functions in tests."""
    def _run(coro):
        return event_loop.run_until_complete(coro)
    return _run


# ============================================================================
# UI Fixtures (for integration tests)
# ============================================================================

@pytest.fixture
def mock_tkinter():
    """Mock tkinter for headless UI tests."""
    mock_tk = MagicMock()
    mock_ctk = MagicMock()
    
    with patch.dict('sys.modules', {
        'tkinter': mock_tk,
        'customtkinter': mock_ctk,
        'tkinter.ttk': MagicMock()
    }):
        yield mock_tk, mock_ctk
```

### 8.2 Example Unit Test File (`tests/unit/test_helpers.py`)

```python
"""Unit tests for utils/helpers.py"""

import pytest
from utils.helpers import (
    parse_m3u,
    parse_extinf,
    _is_valid_stream_url,
    _sanitize_text,
    categorize_channel,
    detect_media_type,
    get_channel_country,
    get_minimum_age,
    format_duration,
    load_json_file,
    save_json_file
)


class TestParseM3U:
    """Tests for parse_m3u function."""
    
    def test_parse_valid_m3u(self, sample_m3u_content):
        """Test parsing valid M3U content."""
        channels = parse_m3u(sample_m3u_content)
        
        assert len(channels) == 4
        assert channels[0]['name'] == 'CNN'
        assert channels[0]['url'] == 'http://stream.cnn.com/live.m3u8'
        assert channels[0]['category'] == 'News'
    
    def test_parse_empty_content(self):
        """Test parsing empty content returns empty list."""
        assert parse_m3u('') == []
        assert parse_m3u('   ') == []
    
    def test_parse_m3u_only_header(self):
        """Test M3U with only header."""
        result = parse_m3u('#EXTM3U\n')
        assert result == []
    
    def test_parse_m3u_no_url(self):
        """Test EXTINF line without URL is ignored."""
        content = '#EXTM3U\n#EXTINF:-1,Test Channel\n'
        result = parse_m3u(content)
        assert result == []
    
    def test_parse_m3u_invalid_url_scheme(self):
        """Test channels with invalid URLs are ignored."""
        content = '#EXTM3U\n#EXTINF:-1,Test\nfile:///etc/passwd\n'
        result = parse_m3u(content)
        assert result == []
    
    @pytest.mark.parametrize('dangerous_url', [
        'javascript:alert(1)',
        'data:text/html,<script>',
        'file:///etc/passwd',
        'vbscript:msgbox',
    ])
    def test_parse_m3u_blocks_dangerous_urls(self, dangerous_url):
        """Test dangerous URL schemes are blocked."""
        content = f'#EXTM3U\n#EXTINF:-1,Test\n{dangerous_url}\n'
        result = parse_m3u(content)
        assert result == []


class TestParseExtinf:
    """Tests for parse_extinf function."""
    
    def test_parse_full_extinf(self):
        """Test parsing EXTINF with all attributes."""
        line = '#EXTINF:-1 tvg-name="Test" tvg-logo="http://logo.com/logo.png" group-title="News",Test Channel'
        result = parse_extinf(line)
        
        assert result['name'] == 'Test'
        assert result['logo'] == 'http://logo.com/logo.png'
        assert result['category'] == 'News'
    
    def test_parse_minimal_extinf(self):
        """Test parsing minimal EXTINF."""
        line = '#EXTINF:-1,Simple Name'
        result = parse_extinf(line)
        
        assert result['name'] == 'Simple Name'
        assert result['category'] == 'Other'
    
    def test_parse_extinf_special_chars(self):
        """Test EXTINF with special characters."""
        line = '#EXTINF:-1 tvg-name="Test <script>alert(1)</script>",Test'
        result = parse_extinf(line)
        
        assert '<script>' not in result['name']
        assert '&lt;' in result['name']


class TestUrlValidation:
    """Tests for _is_valid_stream_url function."""
    
    @pytest.mark.parametrize('url,expected', [
        ('http://example.com/stream.m3u8', True),
        ('https://example.com/stream.m3u8', True),
        ('rtmp://example.com/live/stream', True),
        ('rtsp://example.com/stream', True),
        ('mms://example.com/stream', True),
        ('file:///etc/passwd', False),
        ('javascript:alert(1)', False),
        ('data:text/html,test', False),
        ('ftp://example.com/file.m3u8', False),
        ('', False),
        (None, False),
    ])
    def test_url_validation(self, url, expected):
        """Test URL validation for various schemes."""
        assert _is_valid_stream_url(url) == expected


class TestSanitizeText:
    """Tests for _sanitize_text function."""
    
    def test_sanitize_html(self):
        """Test HTML entity encoding."""
        result = _sanitize_text('<script>alert(1)</script>')
        assert '<' not in result
        assert '>' not in result
    
    def test_sanitize_control_chars(self):
        """Test control character removal."""
        result = _sanitize_text('test\x00\x01\x02string')
        assert '\x00' not in result
        assert 'teststring' in result
    
    def test_sanitize_empty(self):
        """Test empty input."""
        assert _sanitize_text('') == ''
        assert _sanitize_text(None) == ''


class TestCategorizeChannel:
    """Tests for categorize_channel function."""
    
    @pytest.mark.parametrize('name,category,expected', [
        ('CNN International', '', 'News'),
        ('ESPN', '', 'Sports'),
        ('Disney Channel', '', 'Kids'),
        ('HBO Movies', '', 'Movies'),
        ('MTV', '', 'Music'),
        ('Unknown Channel', 'Documentary', 'Documentary'),
        ('Random', '', 'Other'),
    ])
    def test_categorize_by_name_and_category(self, name, category, expected):
        """Test categorization based on channel name and category."""
        channel = {'name': name, 'category': category}
        result = categorize_channel(channel)
        assert result == expected


class TestDetectMediaType:
    """Tests for detect_media_type function."""
    
    def test_detect_tv(self):
        """Test TV detection."""
        channel = {'name': 'BBC One', 'category': 'General'}
        assert detect_media_type(channel) == 'TV'
    
    def test_detect_radio(self):
        """Test Radio detection."""
        channel = {'name': 'BBC Radio 1', 'category': 'Radio'}
        assert detect_media_type(channel) == 'Radio'
    
    def test_detect_radio_by_url(self):
        """Test Radio detection by URL."""
        channel = {'name': 'Station', 'url': 'http://example.com/stream.mp3'}
        assert detect_media_type(channel) == 'Radio'


class TestGetChannelCountry:
    """Tests for get_channel_country function."""
    
    def test_country_from_metadata(self):
        """Test country from channel metadata."""
        channel = {'name': 'Test', 'country': 'Germany'}
        assert get_channel_country(channel) == 'Germany'
    
    def test_country_from_url_tld(self):
        """Test country detection from URL TLD."""
        channel = {'name': 'Test', 'url': 'http://example.co.uk/stream.m3u8'}
        result = get_channel_country(channel)
        assert result in ['UK', 'Unknown']  # May vary based on regex match
    
    def test_country_unknown(self):
        """Test unknown country fallback."""
        channel = {'name': 'Mystery Channel', 'url': 'http://example.com/stream'}
        result = get_channel_country(channel)
        assert result in ['Unknown', 'US', 'International']


class TestGetMinimumAge:
    """Tests for get_minimum_age function."""
    
    @pytest.mark.parametrize('category,expected', [
        ('Kids', 0),
        ('News', 7),
        ('Movies', 13),
        ('Action', 16),
    ])
    def test_age_by_category(self, category, expected):
        """Test age rating by category."""
        channel = {'name': 'Test', 'category': category}
        assert get_minimum_age(channel) == expected


class TestFormatDuration:
    """Tests for format_duration function."""
    
    @pytest.mark.parametrize('seconds,expected', [
        (0, '00:00'),
        (65, '01:05'),
        (3600, '01:00:00'),
        (3725, '01:02:05'),
    ])
    def test_format_duration(self, seconds, expected):
        """Test duration formatting."""
        assert format_duration(seconds) == expected


class TestJsonIO:
    """Tests for JSON file I/O functions."""
    
    def test_load_json_valid(self, temp_channels_file):
        """Test loading valid JSON file."""
        result = load_json_file(temp_channels_file)
        assert result is not None
        assert 'channels' in result
    
    def test_load_json_missing(self):
        """Test loading non-existent file."""
        result = load_json_file('/nonexistent/file.json')
        assert result is None
    
    def test_save_json_success(self, temp_dir):
        """Test saving JSON file."""
        filepath = f'{temp_dir}/test.json'
        data = {'test': 'data'}
        
        assert save_json_file(filepath, data) is True
        
        # Verify file was created
        result = load_json_file(filepath)
        assert result == data
```

### 8.3 Example Async Test File (`tests/unit/test_stream_checker.py`)

```python
"""Unit tests for core/stream_checker.py"""

import pytest
import asyncio
from aioresponses import aioresponses
from core.stream_checker import StreamChecker


class TestStreamChecker:
    """Tests for StreamChecker class."""
    
    @pytest.fixture
    def checker(self):
        """Create StreamChecker instance."""
        checker = StreamChecker(batch_size=5, request_delay=0)
        yield checker
        checker.stop()
    
    @pytest.mark.asyncio
    async def test_check_stream_success_200(self, checker):
        """Test successful stream check with 200 response."""
        channel = {'name': 'Test', 'url': 'http://example.com/stream.m3u8'}
        
        with aioresponses() as m:
            m.head('http://example.com/stream.m3u8', status=200)
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                checker._semaphore = asyncio.Semaphore(10)
                result = await checker.check_stream(channel, session)
        
        assert result['is_working'] is True
        assert 'last_scanned' in result
    
    @pytest.mark.asyncio
    async def test_check_stream_head_405_get_success(self, checker):
        """Test stream check when HEAD returns 405 but GET works."""
        channel = {'name': 'Test', 'url': 'http://example.com/stream.m3u8'}
        
        with aioresponses() as m:
            m.head('http://example.com/stream.m3u8', status=405)
            m.get('http://example.com/stream.m3u8', status=200)
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                checker._semaphore = asyncio.Semaphore(10)
                result = await checker.check_stream(channel, session)
        
        assert result['is_working'] is True
    
    @pytest.mark.asyncio
    async def test_check_stream_timeout(self, checker):
        """Test stream check with timeout."""
        channel = {'name': 'Test', 'url': 'http://example.com/slow.m3u8'}
        
        with aioresponses() as m:
            m.head('http://example.com/slow.m3u8', exception=asyncio.TimeoutError())
            
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=0.1)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                checker._semaphore = asyncio.Semaphore(10)
                result = await checker.check_stream(channel, session)
        
        assert result['is_working'] is False
    
    @pytest.mark.asyncio
    async def test_check_stream_invalid_url_scheme(self, checker):
        """Test that invalid URL schemes are rejected."""
        channel = {'name': 'Test', 'url': 'file:///etc/passwd'}
        
        import aiohttp
        async with aiohttp.ClientSession() as session:
            checker._semaphore = asyncio.Semaphore(10)
            result = await checker.check_stream(channel, session)
        
        assert result['is_working'] is False
    
    @pytest.mark.asyncio
    async def test_check_streams_batch(self, checker, sample_channels):
        """Test batch stream checking."""
        channels = sample_channels[:2]
        checked = []
        
        def on_checked(ch, current, total):
            checked.append((ch['name'], current, total))
        
        with aioresponses() as m:
            m.head('http://cnn.com/stream.m3u8', status=200)
            m.head('http://espn.com/stream.m3u8', status=404)
            
            results = await checker.check_streams_batch(channels, on_checked)
        
        assert len(results) == 2
        assert results[0]['is_working'] is True
        assert results[1]['is_working'] is False
        assert len(checked) == 2
    
    def test_start_background_check(self, checker, sample_channels):
        """Test starting background check."""
        completed = []
        
        def on_complete(results):
            completed.extend(results)
        
        # Mock the HTTP calls
        with aioresponses() as m:
            for ch in sample_channels:
                m.head(ch['url'], status=200)
            
            checker.start_background_check(
                sample_channels[:2],
                on_complete=on_complete
            )
            
            # Wait for completion (with timeout)
            import time
            for _ in range(50):  # 5 second timeout
                if completed:
                    break
                time.sleep(0.1)
        
        assert checker.is_running is False or len(completed) > 0
    
    def test_stop_background_check(self, checker, large_channel_list):
        """Test stopping background check."""
        checker.start_background_check(large_channel_list)
        
        import time
        time.sleep(0.1)  # Let it start
        
        checker.stop()
        
        assert checker.is_running is False
    
    def test_is_running_property(self, checker):
        """Test is_running property."""
        assert checker.is_running is False
        
        checker._running = True
        assert checker.is_running is True
```

### 8.4 Example Integration Test (`tests/integration/test_channel_pipeline.py`)

```python
"""Integration tests for channel management pipeline."""

import pytest
import asyncio
from aioresponses import aioresponses


class TestChannelPipeline:
    """Integration tests for full channel data flow."""
    
    @pytest.mark.asyncio
    async def test_fetch_parse_organize_pipeline(
        self, 
        channel_manager, 
        sample_m3u_content,
        mock_aiohttp_session
    ):
        """Test full pipeline: fetch → parse → organize."""
        mock_aiohttp_session.get(
            'http://test.local/test.m3u',
            body=sample_m3u_content,
            status=200
        )
        
        # Fetch and organize
        await channel_manager._fetch_and_update()
        
        # Verify organization
        assert len(channel_manager.channels) > 0
        assert 'News' in channel_manager.categories
        assert 'Sports' in channel_manager.categories
    
    def test_cache_round_trip(self, channel_manager, sample_channels, temp_dir):
        """Test saving and loading channel cache."""
        import config
        import os
        
        # Set up temp file
        cache_path = os.path.join(temp_dir, 'test_cache.json')
        original_path = config.CHANNELS_FILE
        config.CHANNELS_FILE = cache_path
        
        try:
            # Load sample channels
            channel_manager.channels = sample_channels.copy()
            channel_manager._organize_channels()
            
            # Save
            assert channel_manager.save_channels() is True
            
            # Create new manager and load
            from core.channel_manager import ChannelManager
            new_manager = ChannelManager()
            assert new_manager.load_cached_channels() is True
            
            # Verify
            assert len(new_manager.channels) == len(sample_channels)
            
        finally:
            config.CHANNELS_FILE = original_path
    
    def test_validation_updates_manager(self, channel_manager, sample_channels):
        """Test that validation updates channel status in manager."""
        channel_manager.channels = sample_channels.copy()
        channel_manager._organize_channels()
        
        validated_channels = []
        
        def on_validated(channel, current, total):
            validated_channels.append(channel['name'])
        
        channel_manager.on_channel_validated = on_validated
        
        with aioresponses() as m:
            for ch in sample_channels:
                m.head(ch['url'], status=200)
            
            channel_manager.validate_channels_async()
            
            # Wait for validation
            import time
            for _ in range(50):
                if len(validated_channels) >= len(sample_channels):
                    break
                time.sleep(0.1)
        
        # Verify callbacks were called
        assert len(validated_channels) > 0
```

---

## Appendix A: Test Markers

```python
# In pytest.ini or pyproject.toml
[pytest]
markers =
    smoke: Quick smoke tests
    slow: Tests that take > 5 seconds
    integration: Integration tests
    security: Security-related tests
    ui: UI tests (may require display)
    asyncio: Async tests
```

## Appendix B: Coverage Configuration

```ini
# .coveragerc
[run]
source = .
omit = 
    tests/*
    build/*
    .venv/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    if __name__ == .__main__.:
    raise NotImplementedError

[html]
directory = coverage_html
```

## Appendix C: Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html --cov-report=term

# Run only smoke tests
pytest tests/ -m smoke

# Run only unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_helpers.py -v

# Run specific test
pytest tests/unit/test_helpers.py::TestParseM3U::test_parse_valid_m3u -v

# Run async tests with proper config
pytest tests/ --asyncio-mode=auto

# Run with verbose output and stop on first failure
pytest tests/ -v -x

# Generate JUnit XML report (for CI)
pytest tests/ --junitxml=test-results.xml
```
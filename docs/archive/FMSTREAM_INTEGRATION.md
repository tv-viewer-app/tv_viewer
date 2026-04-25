# FMStream.org Radio Integration Guide

## Overview

This document describes the implementation of GitHub Issue #32: Adding FMStream.org as a radio streams source to TV Viewer.

## Implementation Summary

### Files Created

1. **Flutter/Android**: `flutter_app/lib/services/fmstream_service.dart`
   - Service for fetching and parsing FMStream.org radio directory
   - Returns `List<Channel>` compatible with existing channel model
   - Includes HTML parsing with multiple fallback strategies

2. **Python/Windows**: `utils/fmstream.py`
   - Utility for fetching and parsing FMStream.org radio stations
   - Returns `List[Dict]` compatible with existing channel structure
   - Includes security validations and error handling

## Features

### ✅ Core Requirements

- [x] Parse FMStream.org radio directory (HTML format)
- [x] Extract stream URLs, station names, countries, genres
- [x] Handle multiple stream qualities per station
- [x] De-duplicate against existing channels
- [x] Quality selection (prefer higher bitrate)
- [x] Set mediaType = 'Radio' for all channels
- [x] Optional source (can be enabled/disabled)

### ✅ Additional Features

- [x] Multiple HTML parsing strategies for robustness
- [x] Context-aware metadata extraction
- [x] Bitrate detection (128kbps, 320kbps, etc.)
- [x] Country/genre inference from context
- [x] Logo extraction when available
- [x] Stream URL validation
- [x] Comprehensive error handling
- [x] Security validations (XSS prevention, DoS protection)
- [x] Progress callbacks (Flutter)
- [x] Detailed logging

## Architecture

### Flutter Service (fmstream_service.dart)

```dart
class FMStreamService {
  // Main entry point
  static Future<List<Channel>> fetchFromFMStream({
    void Function(int current, int total)? onProgress,
  })
  
  // HTML parsing with 3 strategies
  static List<Channel> parseHTML(String html)
  
  // Deduplication logic
  static List<Channel> deduplicateStations(List<Channel> stations)
  
  // Stream validation
  static Future<bool> checkStream(String url)
}
```

**Parsing Strategies:**
1. **Directory Links**: Extracts from anchor tags with station pages
2. **Stream Links**: Finds direct .pls, .m3u, /stream URLs
3. **Table Structures**: Parses HTML tables with station data

### Python Utility (fmstream.py)

```python
def fetch_fmstream_stations(
    url: str = 'http://fmstream.org',
    existing_channels: Optional[List[Dict]] = None,
    max_stations: int = 5000
) -> List[Dict[str, Any]]

def parse_html(
    html_content: str,
    base_url: str = 'http://fmstream.org'
) -> List[Dict[str, Any]]

def extract_station_info(
    station_name: str,
    stream_url: str,
    context: str = '',
    base_url: str = 'http://fmstream.org'
) -> Optional[Dict[str, Any]]
```

**Security Features:**
- URL validation (blocks javascript:, file://, data:)
- Content size limits (10MB max)
- DoS prevention (max 5000 stations)
- XSS prevention in text sanitization
- Private IP blocking

## Integration

### Flutter Integration

#### Option 1: Add to Channel Provider

```dart
// In lib/providers/channel_provider.dart

import '../services/fmstream_service.dart';

Future<void> loadChannelsWithFMStream() async {
  try {
    // Load from M3U sources
    final m3uChannels = await M3UService.fetchAllChannels(
      onProgress: (current, total) {
        // Update progress
      },
    );
    
    // Load from FMStream (optional)
    if (_enableFMStream) {
      final fmStreamChannels = await FMStreamService.fetchFromFMStream(
        onProgress: (current, total) {
          // Update progress
        },
      );
      
      // Merge and deduplicate
      final allChannels = [...m3uChannels, ...fmStreamChannels];
      final deduplicated = M3UService.deduplicateChannels(allChannels);
      
      _channels = deduplicated;
    } else {
      _channels = m3uChannels;
    }
    
    notifyListeners();
  } catch (e) {
    logger.error('Error loading channels', e);
  }
}
```

#### Option 2: Standalone Usage

```dart
// Fetch FMStream stations independently
final stations = await FMStreamService.fetchFromFMStream(
  onProgress: (current, total) {
    print('Progress: $current/$total');
  },
);

// Filter radio stations
final radioStations = stations.where((ch) => ch.mediaType == 'Radio').toList();

print('Found ${radioStations.length} radio stations');
```

### Python Integration

#### Option 1: Add to Channel Manager

```python
# In core/channel_manager.py

from utils.fmstream import fetch_fmstream_stations

def load_channels_with_fmstream(self):
    """Load channels from M3U repos and FMStream."""
    
    # Load from M3U repositories
    m3u_channels = self.repository_handler.fetch_all_channels()
    
    # Load from FMStream (optional)
    if self.config.get('enable_fmstream', False):
        try:
            fmstream_channels = fetch_fmstream_stations(
                existing_channels=m3u_channels,
                max_stations=1000
            )
            
            # Merge channels
            all_channels = m3u_channels + fmstream_channels
            
            # Deduplicate by URL
            seen_urls = set()
            unique_channels = []
            for ch in all_channels:
                url = ch.get('url', '').strip().lower()
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_channels.append(ch)
            
            self.channels = unique_channels
        except Exception as e:
            logger.error(f"Error loading FMStream channels: {e}")
            self.channels = m3u_channels
    else:
        self.channels = m3u_channels
```

#### Option 2: Standalone Usage

```python
from utils.fmstream import fetch_fmstream_stations

# Fetch stations with deduplication
existing_channels = [...]  # Your existing channels
stations = fetch_fmstream_stations(
    url='http://fmstream.org',
    existing_channels=existing_channels,
    max_stations=1000
)

# Filter by country
uk_stations = [s for s in stations if s.get('country') == 'UK']

# Print station info
for station in stations:
    print(f"{station['name']} ({station['country']}) - {station['bitrate']}bps")
```

## Configuration

### Enable/Disable FMStream Source

#### Flutter Configuration

Add to `lib/services/m3u_service.dart` or create settings provider:

```dart
class AppSettings {
  bool enableFMStream = false;
  
  void toggleFMStream(bool enabled) {
    enableFMStream = enabled;
    // Save to SharedPreferences
  }
}
```

#### Python Configuration

Add to `config.py`:

```python
# FMStream.org radio source
ENABLE_FMSTREAM = True  # Set to False to disable
FMSTREAM_URL = 'http://fmstream.org'
FMSTREAM_MAX_STATIONS = 1000
```

Or via `channels_config.json`:

```json
{
  "repositories": [
    "https://iptv-org.github.io/iptv/index.m3u",
    "https://iptv-org.github.io/iptv/index.category.m3u"
  ],
  "fmstream": {
    "enabled": true,
    "url": "http://fmstream.org",
    "max_stations": 1000
  },
  "custom_channels": []
}
```

## Data Model

### Channel Structure

Both implementations return channels compatible with the existing data model:

**Flutter (Channel class):**
```dart
Channel(
  name: 'BBC Radio 1',
  url: 'http://stream.bbc.co.uk/radio1',
  category: 'Music',
  country: 'UK',
  language: 'English',
  mediaType: 'Radio',
  bitrate: 320000,  // 320kbps in bps
  logo: 'http://example.com/logo.png',
)
```

**Python (dict):**
```python
{
    'name': 'BBC Radio 1',
    'url': 'http://stream.bbc.co.uk/radio1',
    'category': 'Music',
    'country': 'UK',
    'language': 'English',
    'media_type': 'Radio',
    'bitrate': 320000,  # 320kbps in bps
    'logo': 'http://example.com/logo.png',
}
```

## Quality Selection

When multiple streams are available for the same station, the service selects the best one based on:

1. **Bitrate** (higher is better)
   - 320kbps > 256kbps > 192kbps > 128kbps > 96kbps > 64kbps

2. **Metadata Completeness** (if bitrate is equal)
   - Channels with more complete metadata (country, genre, logo) are preferred

3. **URL Quality** (if all else equal)
   - Direct stream URLs preferred over playlist files

## Deduplication

Deduplication works at two levels:

### 1. Internal Deduplication
- Removes duplicate stations within FMStream results
- Keeps the station with highest bitrate or best metadata

### 2. Cross-Source Deduplication
- Compares against existing channels from M3U sources
- Prevents adding stations already available from other sources
- Can be disabled to show all available sources

**Flutter:**
```dart
final deduplicated = M3UService.deduplicateChannels([
  ...m3uChannels,
  ...fmstreamChannels,
]);
```

**Python:**
```python
stations = fetch_fmstream_stations(
    existing_channels=m3u_channels,  # Dedup against these
    max_stations=1000
)
```

## Error Handling

### Flutter

```dart
try {
  final stations = await FMStreamService.fetchFromFMStream();
  // Use stations
} catch (e) {
  if (e is AppError) {
    print('Error: ${e.userMessage}');
    print('Code: ${e.code}');
  } else {
    print('Unexpected error: $e');
  }
}
```

### Python

```python
try:
    stations = fetch_fmstream_stations()
    # Use stations
except Exception as e:
    logger.error(f"Error fetching FMStream stations: {e}")
    # Fallback to M3U only
    stations = []
```

## Testing

### Manual Testing

#### Flutter
```dart
// In a test file or main.dart
void testFMStream() async {
  final stations = await FMStreamService.fetchFromFMStream(
    onProgress: (current, total) {
      print('Progress: $current/$total');
    },
  );
  
  print('Found ${stations.length} stations');
  for (final station in stations.take(10)) {
    print('${station.name} - ${station.url}');
  }
}
```

#### Python
```python
# In a test script
from utils.fmstream import fetch_fmstream_stations

def test_fmstream():
    stations = fetch_fmstream_stations(max_stations=10)
    print(f"Found {len(stations)} stations")
    for station in stations:
        print(f"{station['name']} - {station['url']}")

if __name__ == '__main__':
    test_fmstream()
```

### Unit Tests

#### Flutter (test/services/fmstream_service_test.dart)
```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:tv_viewer/services/fmstream_service.dart';

void main() {
  group('FMStreamService', () {
    test('parseHTML extracts stations', () {
      final html = '''
        <a href="http://example.com/stream">Test Radio</a>
      ''';
      
      final stations = FMStreamService.parseHTML(html);
      expect(stations.length, greaterThan(0));
      expect(stations.first.mediaType, 'Radio');
    });
    
    test('deduplicateStations removes duplicates', () {
      // Test deduplication logic
    });
  });
}
```

#### Python (tests/test_fmstream.py)
```python
import unittest
from utils.fmstream import parse_html, extract_station_info

class TestFMStream(unittest.TestCase):
    def test_parse_html(self):
        html = '<a href="http://example.com/stream">Test Radio</a>'
        stations = parse_html(html)
        self.assertGreater(len(stations), 0)
        self.assertEqual(stations[0]['media_type'], 'Radio')
    
    def test_extract_station_info(self):
        station = extract_station_info(
            station_name='Test Radio',
            stream_url='http://example.com/stream',
            context='UK 128kbps'
        )
        self.assertIsNotNone(station)
        self.assertEqual(station['media_type'], 'Radio')

if __name__ == '__main__':
    unittest.main()
```

## Performance Considerations

### Flutter
- HTML parsing is CPU-intensive; runs on isolate if needed
- Progress callbacks for UI responsiveness
- Timeouts prevent hanging (30s for fetch)
- Stream validation can be batched (5 at a time)

### Python
- HTML content size limited to 10MB
- Max 5000 stations to prevent DoS
- Request timeout of 15 seconds
- Streaming HTTP response for large pages
- Regex compilation is cached

## Security

### Input Validation
- ✅ URL scheme validation (only http/https)
- ✅ Content size limits
- ✅ Line length limits
- ✅ HTML entity decoding
- ✅ XSS prevention in text sanitization

### Output Validation
- ✅ Stream URL validation
- ✅ Sanitized station names
- ✅ Validated metadata fields
- ✅ No script injection possible

### Network Security
- ✅ User-Agent header for proper HTTP requests
- ✅ Timeout handling
- ✅ No credentials in URLs
- ✅ HTTPS preferred when available

## Troubleshooting

### No Stations Found

**Possible causes:**
1. FMStream.org changed their HTML structure
2. Network connectivity issues
3. Website is down
4. HTML parsing regex needs updating

**Solutions:**
1. Check if website is accessible in browser
2. Review logs for parsing errors
3. Update regex patterns if HTML structure changed
4. Add more parsing strategies

### Low Quality Streams

**Solutions:**
1. Adjust quality selection logic
2. Filter by minimum bitrate (e.g., only 128kbps+)
3. Validate streams before adding to list
4. Prefer direct stream URLs over playlists

### Duplicate Stations

**Solutions:**
1. Ensure deduplication is enabled
2. Compare against existing M3U channels
3. Use stricter URL matching (normalize URLs)
4. Compare station names (fuzzy matching)

## Future Enhancements

1. **Caching**: Cache FMStream results for faster subsequent loads
2. **Favorites**: Allow users to favorite specific stations
3. **Search**: Add search/filter by country, genre, bitrate
4. **Auto-Update**: Periodically refresh station list
5. **User Ratings**: Allow users to rate stream quality
6. **Geo-Detection**: Auto-select stations based on user location
7. **M3U Export**: Export FMStream stations as M3U playlist
8. **Multi-Source**: Support multiple radio directory sites

## References

- GitHub Issue #32: Add FMStream.org radio streams source
- Channel Model: `flutter_app/lib/models/channel.dart`
- M3U Service: `flutter_app/lib/services/m3u_service.dart`
- Helpers: `utils/helpers.py`
- Config: `config.py`

## Changelog

### v1.0.0 (Initial Implementation)
- ✅ Created FMStreamService for Flutter
- ✅ Created fmstream.py utility for Python
- ✅ HTML parsing with 3 strategies
- ✅ Metadata extraction (country, genre, bitrate)
- ✅ Quality selection and deduplication
- ✅ Security validations
- ✅ Error handling and logging
- ✅ Integration examples
- ✅ Documentation

---

**Status**: ✅ Implementation Complete
**Date**: 2024
**Issue**: #32
**Contributors**: TV Viewer Development Team

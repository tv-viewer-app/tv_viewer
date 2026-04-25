# FMStream Quick Start Guide

Add radio stations from FMStream.org to your TV Viewer app in just a few lines of code!

---

## Flutter (Android)

### 1. Basic Usage

```dart
import '../services/fmstream_service.dart';

// Fetch radio stations
final stations = await FMStreamService.fetchFromFMStream();

print('Found ${stations.length} radio stations!');
```

### 2. With Progress Updates

```dart
final stations = await FMStreamService.fetchFromFMStream(
  onProgress: (current, total) {
    print('Loading: $current/$total');
  },
);
```

### 3. Merge with M3U Channels

```dart
// Load from both sources
final m3uChannels = await M3UService.fetchAllChannels();
final fmstreamStations = await FMStreamService.fetchFromFMStream();

// Merge and deduplicate
final allChannels = [...m3uChannels, ...fmstreamStations];
final unique = M3UService.deduplicateChannels(allChannels);

print('Total unique channels: ${unique.length}');
```

### 4. Filter Radio Stations

```dart
// Get only radio stations
final radioStations = unique.where((ch) => ch.mediaType == 'Radio').toList();

// Get high-quality radio (>= 128kbps)
final hqRadio = radioStations
    .where((ch) => ch.bitrate != null && ch.bitrate! >= 128000)
    .toList();

// Get stations by country
final ukStations = radioStations
    .where((ch) => ch.country == 'UK')
    .toList();
```

---

## Python (Windows)

### 1. Basic Usage

```python
from utils.fmstream import fetch_fmstream_stations

# Fetch radio stations
stations = fetch_fmstream_stations()

print(f"Found {len(stations)} radio stations!")
```

### 2. With Deduplication

```python
# Load M3U channels first
m3u_channels = load_m3u_channels()

# Fetch FMStream with deduplication
stations = fetch_fmstream_stations(
    url='http://fmstream.org',
    existing_channels=m3u_channels,
    max_stations=1000
)
```

### 3. Filter Stations

```python
# Get stations by country
uk_stations = [s for s in stations if s.get('country') == 'UK']

# Get high-quality radio (>= 128kbps)
hq_stations = [s for s in stations if s.get('bitrate', 0) >= 128000]

# Get stations by genre
jazz_stations = [s for s in stations if s.get('category') == 'Jazz']
```

---

## Testing

### Test Python Implementation

```bash
# Fetch 50 stations and display info
python test_fmstream.py --max 50

# Filter by country
python test_fmstream.py --country UK

# Filter by minimum bitrate
python test_fmstream.py --min-bitrate 128

# Verbose output
python test_fmstream.py --verbose
```

---

## Configuration

### Enable/Disable FMStream

#### Python (`config.py`)

```python
# Add these settings
ENABLE_FMSTREAM = True  # Set to False to disable
FMSTREAM_URL = 'http://fmstream.org'
FMSTREAM_MAX_STATIONS = 1000
```

#### Flutter (in settings provider)

```dart
bool enableFMStream = true;

void toggleFMStream() {
  enableFMStream = !enableFMStream;
  // Reload channels if needed
}
```

---

## Channel Data Structure

### Flutter (Channel class)

```dart
Channel(
  name: 'BBC Radio 1',
  url: 'http://stream.bbc.co.uk/radio1',
  mediaType: 'Radio',          // Always 'Radio'
  country: 'UK',
  category: 'Music',
  language: 'English',
  bitrate: 320000,             // 320kbps in bps
  logo: 'http://...',
)
```

### Python (dict)

```python
{
    'name': 'BBC Radio 1',
    'url': 'http://stream.bbc.co.uk/radio1',
    'media_type': 'Radio',     # Always 'Radio'
    'country': 'UK',
    'category': 'Music',
    'language': 'English',
    'bitrate': 320000,         # 320kbps in bps
    'logo': 'http://...',
}
```

---

## Error Handling

### Flutter

```dart
try {
  final stations = await FMStreamService.fetchFromFMStream();
  // Use stations
} catch (e) {
  print('Error: $e');
  // Fallback to M3U only
}
```

### Python

```python
try:
    stations = fetch_fmstream_stations()
    # Use stations
except Exception as e:
    print(f"Error: {e}")
    # Fallback to M3U only
    stations = []
```

---

## Examples

### Complete Integration Examples

- **Python**: `fmstream_integration_example.py`
- **Flutter**: `flutter_app/fmstream_integration_example.dart`

### Full Documentation

- **Integration Guide**: `FMSTREAM_INTEGRATION.md`
- **Implementation Summary**: `ISSUE_32_IMPLEMENTATION_SUMMARY.md`

---

## Features

✅ Extracts station names, URLs, countries, genres, bitrates  
✅ Handles multiple stream qualities (prefers higher bitrate)  
✅ De-duplicates against existing channels  
✅ Sets mediaType = 'Radio' automatically  
✅ Optional source (can be enabled/disabled)  
✅ Comprehensive error handling  
✅ Security validations (XSS prevention, URL validation)  
✅ Progress callbacks (Flutter)  

---

## Need Help?

- **Full docs**: See `FMSTREAM_INTEGRATION.md`
- **Examples**: See `*_integration_example.py/dart`
- **Testing**: Run `python test_fmstream.py --help`

---

**Status**: ✅ Production Ready  
**Issue**: GitHub #32  
**Version**: 1.0.0

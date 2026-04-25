# EPG (Electronic Program Guide) Feature - Issue #20

## Overview

This feature adds simple EPG/schedule information display for IPTV channels. Since EPG data is often not available in free IPTV sources, the implementation focuses on **graceful degradation** with placeholders when data is unavailable.

## Implementation Details

### Components Created

#### 1. **Models** (`lib/models/epg_info.dart`)

- **`EpgInfo`** - Represents a single program/show
  - Program title, description, start/end times, category
  - Calculates progress, remaining time, duration
  - Formats time ranges (e.g., "14:00 - 15:30")
  - Factory for placeholder data when EPG unavailable
  
- **`ChannelEpg`** - Collection of programs for a channel
  - Manages channel schedule
  - Finds current and next programs
  - Provides placeholder EPG when data unavailable
  - Supports JSON serialization for future API integration

#### 2. **Widgets** (`lib/widgets/epg_display.dart`)

- **`EpgDisplay`** - Full EPG display widget
  - Shows "Now Playing" and "Next" program cards
  - Progress bar for current program
  - Visual indicators for data availability
  - Displays category, description, time range, duration
  - Graceful degradation to placeholders
  
- **`CompactEpgDisplay`** - Compact EPG widget
  - Minimal space usage for overlays
  - Shows current program and time remaining
  - Visual indicator for live/placeholder status

#### 3. **Model Updates** (`lib/models/channel.dart`)

- Added `tvgId` field to Channel model
- Parses `tvg-id` attribute from M3U files
- Used as reference ID for EPG data lookup
- Included in JSON serialization

### Integration with Player Screen

The EPG display is integrated into the video player (`lib/screens/player_screen.dart`):

1. **Compact Display** - Always visible in top overlay
   - Shows current program title
   - Appears with channel name and quality info
   
2. **Full Display** - Toggle with info button
   - Shows detailed "Now" and "Next" program info
   - Auto-hides after 10 seconds
   - Positioned above bottom controls
   
3. **Info Button** - New control in top bar
   - Icon changes color when EPG overlay active
   - Toggles full EPG display

## Usage Examples

### Basic Placeholder Usage (No EPG Data)

```dart
// In player or channel detail screen
EpgDisplay.placeholder()
```

This shows:
- "NOW PLAYING: Live Broadcast" 
- "NEXT: Scheduled Program"
- With note "EPG data not available"

### With Actual EPG Data (Future Enhancement)

```dart
final channelEpg = ChannelEpg(
  channelId: channel.tvgId ?? channel.name,
  channelName: channel.name,
  programs: [
    EpgInfo(
      programTitle: 'Evening News',
      description: 'Breaking news and weather',
      startTime: DateTime(2024, 1, 15, 18, 0),
      endTime: DateTime(2024, 1, 15, 19, 0),
      category: 'News',
    ),
    // ... more programs
  ],
);

// Display EPG
EpgDisplay.fromChannelEpg(channelEpg)
```

### Compact Display

```dart
// For overlays or minimal UI
CompactEpgDisplay.placeholder()

// Or with data
CompactEpgDisplay.fromChannelEpg(channelEpg)
```

## M3U File Format Support

The feature parses EPG reference IDs from M3U files:

```m3u
#EXTINF:-1 tvg-id="cnn" tvg-logo="logo.png" group-title="News",CNN International
http://stream.example.com/cnn.m3u8
```

The `tvg-id="cnn"` attribute is stored in `channel.tvgId` for future EPG lookups.

## Design Decisions

### Why Placeholders?

1. **Free IPTV sources rarely provide EPG data**
2. **Better UX** - Show something rather than nothing
3. **Progressive enhancement** - Easy to plug in real data later
4. **Sets user expectations** - Clear indication when data unavailable

### Visual Design

- **Color coding**: Red for "NOW", Blue for "NEXT"
- **Status indicators**: Green icon for real data, grey for placeholder
- **Progress bars**: Only shown for currently airing programs
- **Info tooltips**: Explain when EPG data unavailable

### Auto-hide Behavior

- Compact display: Always visible with controls
- Full display: Auto-hides after 10 seconds
- Reason: Don't obscure video content

## Future Enhancements (Out of Scope)

This simplified implementation sets the foundation for:

1. **External EPG Sources**
   - XMLTV format support
   - EPG API integration (e.g., EPG.pw, XMLTV.org)
   - Local EPG file loading
   
2. **EPG Data Service**
   ```dart
   class EpgService {
     Future<ChannelEpg?> fetchEpg(String tvgId);
     Stream<ChannelEpg> getEpgStream(String tvgId);
     void cacheEpg(String tvgId, ChannelEpg epg);
   }
   ```

3. **Advanced Features**
   - Full program schedule (7-day view)
   - Program reminders/notifications
   - Search programs across channels
   - Record/catch-up integration
   - Genre-based browsing

4. **EPG Update Mechanism**
   - Periodic background refresh
   - Smart caching with expiry
   - Delta updates to save bandwidth

## Testing

Comprehensive tests included:

- **`test/models/epg_info_test.dart`** - Model logic and edge cases
- **`test/widgets/epg_display_test.dart`** - Widget rendering
- **`test/models/channel_test.dart`** - Updated for tvgId parsing

Run tests:
```bash
flutter test test/models/epg_info_test.dart
flutter test test/widgets/epg_display_test.dart
flutter test test/models/channel_test.dart
```

## API Reference

### EpgInfo

```dart
// Properties
String programTitle
String? description
DateTime startTime
DateTime endTime
String? category

// Computed
double progress           // 0.0 to 1.0
bool isCurrentlyAiring
int remainingMinutes
String timeRange         // "14:00 - 15:30"
String duration          // "1h 30min"

// Factory
EpgInfo.placeholder({required bool isNow})
EpgInfo.fromJson(Map<String, dynamic> json)
```

### ChannelEpg

```dart
// Properties
String channelId
String channelName
List<EpgInfo> programs

// Computed
EpgInfo? currentProgram
EpgInfo? nextProgram

// Methods
Map<String, EpgInfo> getCurrentAndNext()

// Factory
ChannelEpg.placeholder({required String channelId, required String channelName})
ChannelEpg.fromJson(Map<String, dynamic> json)
```

### Widgets

```dart
// Full display
EpgDisplay({
  required EpgInfo nowPlaying,
  required EpgInfo nextProgram,
  bool isDataAvailable = false,
})

EpgDisplay.placeholder()
EpgDisplay.fromChannelEpg(ChannelEpg channelEpg)

// Compact display
CompactEpgDisplay({
  required EpgInfo nowPlaying,
  bool isDataAvailable = false,
})

CompactEpgDisplay.placeholder()
CompactEpgDisplay.fromChannelEpg(ChannelEpg channelEpg)
```

## Troubleshooting

### EPG info not showing
- Check that imports are correct
- Verify player_screen.dart includes EPG widgets
- Ensure `_showEpgInfo` state is toggled

### tvg-id not parsed
- Verify M3U format: `tvg-id="value"`
- Check Channel.fromM3ULine() regex
- Test with sample M3U file

### Widget rendering issues
- Check MaterialApp wrapper in tests
- Verify theme/color compatibility
- Test in both light/dark modes

## Related Issues

- Issue #20: Add channel EPG/schedule info (simplified version) - **IMPLEMENTED**
- Issue #19: DVR/Recording feature - Future work
- Issue #12: Add category filtering - Related (EPG by genre)

## Screenshots

See player_screen.dart in action:
1. Top overlay: Compact EPG with "NOW: [Program]"
2. Info button: Toggle full EPG display
3. Full EPG: Two cards showing Now and Next programs

## Summary

This simplified EPG implementation provides:
- ✅ Parse tvg-id from M3U files
- ✅ Display "Now Playing" and "Next" placeholders
- ✅ Graceful degradation when no data
- ✅ Visual UI in player screen
- ✅ Extensible architecture for future EPG sources
- ✅ Comprehensive test coverage

The feature is production-ready for IPTV apps where EPG data may not be available, with clear extension points for adding real EPG integration later.

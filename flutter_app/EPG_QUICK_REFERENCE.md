# EPG Feature - Quick Reference Guide

## 🚀 Quick Start

### Display EPG Placeholder (No Data Available)

```dart
// Full display
EpgDisplay.placeholder()

// Compact display
CompactEpgDisplay.placeholder()
```

### Display EPG with Real Data

```dart
final channelEpg = ChannelEpg(
  channelId: channel.tvgId ?? channel.name,
  channelName: channel.name,
  programs: [...], // List of EpgInfo
);

// Full display
EpgDisplay.fromChannelEpg(channelEpg)

// Compact display
CompactEpgDisplay.fromChannelEpg(channelEpg)
```

## 📦 Import Statements

```dart
import 'package:flutter_app/models/epg_info.dart';
import 'package:flutter_app/widgets/epg_display.dart';
```

## 🏗️ Data Models

### EpgInfo - Single Program

```dart
EpgInfo(
  programTitle: 'News Hour',
  description: 'Breaking news',      // optional
  startTime: DateTime(...),
  endTime: DateTime(...),
  category: 'News',                  // optional
)

// Placeholder
EpgInfo.placeholder(isNow: true)   // Current program
EpgInfo.placeholder(isNow: false)  // Next program
```

### ChannelEpg - Channel Schedule

```dart
ChannelEpg(
  channelId: 'cnn',
  channelName: 'CNN',
  programs: [epg1, epg2, epg3],
)

// Placeholder
ChannelEpg.placeholder(
  channelId: 'cnn',
  channelName: 'CNN',
)
```

## 🎨 Widget Components

### EpgDisplay (Full)

Shows detailed "Now" and "Next" program cards with:
- Program titles and descriptions
- Time ranges and durations
- Categories
- Progress bars for live content
- Status indicators

```dart
EpgDisplay.placeholder()
EpgDisplay.fromChannelEpg(channelEpg)
EpgDisplay(
  nowPlaying: epgInfo1,
  nextProgram: epgInfo2,
  isDataAvailable: true,
)
```

### CompactEpgDisplay (Minimal)

Compact display for overlays:
- Current program title
- Time remaining
- Status indicator

```dart
CompactEpgDisplay.placeholder()
CompactEpgDisplay.fromChannelEpg(channelEpg)
CompactEpgDisplay(
  nowPlaying: epgInfo,
  isDataAvailable: true,
)
```

## 🔄 Channel Model Updates

### tvgId Field

```dart
// Parse from M3U
Channel.fromM3ULine(
  '#EXTINF:-1 tvg-id="cnn" tvg-logo="..." group-title="News",CNN',
  'http://...'
)
// Result: channel.tvgId = 'cnn'

// Create manually
Channel(
  name: 'CNN',
  url: 'http://...',
  tvgId: 'cnn',  // EPG reference ID
)

// JSON
channel.toJson()    // includes 'tvgId'
Channel.fromJson()  // supports 'tvgId' or 'tvg_id'
```

## 📝 Computed Properties

### EpgInfo Properties

```dart
epgInfo.progress             // 0.0 - 1.0
epgInfo.isCurrentlyAiring    // bool
epgInfo.remainingMinutes     // int
epgInfo.timeRange            // "14:00 - 15:30"
epgInfo.duration             // "1h 30min"
```

### ChannelEpg Properties

```dart
channelEpg.currentProgram    // EpgInfo?
channelEpg.nextProgram       // EpgInfo?
channelEpg.getCurrentAndNext()  // Map<String, EpgInfo>
```

## 🎬 Player Integration

```dart
// In player screen state
bool _showEpgInfo = false;

void _toggleEpgInfo() {
  setState(() => _showEpgInfo = !_showEpgInfo);
  
  if (_showEpgInfo) {
    // Auto-hide after 10 seconds
    Future.delayed(Duration(seconds: 10), () {
      if (mounted && _showEpgInfo) {
        setState(() => _showEpgInfo = false);
      }
    });
  }
}

// In build method
Stack(
  children: [
    // Video player
    
    // Top overlay - compact EPG
    Positioned(
      top: 0,
      child: CompactEpgDisplay.placeholder(),
    ),
    
    // Info button
    IconButton(
      icon: Icon(Icons.info_outline),
      onPressed: _toggleEpgInfo,
    ),
    
    // Full EPG overlay
    if (_showEpgInfo)
      Positioned(
        bottom: 100,
        left: 16,
        right: 16,
        child: EpgDisplay.placeholder(),
      ),
  ],
)
```

## 🧪 Testing

```dart
// Model tests
test('creates EPG info', () {
  final epg = EpgInfo(
    programTitle: 'News',
    startTime: DateTime(...),
    endTime: DateTime(...),
  );
  expect(epg.programTitle, 'News');
});

// Widget tests
testWidgets('displays EPG widget', (tester) async {
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: EpgDisplay.placeholder(),
      ),
    ),
  );
  
  expect(find.text('SCHEDULE'), findsOneWidget);
  expect(find.text('NOW PLAYING'), findsOneWidget);
});
```

## 🔮 Future Integration (Example)

```dart
// EPG Service (not implemented yet)
Future<ChannelEpg?> fetchEpg(String tvgId) async {
  // Fetch from XMLTV, API, etc.
  return channelEpg;
}

// Use in widget
FutureBuilder<ChannelEpg?>(
  future: fetchEpg(channel.tvgId ?? ''),
  builder: (context, snapshot) {
    if (snapshot.hasData) {
      return EpgDisplay.fromChannelEpg(snapshot.data!);
    }
    return EpgDisplay.placeholder();
  },
)
```

## 🎯 Common Use Cases

### 1. Show EPG in Player
```dart
CompactEpgDisplay.placeholder()  // Always visible in top bar
```

### 2. Show Detailed EPG on Demand
```dart
// Toggle with button
EpgDisplay.placeholder()
```

### 3. Channel List Preview
```dart
// In list tile
CompactEpgDisplay.placeholder()
```

### 4. Parse M3U with EPG ID
```dart
final channel = Channel.fromM3ULine(m3uLine, url);
print(channel.tvgId);  // 'cnn' or null
```

### 5. Create Sample EPG Data
```dart
final now = DateTime.now();
final epg = EpgInfo(
  programTitle: 'News Hour',
  startTime: now.subtract(Duration(minutes: 30)),
  endTime: now.add(Duration(minutes: 30)),
);
```

## 🎨 Visual Elements

### Color Coding
- **Red**: NOW PLAYING label
- **Blue**: NEXT label
- **Green**: Real EPG data indicator
- **Grey**: Placeholder data indicator

### Icons
- `Icons.schedule`: EPG schedule icon
- `Icons.info_outline`: Info/unavailable data tooltip
- `Icons.category_outlined`: Program category

## 📱 Responsive Design

- **Full Display**: Suitable for tablets and landscape
- **Compact Display**: Optimized for mobile and overlays
- **Auto-hide**: Prevents video obstruction

## ⚡ Performance Tips

1. **Lazy Loading**: Only create EPG when needed
2. **Caching**: Cache fetched EPG data
3. **Placeholders**: Always have fallback
4. **Auto-hide**: Don't keep overlays permanently visible

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| EPG not showing | Check imports, verify widget placement |
| tvgId is null | M3U missing `tvg-id` attribute |
| Widget overflow | Use SingleChildScrollView wrapper |
| Colors not visible | Check theme compatibility |
| Auto-hide not working | Verify mounted check in delayed callback |

## 📚 Related Files

- **Models**: `lib/models/epg_info.dart`
- **Widgets**: `lib/widgets/epg_display.dart`
- **Channel**: `lib/models/channel.dart`
- **Player**: `lib/screens/player_screen.dart`
- **Examples**: `lib/epg_examples.dart`
- **Tests**: `test/models/epg_info_test.dart`, `test/widgets/epg_display_test.dart`
- **Docs**: `EPG_FEATURE_README.md`, `ISSUE_20_IMPLEMENTATION_SUMMARY.md`

## 🔗 Related Issues

- **Issue #20**: EPG/schedule info ✅ IMPLEMENTED
- **Issue #19**: DVR/Recording (future)
- **Issue #12**: Category filtering

## 📊 Test Coverage

- ✅ 32 model tests (EpgInfo, ChannelEpg)
- ✅ 10 widget tests (EpgDisplay, CompactEpgDisplay)
- ✅ 6 channel tests (tvgId field)
- ✅ **Total: 48 tests**

## ✨ Key Features

✅ Parse tvg-id from M3U files  
✅ Display "Now Playing" and "Next" placeholders  
✅ Show EPG data when available  
✅ Graceful degradation when not available  
✅ Progress bars for live content  
✅ Time and duration formatting  
✅ Compact and full display modes  
✅ Player screen integration  
✅ Comprehensive test coverage  

---

**Version**: 1.0.0  
**Issue**: #20 - Add channel EPG/schedule info (simplified version)  
**Status**: ✅ COMPLETE

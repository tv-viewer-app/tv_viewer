# Firebase Services - Quick Reference

## 🚀 Quick Start

### Import Services
```dart
import 'package:tv_viewer/services/analytics_service.dart';
import 'package:tv_viewer/services/crashlytics_service.dart';
import 'package:tv_viewer/di/service_locator.dart';
```

### Get Service Instances
```dart
// Via dependency injection (recommended)
final analytics = getIt<AnalyticsService>();
final crashlytics = getIt<CrashlyticsService>();

// Or directly
final analytics = AnalyticsService.instance;
final crashlytics = CrashlyticsService.instance;
```

---

## 📊 Analytics - Common Use Cases

### Track App Start
```dart
await analytics.logAppStart();
```

### Track Screen Views
```dart
await analytics.logScreenView(
  screenName: 'ChannelList',
  screenClass: 'ChannelListScreen',
);
```

### Track Channel Play
```dart
await analytics.logChannelPlay(
  channelName: 'CNN International',
  category: 'News',
  country: 'USA',
  mediaType: 'Live TV',
);
```

### Track Playlist Scanning
```dart
// Start
await analytics.logScanStart(
  playlistUrl: 'https://example.com/playlist.m3u',
  playlistName: 'My Playlist',
);

// Complete
await analytics.logScanComplete(
  playlistUrl: 'https://example.com/playlist.m3u',
  channelCount: 150,
  success: true,
  durationMs: 2500,
);
```

### Track Filter Usage
```dart
await analytics.logFilterApplied(
  filterType: 'category',
  filterValue: 'Sports',
);
```

### Track Errors
```dart
await analytics.logError(
  errorMessage: 'Failed to load stream',
  errorCode: 'STREAM_ERROR',
  context: 'PlayerScreen',
);
```

### Track Favorites
```dart
await analytics.logFavoritesToggled(
  channelName: 'ESPN',
  isFavorite: true,
);
```

### Track Settings Changes
```dart
await analytics.logSettingsChanged(
  settingKey: 'theme',
  settingValue: 'dark',
);
```

### Custom Events
```dart
await analytics.logEvent(
  name: 'custom_event',
  parameters: {
    'custom_param': 'value',
    'timestamp': DateTime.now().toIso8601String(),
  },
);
```

### Set User Properties
```dart
await analytics.setUserId('user_12345');
await analytics.setUserProperty(name: 'user_type', value: 'premium');
```

---

## 🔥 Crashlytics - Common Use Cases

### Record Non-Fatal Error
```dart
try {
  await loadChannel(url);
} catch (e, stack) {
  await crashlytics.recordError(
    e,
    stack,
    reason: 'Failed to load channel',
    fatal: false,
  );
}
```

### Record Fatal Error
```dart
await crashlytics.recordError(
  exception,
  stackTrace,
  reason: 'Critical error',
  fatal: true,
);
```

### Add Context to Crashes
```dart
await crashlytics.setCustomKey('playlist_url', currentPlaylist);
await crashlytics.setCustomKey('channel_count', channels.length.toString());
await crashlytics.setCustomKey('screen', 'PlayerScreen');
```

### Set User Identifier
```dart
await crashlytics.setUserIdentifier('user_12345');
```

### Log Breadcrumbs
```dart
await crashlytics.log('Starting channel scan...');
await crashlytics.log('Found 150 channels');
await crashlytics.log('Applying filters...');
```

### Enable/Disable Crash Collection
```dart
await crashlytics.setCrashlyticsCollectionEnabled(true);
```

---

## 🎯 Common Patterns

### Pattern 1: Track Screen in StatefulWidget
```dart
class MyScreen extends StatefulWidget {
  @override
  State<MyScreen> createState() => _MyScreenState();
}

class _MyScreenState extends State<MyScreen> {
  final _analytics = getIt<AnalyticsService>();
  final _crashlytics = getIt<CrashlyticsService>();
  
  @override
  void initState() {
    super.initState();
    
    // Track screen view
    _analytics.logScreenView(screenName: 'MyScreen');
    
    // Set crash context
    _crashlytics.setCustomKey('screen', 'MyScreen');
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(/* ... */);
  }
}
```

### Pattern 2: Track User Action
```dart
Future<void> _onButtonPress() async {
  final analytics = getIt<AnalyticsService>();
  
  await analytics.logEvent(
    name: 'button_pressed',
    parameters: {'button_name': 'play_channel'},
  );
  
  // Perform action...
}
```

### Pattern 3: Error Handling with Context
```dart
Future<void> loadData() async {
  final crashlytics = getIt<CrashlyticsService>();
  final analytics = getIt<AnalyticsService>();
  
  // Add context before operation
  await crashlytics.setCustomKey('operation', 'loadData');
  await crashlytics.log('Starting data load...');
  
  try {
    final data = await fetchData();
    await crashlytics.log('Data loaded successfully');
    
  } catch (e, stack) {
    // Record error
    await crashlytics.recordError(
      e,
      stack,
      reason: 'Failed to load data',
    );
    
    // Track in analytics
    await analytics.logError(
      errorMessage: e.toString(),
      context: 'loadData',
    );
    
    rethrow;
  }
}
```

### Pattern 4: Track Timed Operations
```dart
Future<void> scanPlaylist(String url) async {
  final analytics = getIt<AnalyticsService>();
  final startTime = DateTime.now();
  
  try {
    // Start
    await analytics.logScanStart(playlistUrl: url);
    
    // Perform operation
    final channels = await performScan(url);
    
    // Complete
    final duration = DateTime.now().difference(startTime);
    await analytics.logScanComplete(
      playlistUrl: url,
      channelCount: channels.length,
      success: true,
      durationMs: duration.inMilliseconds,
    );
    
  } catch (e, stack) {
    // Track failure
    final duration = DateTime.now().difference(startTime);
    await analytics.logScanComplete(
      playlistUrl: url,
      channelCount: 0,
      success: false,
      durationMs: duration.inMilliseconds,
    );
    
    rethrow;
  }
}
```

---

## 📋 Event Names Reference

| Event | Description |
|-------|-------------|
| `app_start` | App launched |
| `screen_view` | Screen viewed |
| `channel_play` | Channel played |
| `scan_start` | Playlist scan started |
| `scan_complete` | Playlist scan finished |
| `filter_applied` | Filter used |
| `error_occurred` | Error happened |
| `playlist_added` | Playlist added |
| `playlist_removed` | Playlist removed |
| `favorites_toggled` | Favorite toggled |
| `settings_changed` | Setting changed |
| `help_viewed` | Help accessed |
| `feedback_submitted` | Feedback sent |
| `external_player_launched` | External player used |

---

## 🔑 Parameter Keys Reference

| Parameter | Description |
|-----------|-------------|
| `channel_name` | Channel name |
| `channel_url` | Channel URL |
| `category` | Category name |
| `country` | Country code |
| `media_type` | Media type (Live TV, Radio) |
| `playlist_url` | Playlist URL |
| `playlist_name` | Playlist name |
| `channel_count` | Number of channels |
| `filter_type` | Filter type |
| `filter_value` | Filter value |
| `error_code` | Error code |
| `error_message` | Error message |
| `setting_key` | Setting key |
| `setting_value` | Setting value |
| `help_topic` | Help topic |
| `feedback_type` | Feedback type |
| `player_type` | Player type |
| `duration` | Duration (ms) |
| `success` | Success boolean |

---

## ✅ Best Practices

### DO ✅
- Track meaningful user actions
- Add context to crashes before operations
- Log breadcrumbs for debugging
- Set user identifiers for crash reports
- Track success AND failure states
- Use constants for event names and parameters

### DON'T ❌
- Track personally identifiable information (PII)
- Over-track (every button press)
- Log sensitive data (passwords, tokens)
- Block UI thread waiting for analytics
- Ignore errors in analytics calls

---

## 🔍 Debugging

### Check Service Status
```dart
print('Analytics initialized: ${analytics.isInitialized}');
print('Analytics has Firebase: ${analytics.isFirebaseAvailable}');
print('Crashlytics initialized: ${crashlytics.isInitialized}');
print('Crashlytics has Firebase: ${crashlytics.isFirebaseAvailable}');
```

### Expected Logs (Without Firebase)
```
[Analytics] Running in fallback mode (no Firebase configured)
[Crashlytics] Running in fallback mode (no Firebase configured)
[INFO] [Analytics] Event: app_start
[ERROR] [Crashlytics Fallback] Exception: Test error
```

### Expected Logs (With Firebase)
```
[Analytics] Firebase Analytics initialized successfully
[Crashlytics] Firebase Crashlytics initialized successfully
[DEBUG] [Analytics] Event: app_start
[ERROR] [Crashlytics] Error: Test error
```

---

## 🚨 Testing

### Test Analytics Event
```dart
// In development/debug mode
if (kDebugMode) {
  await analytics.logEvent(
    name: 'test_event',
    parameters: {'test': 'value'},
  );
  print('Test event logged');
}
```

### Test Crashlytics (DEVELOPMENT ONLY!)
```dart
// DO NOT USE IN PRODUCTION!
if (kDebugMode) {
  await crashlytics.recordError(
    Exception('Test error'),
    StackTrace.current,
    reason: 'Testing crash reporting',
  );
}
```

### Test Crash (DEVELOPMENT ONLY!)
```dart
// EXTREMELY DANGEROUS - USE ONLY FOR TESTING
if (kDebugMode) {
  await crashlytics.crash();
}
```

---

## 📚 More Information

- **Full Setup**: See `FIREBASE_SETUP.md`
- **Implementation Details**: See `FIREBASE_IMPLEMENTATION_SUMMARY.md`
- **Examples**: See `lib/services/firebase_services_examples.dart`
- **Service Code**: 
  - `lib/services/analytics_service.dart`
  - `lib/services/crashlytics_service.dart`

---

## ⚡ Quick Commands

### Initialize Services (in main.dart)
```dart
await setupServiceLocator(); // Initializes all services
```

### Track Common Events
```dart
analytics.logAppStart();                                // App start
analytics.logScreenView(screenName: 'Home');           // Screen view
analytics.logChannelPlay(channelName: 'CNN');          // Channel play
analytics.logFilterApplied(                            // Filter
  filterType: 'category', 
  filterValue: 'News'
);
```

### Handle Errors
```dart
try {
  // risky operation
} catch (e, stack) {
  crashlytics.recordError(e, stack, reason: 'Operation failed');
  analytics.logError(errorMessage: e.toString());
}
```

---

**Quick Reference Version**: 1.0  
**Last Updated**: 2024  
**Related Issues**: #24 (Crashlytics), #25 (Analytics)

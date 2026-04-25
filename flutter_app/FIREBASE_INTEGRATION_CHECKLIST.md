# Firebase Services Integration Checklist

This checklist helps you integrate the new Analytics and Crashlytics services into the TV Viewer app.

## ✅ Phase 1: Verify Installation (DONE)

- [x] `lib/services/analytics_service.dart` created
- [x] `lib/services/crashlytics_service.dart` created
- [x] `lib/di/service_locator.dart` updated
- [x] `FIREBASE_SETUP.md` created
- [x] `FIREBASE_IMPLEMENTATION_SUMMARY.md` created
- [x] `FIREBASE_QUICK_REFERENCE.md` created
- [x] `lib/services/firebase_services_examples.dart` created
- [x] No syntax errors

## 📋 Phase 2: Basic Integration (RECOMMENDED)

### 2.1 Update Main App

**File**: `lib/main.dart`

- [ ] Add imports:
  ```dart
  import 'services/analytics_service.dart';
  import 'services/crashlytics_service.dart';
  ```

- [ ] Track app start in `main()`:
  ```dart
  void main() async {
    WidgetsFlutterBinding.ensureInitialized();
    
    // Initialize DI (already calls analytics/crashlytics init)
    await setupServiceLocator();
    
    // Track app start
    await getIt<AnalyticsService>().logAppStart();
    
    runApp(MyApp());
  }
  ```

### 2.2 Add Screen Tracking

**Files**: All screen widgets (`lib/screens/*.dart`)

For each screen, add in `initState()`:

```dart
@override
void initState() {
  super.initState();
  
  final analytics = getIt<AnalyticsService>();
  analytics.logScreenView(
    screenName: 'ScreenName', // e.g., 'ChannelList', 'Player', 'Settings'
    screenClass: runtimeType.toString(),
  );
}
```

**Priority Screens**:
- [ ] `lib/screens/channel_list_screen.dart` - Main screen
- [ ] `lib/screens/player_screen.dart` - Player screen
- [ ] `lib/screens/playlist_manager_screen.dart` - Playlist screen
- [ ] `lib/screens/settings_screen.dart` - Settings screen
- [ ] `lib/screens/favorites_screen.dart` - Favorites screen
- [ ] `lib/screens/help_screen.dart` - Help screen

### 2.3 Add Channel Playback Tracking

**File**: `lib/screens/player_screen.dart`

- [ ] Import services:
  ```dart
  import 'package:tv_viewer/services/analytics_service.dart';
  import 'package:tv_viewer/services/crashlytics_service.dart';
  import 'package:tv_viewer/di/service_locator.dart';
  ```

- [ ] Track channel play:
  ```dart
  Future<void> _playChannel(Channel channel) async {
    final analytics = getIt<AnalyticsService>();
    final crashlytics = getIt<CrashlyticsService>();
    
    try {
      // Add crash context
      await crashlytics.setCustomKey('current_channel', channel.name);
      await crashlytics.setCustomKey('channel_url', channel.url);
      
      // Track analytics
      await analytics.logChannelPlay(
        channelName: channel.name,
        category: channel.category,
        country: channel.country,
        mediaType: channel.mediaType,
      );
      
      // Play channel...
      
    } catch (e, stack) {
      await crashlytics.recordError(e, stack, reason: 'Failed to play channel');
      await analytics.logError(errorMessage: e.toString());
      rethrow;
    }
  }
  ```

### 2.4 Add Playlist Scanning Tracking

**File**: `lib/providers/channel_provider.dart` or `lib/services/m3u_service.dart`

- [ ] Track scan start and complete:
  ```dart
  Future<void> scanPlaylist(String url) async {
    final analytics = getIt<AnalyticsService>();
    final startTime = DateTime.now();
    
    try {
      await analytics.logScanStart(playlistUrl: url);
      
      // Perform scan...
      final channels = await _performScan(url);
      
      final duration = DateTime.now().difference(startTime);
      await analytics.logScanComplete(
        playlistUrl: url,
        channelCount: channels.length,
        success: true,
        durationMs: duration.inMilliseconds,
      );
      
      return channels;
      
    } catch (e, stack) {
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

### 2.5 Add Filter Tracking

**File**: `lib/providers/channel_provider.dart` or wherever filters are applied

- [ ] Track filter usage:
  ```dart
  void setCategory(String? category) {
    final analytics = getIt<AnalyticsService>();
    
    if (category != null) {
      analytics.logFilterApplied(
        filterType: 'category',
        filterValue: category,
      );
    }
    
    // Apply filter...
  }
  
  void setCountry(String? country) {
    final analytics = getIt<AnalyticsService>();
    
    if (country != null) {
      analytics.logFilterApplied(
        filterType: 'country',
        filterValue: country,
      );
    }
    
    // Apply filter...
  }
  ```

### 2.6 Add Favorites Tracking

**File**: `lib/services/favorites_service.dart` or wherever favorites are managed

- [ ] Track favorites toggle:
  ```dart
  Future<void> toggleFavorite(Channel channel) async {
    final analytics = getIt<AnalyticsService>();
    
    final isFavorite = await _toggleFavorite(channel);
    
    await analytics.logFavoritesToggled(
      channelName: channel.name,
      isFavorite: isFavorite,
    );
  }
  ```

### 2.7 Add Error Tracking

**File**: `lib/utils/error_handler.dart` or wherever errors are handled

- [ ] Track errors globally:
  ```dart
  Future<void> handleError(dynamic error, StackTrace? stack) async {
    final crashlytics = getIt<CrashlyticsService>();
    final analytics = getIt<AnalyticsService>();
    
    // Record to crashlytics
    await crashlytics.recordError(
      error,
      stack ?? StackTrace.current,
      reason: 'App error',
    );
    
    // Track in analytics
    await analytics.logError(
      errorMessage: error.toString(),
    );
    
    // Log to file
    logger.error('Error occurred', error, stack);
  }
  ```

## 🔥 Phase 3: Firebase Configuration (OPTIONAL)

**When**: Only when you want remote analytics and crash reporting

**Time Required**: 30 minutes

- [ ] Create Firebase project (see `FIREBASE_SETUP.md`)
- [ ] Download `google-services.json`
- [ ] Add to `android/app/google-services.json`
- [ ] Update `android/build.gradle` (project-level)
- [ ] Update `android/app/build.gradle` (app-level)
- [ ] Update `pubspec.yaml` dependencies:
  ```yaml
  firebase_core: ^2.24.2
  firebase_analytics: ^10.8.0
  firebase_crashlytics: ^3.4.8
  ```
- [ ] Run `flutter pub get`
- [ ] Uncomment Firebase code in `analytics_service.dart`
- [ ] Uncomment Firebase code in `crashlytics_service.dart`
- [ ] Test Firebase initialization
- [ ] Verify events in Firebase Console

## 🧪 Phase 4: Testing

### Test Without Firebase (Current State)

- [ ] Run app: `flutter run`
- [ ] Check logs for:
  ```
  [Analytics] Running in fallback mode (no Firebase configured)
  [Crashlytics] Running in fallback mode (no Firebase configured)
  Service locator initialized successfully
  ```
- [ ] Play a channel
- [ ] Check logs for: `[INFO] [Analytics] Event: channel_play | Params: ...`
- [ ] Trigger an error
- [ ] Check logs for: `[ERROR] [Crashlytics Fallback] ...`

### Test With Firebase (If Enabled)

- [ ] Run app: `flutter run`
- [ ] Check logs for:
  ```
  [Analytics] Firebase Analytics initialized successfully
  [Crashlytics] Firebase Crashlytics initialized successfully
  ```
- [ ] Play a channel
- [ ] Check Firebase Console → Analytics → Events (wait 1-2 hours)
- [ ] Trigger an error
- [ ] Check Firebase Console → Crashlytics → Dashboard (appears in minutes)

## 📊 Phase 5: Monitor & Optimize

### Monitor Key Metrics

In Firebase Console (when enabled):

- [ ] Analytics → Events:
  - Most played channels (`channel_play`)
  - Most used filters (`filter_applied`)
  - Most viewed screens (`screen_view`)
  - Error frequency (`error_occurred`)

- [ ] Crashlytics → Dashboard:
  - Crash-free users percentage
  - Most common crashes
  - Crash trends over time

### Optimize Based on Data

- [ ] Identify most used features → prioritize improvements
- [ ] Identify common errors → fix top issues
- [ ] Identify unused features → consider removing
- [ ] Identify popular categories → enhance experience

## 🎯 Quick Integration (Minimal)

**If you want the absolute minimum integration**:

1. ✅ Services are already created and registered
2. ✅ Add screen tracking to top 3 screens:
   - Channel list screen
   - Player screen
   - Settings screen
3. ✅ Add error tracking to global error handler
4. ✅ Track app start in `main()`

**Time**: 15 minutes  
**Impact**: Basic analytics working without Firebase

## 📝 Integration Examples

### Example 1: Channel List Screen

```dart
class ChannelListScreen extends StatefulWidget {
  @override
  State<ChannelListScreen> createState() => _ChannelListScreenState();
}

class _ChannelListScreenState extends State<ChannelListScreen> {
  final _analytics = getIt<AnalyticsService>();
  
  @override
  void initState() {
    super.initState();
    _analytics.logScreenView(screenName: 'ChannelList');
  }
  
  void _onFilterChanged(String filterType, String filterValue) {
    _analytics.logFilterApplied(
      filterType: filterType,
      filterValue: filterValue,
    );
  }
  
  @override
  Widget build(BuildContext context) {
    // UI code...
  }
}
```

### Example 2: Player Screen

```dart
class PlayerScreen extends StatefulWidget {
  final Channel channel;
  
  const PlayerScreen({required this.channel});
  
  @override
  State<PlayerScreen> createState() => _PlayerScreenState();
}

class _PlayerScreenState extends State<PlayerScreen> {
  final _analytics = getIt<AnalyticsService>();
  final _crashlytics = getIt<CrashlyticsService>();
  
  @override
  void initState() {
    super.initState();
    
    _analytics.logScreenView(screenName: 'Player');
    _crashlytics.setCustomKey('current_channel', widget.channel.name);
    
    _playChannel();
  }
  
  Future<void> _playChannel() async {
    try {
      await _analytics.logChannelPlay(
        channelName: widget.channel.name,
        category: widget.channel.category,
        country: widget.channel.country,
      );
      
      // Play channel...
      
    } catch (e, stack) {
      await _crashlytics.recordError(e, stack);
      await _analytics.logError(errorMessage: e.toString());
    }
  }
  
  @override
  Widget build(BuildContext context) {
    // UI code...
  }
}
```

## ❓ FAQ

**Q: Do I need to integrate now?**  
A: No. Services are already created and working in fallback mode. Integration is optional.

**Q: What happens if I don't integrate?**  
A: App works normally. You just won't track user behavior or crashes.

**Q: What's the minimum integration?**  
A: Track app start in `main()` + screen views in top 3 screens = 15 minutes.

**Q: Do I need Firebase?**  
A: No. Services work without Firebase, logging to local files via `logger_service.dart`.

**Q: When should I enable Firebase?**  
A: When you want remote analytics and crash reports in Firebase Console.

**Q: Will this slow down my app?**  
A: No. Analytics and crash reporting are asynchronous and non-blocking.

**Q: Can I test without Firebase?**  
A: Yes! Services work perfectly without Firebase. All events log to files.

## ✅ Completion Checklist

### Minimum Viable Integration
- [ ] Track app start in `main()`
- [ ] Track 3 main screens
- [ ] Track errors globally
- [ ] Test logs appear

### Recommended Integration
- [ ] Minimum viable integration ✓
- [ ] Track channel playback
- [ ] Track filter usage
- [ ] Track favorites
- [ ] Track playlist scanning
- [ ] Add crash context

### Full Integration
- [ ] Recommended integration ✓
- [ ] Enable Firebase (optional)
- [ ] Track all screens
- [ ] Track all user actions
- [ ] Monitor Firebase Console
- [ ] Optimize based on data

## 📚 Related Files

- `FIREBASE_SETUP.md` - Firebase configuration guide
- `FIREBASE_IMPLEMENTATION_SUMMARY.md` - Implementation details
- `FIREBASE_QUICK_REFERENCE.md` - Quick reference for developers
- `lib/services/firebase_services_examples.dart` - Code examples
- `lib/services/analytics_service.dart` - Analytics service
- `lib/services/crashlytics_service.dart` - Crashlytics service

---

**Last Updated**: 2024  
**Status**: Ready for integration  
**Required**: No (Optional)  
**Firebase Required**: No (Optional)

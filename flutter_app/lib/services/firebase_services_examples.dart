/// Example: Using Analytics and Crashlytics Services
/// 
/// This file demonstrates how to use the analytics and crashlytics services
/// in your application. Copy these patterns into your actual code.

import 'package:flutter/material.dart';
import 'package:tv_viewer/services/analytics_service.dart';
import 'package:tv_viewer/services/crashlytics_service.dart';
import 'package:tv_viewer/di/service_locator.dart';

// ============================================================================
// Example 1: Track screen views
// ============================================================================

class ExampleChannelListScreen extends StatefulWidget {
  const ExampleChannelListScreen({Key? key}) : super(key: key);

  @override
  State<ExampleChannelListScreen> createState() => _ExampleChannelListScreenState();
}

class _ExampleChannelListScreenState extends State<ExampleChannelListScreen> {
  // Inject analytics service
  final _analytics = getIt<AnalyticsService>();
  
  @override
  void initState() {
    super.initState();
    
    // Track screen view
    _analytics.logScreenView(
      screenName: 'ChannelList',
      screenClass: 'ExampleChannelListScreen',
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Channels')),
      body: const Center(child: Text('Channel List')),
    );
  }
}

// ============================================================================
// Example 2: Track user actions
// ============================================================================

class ExampleChannelPlayer {
  final _analytics = getIt<AnalyticsService>();
  final _crashlytics = getIt<CrashlyticsService>();
  
  Future<void> playChannel({
    required String channelName,
    required String channelUrl,
    String? category,
    String? country,
  }) async {
    try {
      // Add context for crash reports
      await _crashlytics.setCustomKey('current_channel', channelName);
      await _crashlytics.setCustomKey('channel_url', channelUrl);
      await _crashlytics.log('Starting playback: $channelName');
      
      // Track analytics event
      await _analytics.logChannelPlay(
        channelName: channelName,
        category: category,
        country: country,
        mediaType: 'Live TV',
      );
      
      // Simulate channel playback
      print('Playing $channelName from $channelUrl');
      
    } catch (e, stack) {
      // Record error
      await _crashlytics.recordError(
        e,
        stack,
        reason: 'Failed to play channel: $channelName',
      );
      
      await _analytics.logError(
        errorMessage: e.toString(),
        errorCode: 'CHANNEL_PLAY_ERROR',
        context: 'playChannel',
      );
      
      rethrow;
    }
  }
}

// ============================================================================
// Example 3: Track playlist operations
// ============================================================================

class ExamplePlaylistManager {
  final _analytics = getIt<AnalyticsService>();
  final _crashlytics = getIt<CrashlyticsService>();
  
  Future<List<dynamic>> scanPlaylist(String playlistUrl) async {
    final startTime = DateTime.now();
    
    try {
      // Track scan start
      await _analytics.logScanStart(
        playlistUrl: playlistUrl,
        playlistName: 'My Playlist',
      );
      
      // Add breadcrumb
      await _crashlytics.log('Starting playlist scan: $playlistUrl');
      
      // Simulate playlist scanning
      await Future.delayed(const Duration(seconds: 2));
      final channels = <dynamic>[]; // Simulated channels
      
      // Track scan completion
      final duration = DateTime.now().difference(startTime);
      await _analytics.logScanComplete(
        playlistUrl: playlistUrl,
        channelCount: channels.length,
        success: true,
        durationMs: duration.inMilliseconds,
      );
      
      return channels;
      
    } catch (e, stack) {
      // Track failed scan
      final duration = DateTime.now().difference(startTime);
      await _analytics.logScanComplete(
        playlistUrl: playlistUrl,
        channelCount: 0,
        success: false,
        durationMs: duration.inMilliseconds,
      );
      
      // Record error
      await _crashlytics.recordError(
        e,
        stack,
        reason: 'Playlist scan failed',
      );
      
      rethrow;
    }
  }
  
  Future<void> addPlaylist(String playlistUrl, String playlistName) async {
    try {
      // Track playlist added
      await _analytics.logPlaylistAdded(
        playlistUrl: playlistUrl,
        playlistName: playlistName,
      );
      
      // Add context
      await _crashlytics.setCustomKey('last_playlist_added', playlistUrl);
      
    } catch (e, stack) {
      await _crashlytics.recordError(e, stack, reason: 'Failed to add playlist');
      rethrow;
    }
  }
  
  Future<void> removePlaylist(String playlistUrl) async {
    try {
      // Track playlist removed
      await _analytics.logPlaylistRemoved(playlistUrl: playlistUrl);
      
    } catch (e, stack) {
      await _crashlytics.recordError(e, stack, reason: 'Failed to remove playlist');
      rethrow;
    }
  }
}

// ============================================================================
// Example 4: Track favorites
// ============================================================================

class ExampleFavoritesManager {
  final _analytics = getIt<AnalyticsService>();
  
  Future<void> toggleFavorite(String channelName, bool isFavorite) async {
    await _analytics.logFavoritesToggled(
      channelName: channelName,
      isFavorite: isFavorite,
    );
  }
}

// ============================================================================
// Example 5: Track filter usage
// ============================================================================

class ExampleFilterManager {
  final _analytics = getIt<AnalyticsService>();
  
  Future<void> applyCategoryFilter(String category) async {
    await _analytics.logFilterApplied(
      filterType: 'category',
      filterValue: category,
    );
  }
  
  Future<void> applyCountryFilter(String country) async {
    await _analytics.logFilterApplied(
      filterType: 'country',
      filterValue: country,
    );
  }
  
  Future<void> applyMediaTypeFilter(String mediaType) async {
    await _analytics.logFilterApplied(
      filterType: 'media_type',
      filterValue: mediaType,
    );
  }
}

// ============================================================================
// Example 6: Track settings changes
// ============================================================================

class ExampleSettingsManager {
  final _analytics = getIt<AnalyticsService>();
  
  Future<void> changeTheme(String theme) async {
    await _analytics.logSettingsChanged(
      settingKey: 'theme',
      settingValue: theme,
    );
  }
  
  Future<void> changeVideoQuality(String quality) async {
    await _analytics.logSettingsChanged(
      settingKey: 'video_quality',
      settingValue: quality,
    );
  }
  
  Future<void> toggleAutoplay(bool enabled) async {
    await _analytics.logSettingsChanged(
      settingKey: 'autoplay',
      settingValue: enabled,
    );
  }
}

// ============================================================================
// Example 7: Track help and feedback
// ============================================================================

class ExampleHelpAndFeedback {
  final _analytics = getIt<AnalyticsService>();
  
  Future<void> viewHelp(String helpTopic) async {
    await _analytics.logHelpViewed(helpTopic: helpTopic);
  }
  
  Future<void> submitFeedback(String feedbackType) async {
    await _analytics.logFeedbackSubmitted(
      feedbackType: feedbackType,
      category: 'General',
    );
  }
}

// ============================================================================
// Example 8: Track external player launch
// ============================================================================

class ExampleExternalPlayerLauncher {
  final _analytics = getIt<AnalyticsService>();
  
  Future<void> launchExternalPlayer(String playerType, String channelName) async {
    await _analytics.logExternalPlayerLaunched(
      playerType: playerType,
      channelName: channelName,
    );
  }
}

// ============================================================================
// Example 9: Error handling with crashlytics
// ============================================================================

class ExampleErrorHandler {
  final _crashlytics = getIt<CrashlyticsService>();
  final _analytics = getIt<AnalyticsService>();
  
  Future<void> handleError(
    dynamic error,
    StackTrace stack, {
    String? context,
    bool fatal = false,
  }) async {
    // Record to crashlytics
    await _crashlytics.recordError(
      error,
      stack,
      reason: context,
      fatal: fatal,
    );
    
    // Track in analytics
    await _analytics.logError(
      errorMessage: error.toString(),
      context: context,
    );
  }
  
  Future<void> addCrashContext({
    required String key,
    required dynamic value,
  }) async {
    await _crashlytics.setCustomKey(key, value);
  }
  
  Future<void> setUserIdentifier(String userId) async {
    await _crashlytics.setUserIdentifier(userId);
  }
}

// ============================================================================
// Example 10: App initialization
// ============================================================================

Future<void> exampleAppInitialization() async {
  final analytics = getIt<AnalyticsService>();
  final crashlytics = getIt<CrashlyticsService>();
  
  // Check if Firebase is available
  if (analytics.isFirebaseAvailable) {
    print('✅ Firebase Analytics enabled');
  } else {
    print('⚠️ Firebase Analytics in fallback mode (using logger)');
  }
  
  if (crashlytics.isFirebaseAvailable) {
    print('✅ Firebase Crashlytics enabled');
  } else {
    print('⚠️ Firebase Crashlytics in fallback mode (using logger)');
  }
  
  // Track app start
  await analytics.logAppStart();
  
  // Set initial crash context
  await crashlytics.setCustomKey('app_version', '1.9.0');
  await crashlytics.setCustomKey('environment', 'production');
}

// ============================================================================
// Example 11: Widget with analytics
// ============================================================================

class ExampleAnalyticsWidget extends StatefulWidget {
  const ExampleAnalyticsWidget({Key? key}) : super(key: key);

  @override
  State<ExampleAnalyticsWidget> createState() => _ExampleAnalyticsWidgetState();
}

class _ExampleAnalyticsWidgetState extends State<ExampleAnalyticsWidget> {
  final _analytics = getIt<AnalyticsService>();
  final _crashlytics = getIt<CrashlyticsService>();
  
  @override
  void initState() {
    super.initState();
    
    // Track screen view
    _analytics.logScreenView(screenName: 'ExampleScreen');
    
    // Set crash context
    _crashlytics.setCustomKey('screen', 'ExampleScreen');
  }
  
  void _handleButtonPress(String buttonName) async {
    // Track button press
    await _analytics.logEvent(
      name: 'button_pressed',
      parameters: {'button_name': buttonName},
    );
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Example Analytics')),
      body: Center(
        child: ElevatedButton(
          onPressed: () => _handleButtonPress('example_button'),
          child: const Text('Press Me'),
        ),
      ),
    );
  }
}

// ============================================================================
// Example 12: Custom analytics event
// ============================================================================

class ExampleCustomEvent {
  final _analytics = getIt<AnalyticsService>();
  
  Future<void> trackCustomEvent({
    required String eventName,
    Map<String, dynamic>? parameters,
  }) async {
    await _analytics.logEvent(
      name: eventName,
      parameters: parameters,
    );
  }
  
  Future<void> trackVideoPlayback({
    required String channelName,
    required int duration,
    required String quality,
  }) async {
    await trackCustomEvent(
      eventName: 'video_playback',
      parameters: {
        'channel_name': channelName,
        'duration_seconds': duration,
        'quality': quality,
        'timestamp': DateTime.now().toIso8601String(),
      },
    );
  }
}

// ============================================================================
// Example 13: Set user properties
// ============================================================================

class ExampleUserProperties {
  final _analytics = getIt<AnalyticsService>();
  
  Future<void> setUserProperties({
    String? userId,
    String? userType,
    String? preferredLanguage,
  }) async {
    if (userId != null) {
      await _analytics.setUserId(userId);
    }
    
    if (userType != null) {
      await _analytics.setUserProperty(
        name: 'user_type',
        value: userType,
      );
    }
    
    if (preferredLanguage != null) {
      await _analytics.setUserProperty(
        name: 'preferred_language',
        value: preferredLanguage,
      );
    }
  }
}

// ============================================================================
// Testing the services
// ============================================================================

void main() async {
  // Note: In real app, this would be in your actual main.dart
  // This is just for demonstration
  
  print('=== Firebase Services Examples ===\n');
  
  // Example 1: Check service status
  print('Service Status:');
  final analytics = AnalyticsService.instance;
  final crashlytics = CrashlyticsService.instance;
  
  await analytics.initialize();
  await crashlytics.initialize();
  
  print('Analytics initialized: ${analytics.isInitialized}');
  print('Analytics Firebase available: ${analytics.isFirebaseAvailable}');
  print('Crashlytics initialized: ${crashlytics.isInitialized}');
  print('Crashlytics Firebase available: ${crashlytics.isFirebaseAvailable}');
  
  // Example 2: Track events
  print('\n=== Tracking Events ===');
  await analytics.logAppStart();
  await analytics.logChannelPlay(channelName: 'Example Channel');
  await analytics.logFilterApplied(filterType: 'category', filterValue: 'News');
  
  // Example 3: Record error
  print('\n=== Recording Error ===');
  try {
    throw Exception('Example error');
  } catch (e, stack) {
    await crashlytics.recordError(e, stack, reason: 'Testing error reporting');
  }
  
  print('\n✅ Examples complete! Check logs for output.');
}

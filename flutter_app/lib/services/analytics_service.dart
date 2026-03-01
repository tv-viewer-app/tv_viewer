import 'package:flutter/foundation.dart';
import '../utils/logger_service.dart';

/// Analytics event names
class AnalyticsEvents {
  static const String appStart = 'app_start';
  static const String channelPlay = 'channel_play';
  static const String scanStart = 'scan_start';
  static const String scanComplete = 'scan_complete';
  static const String filterApplied = 'filter_applied';
  static const String errorOccurred = 'error_occurred';
  static const String playlistAdded = 'playlist_added';
  static const String playlistRemoved = 'playlist_removed';
  static const String favoritesToggled = 'favorites_toggled';
  static const String settingsChanged = 'settings_changed';
  static const String helpViewed = 'help_viewed';
  static const String feedbackSubmitted = 'feedback_submitted';
  static const String externalPlayerLaunched = 'external_player_launched';
}

/// Analytics parameter keys
class AnalyticsParameters {
  static const String channelName = 'channel_name';
  static const String channelUrl = 'channel_url';
  static const String category = 'category';
  static const String country = 'country';
  static const String mediaType = 'media_type';
  static const String playlistUrl = 'playlist_url';
  static const String playlistName = 'playlist_name';
  static const String channelCount = 'channel_count';
  static const String filterType = 'filter_type';
  static const String filterValue = 'filter_value';
  static const String errorCode = 'error_code';
  static const String errorMessage = 'error_message';
  static const String settingKey = 'setting_key';
  static const String settingValue = 'setting_value';
  static const String helpTopic = 'help_topic';
  static const String feedbackType = 'feedback_type';
  static const String playerType = 'player_type';
  static const String duration = 'duration';
  static const String success = 'success';
}

/// Analytics service that works with or without Firebase
/// 
/// When Firebase is not configured, falls back to logger_service.dart
/// This allows the app to function without Firebase setup
class AnalyticsService {
  static AnalyticsService? _instance;
  static AnalyticsService get instance => _instance ??= AnalyticsService._();
  
  AnalyticsService._();
  
  bool _isInitialized = false;
  bool _firebaseAvailable = false;
  final LoggerService _logger = LoggerService.instance;
  
  // Firebase Analytics instance (will be null if Firebase not configured)
  // ignore: unused_field
  dynamic _analytics;
  
  /// Initialize analytics service
  /// 
  /// Checks if Firebase is configured and available
  /// Falls back to logger if Firebase is not set up
  Future<void> initialize() async {
    if (_isInitialized) return;
    
    try {
      // Try to initialize Firebase Analytics
      // This will fail gracefully if Firebase is not configured
      _firebaseAvailable = await _initializeFirebase();
      
      if (_firebaseAvailable) {
        _logger.info('[Analytics] Firebase Analytics initialized successfully');
      } else {
        _logger.info('[Analytics] Running in fallback mode (no Firebase configured)');
      }
      
      _isInitialized = true;
    } catch (e) {
      _logger.warning('[Analytics] Failed to initialize Firebase Analytics, using fallback mode', e);
      _firebaseAvailable = false;
      _isInitialized = true;
    }
  }
  
  /// Try to initialize Firebase Analytics
  /// Returns true if successful, false otherwise
  Future<bool> _initializeFirebase() async {
    try {
      // Check if Firebase core is available
      // This will be implemented when Firebase is set up
      // For now, return false to use fallback mode
      
      // Uncomment when Firebase is configured:
      // await Firebase.initializeApp();
      // _analytics = FirebaseAnalytics.instance;
      // return true;
      
      return false;
    } catch (e) {
      debugPrint('[Analytics] Firebase not available: $e');
      return false;
    }
  }
  
  /// Log an analytics event
  /// 
  /// If Firebase is available, logs to Firebase Analytics
  /// Otherwise, logs to logger_service.dart
  Future<void> logEvent({
    required String name,
    Map<String, dynamic>? parameters,
  }) async {
    if (!_isInitialized) {
      await initialize();
    }
    
    try {
      if (_firebaseAvailable && _analytics != null) {
        // Log to Firebase Analytics
        // await _analytics.logEvent(name: name, parameters: parameters);
        _logger.debug('[Analytics] Event: $name ${parameters != null ? parameters.toString() : ''}');
      } else {
        // Fallback: Log to logger service
        final params = parameters != null ? ' | Params: ${parameters.toString()}' : '';
        _logger.info('[Analytics] Event: $name$params');
      }
    } catch (e) {
      _logger.warning('[Analytics] Failed to log event: $name', e);
    }
  }
  
  /// Set user property
  /// 
  /// Useful for segmenting analytics by user characteristics
  Future<void> setUserProperty({
    required String name,
    required String? value,
  }) async {
    if (!_isInitialized) {
      await initialize();
    }
    
    try {
      if (_firebaseAvailable && _analytics != null) {
        // Set Firebase user property
        // await _analytics.setUserProperty(name: name, value: value);
        _logger.debug('[Analytics] User property: $name = $value');
      } else {
        // Fallback: Log to logger service
        _logger.info('[Analytics] User property: $name = $value');
      }
    } catch (e) {
      _logger.warning('[Analytics] Failed to set user property: $name', e);
    }
  }
  
  /// Set user ID for analytics
  Future<void> setUserId(String? userId) async {
    if (!_isInitialized) {
      await initialize();
    }
    
    try {
      if (_firebaseAvailable && _analytics != null) {
        // Set Firebase user ID
        // await _analytics.setUserId(id: userId);
        _logger.debug('[Analytics] User ID set: $userId');
      } else {
        // Fallback: Log to logger service
        _logger.info('[Analytics] User ID set: $userId');
      }
    } catch (e) {
      _logger.warning('[Analytics] Failed to set user ID', e);
    }
  }
  
  /// Log screen view
  Future<void> logScreenView({
    required String screenName,
    String? screenClass,
  }) async {
    await logEvent(
      name: 'screen_view',
      parameters: {
        'screen_name': screenName,
        if (screenClass != null) 'screen_class': screenClass,
      },
    );
  }
  
  // Convenience methods for common events
  
  /// Log app start event
  Future<void> logAppStart() async {
    await logEvent(name: AnalyticsEvents.appStart);
  }
  
  /// Log channel play event
  Future<void> logChannelPlay({
    required String channelName,
    String? category,
    String? country,
    String? mediaType,
  }) async {
    await logEvent(
      name: AnalyticsEvents.channelPlay,
      parameters: {
        AnalyticsParameters.channelName: channelName,
        if (category != null) AnalyticsParameters.category: category,
        if (country != null) AnalyticsParameters.country: country,
        if (mediaType != null) AnalyticsParameters.mediaType: mediaType,
      },
    );
  }
  
  /// Log channel scan start
  Future<void> logScanStart({
    required String playlistUrl,
    String? playlistName,
  }) async {
    await logEvent(
      name: AnalyticsEvents.scanStart,
      parameters: {
        AnalyticsParameters.playlistUrl: playlistUrl,
        if (playlistName != null) AnalyticsParameters.playlistName: playlistName,
      },
    );
  }
  
  /// Log channel scan complete
  Future<void> logScanComplete({
    required String playlistUrl,
    required int channelCount,
    required bool success,
    int? durationMs,
  }) async {
    await logEvent(
      name: AnalyticsEvents.scanComplete,
      parameters: {
        AnalyticsParameters.playlistUrl: playlistUrl,
        AnalyticsParameters.channelCount: channelCount,
        AnalyticsParameters.success: success,
        if (durationMs != null) AnalyticsParameters.duration: durationMs,
      },
    );
  }
  
  /// Log filter applied
  Future<void> logFilterApplied({
    required String filterType,
    required String filterValue,
  }) async {
    await logEvent(
      name: AnalyticsEvents.filterApplied,
      parameters: {
        AnalyticsParameters.filterType: filterType,
        AnalyticsParameters.filterValue: filterValue,
      },
    );
  }
  
  /// Log error occurred
  Future<void> logError({
    required String errorMessage,
    String? errorCode,
    String? context,
  }) async {
    await logEvent(
      name: AnalyticsEvents.errorOccurred,
      parameters: {
        AnalyticsParameters.errorMessage: errorMessage,
        if (errorCode != null) AnalyticsParameters.errorCode: errorCode,
        if (context != null) 'context': context,
      },
    );
  }
  
  /// Log playlist added
  Future<void> logPlaylistAdded({
    required String playlistUrl,
    String? playlistName,
  }) async {
    await logEvent(
      name: AnalyticsEvents.playlistAdded,
      parameters: {
        AnalyticsParameters.playlistUrl: playlistUrl,
        if (playlistName != null) AnalyticsParameters.playlistName: playlistName,
      },
    );
  }
  
  /// Log playlist removed
  Future<void> logPlaylistRemoved({
    required String playlistUrl,
  }) async {
    await logEvent(
      name: AnalyticsEvents.playlistRemoved,
      parameters: {
        AnalyticsParameters.playlistUrl: playlistUrl,
      },
    );
  }
  
  /// Log favorites toggle
  Future<void> logFavoritesToggled({
    required String channelName,
    required bool isFavorite,
  }) async {
    await logEvent(
      name: AnalyticsEvents.favoritesToggled,
      parameters: {
        AnalyticsParameters.channelName: channelName,
        'is_favorite': isFavorite,
      },
    );
  }
  
  /// Log settings changed
  Future<void> logSettingsChanged({
    required String settingKey,
    required dynamic settingValue,
  }) async {
    await logEvent(
      name: AnalyticsEvents.settingsChanged,
      parameters: {
        AnalyticsParameters.settingKey: settingKey,
        AnalyticsParameters.settingValue: settingValue.toString(),
      },
    );
  }
  
  /// Log help viewed
  Future<void> logHelpViewed({
    required String helpTopic,
  }) async {
    await logEvent(
      name: AnalyticsEvents.helpViewed,
      parameters: {
        AnalyticsParameters.helpTopic: helpTopic,
      },
    );
  }
  
  /// Log feedback submitted
  Future<void> logFeedbackSubmitted({
    required String feedbackType,
    String? category,
  }) async {
    await logEvent(
      name: AnalyticsEvents.feedbackSubmitted,
      parameters: {
        AnalyticsParameters.feedbackType: feedbackType,
        if (category != null) AnalyticsParameters.category: category,
      },
    );
  }
  
  /// Log external player launched
  Future<void> logExternalPlayerLaunched({
    required String playerType,
    String? channelName,
  }) async {
    await logEvent(
      name: AnalyticsEvents.externalPlayerLaunched,
      parameters: {
        AnalyticsParameters.playerType: playerType,
        if (channelName != null) AnalyticsParameters.channelName: channelName,
      },
    );
  }
  
  /// Check if Firebase is available
  bool get isFirebaseAvailable => _firebaseAvailable;
  
  /// Check if analytics is initialized
  bool get isInitialized => _isInitialized;
}

/// Global analytics instance (convenience)
final analytics = AnalyticsService.instance;

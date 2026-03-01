/// Example: Using the Supabase-backed Analytics and Crashlytics Services
///
/// This file demonstrates how to use the anonymous analytics service
/// in your application. Copy these patterns into your actual code.
///
/// The analytics service uses Supabase REST API — no Firebase required.
/// All data is anonymous: URLs are SHA-256 hashed, and the only identifier
/// is a random UUID generated per install and stored in shared_preferences.

import 'package:flutter/material.dart';
import 'package:tv_viewer/services/analytics_service.dart';
import 'package:tv_viewer/services/crashlytics_service.dart';
import 'package:tv_viewer/di/service_locator.dart';

// ============================================================================
// Example 1: Track channel playback (URL is auto-hashed for privacy)
// ============================================================================

class ExampleChannelPlayer {
  final _analytics = getIt<AnalyticsService>();
  final _crashlytics = getIt<CrashlyticsService>();

  Future<void> playChannel({
    required String channelUrl,
  }) async {
    try {
      // Add breadcrumb for crash reports
      await _crashlytics.log('Starting playback');

      // Track play event — URL is SHA-256 hashed internally
      await _analytics.trackChannelPlay(channelUrl);

      // Simulate channel playback
      print('Playing $channelUrl');
    } catch (e, stack) {
      // Record crash context
      await _crashlytics.recordError(
        e,
        stack,
        reason: 'Failed to play channel',
      );

      // Track the failure — URL is SHA-256 hashed internally
      await _analytics.trackChannelFail(channelUrl, e.toString());

      rethrow;
    }
  }
}

// ============================================================================
// Example 2: Track scan completion
// ============================================================================

class ExamplePlaylistManager {
  final _analytics = getIt<AnalyticsService>();
  final _crashlytics = getIt<CrashlyticsService>();

  Future<List<dynamic>> scanPlaylist(String playlistUrl) async {
    final startTime = DateTime.now();

    try {
      await _crashlytics.log('Starting playlist scan');

      // Simulate playlist scanning
      await Future.delayed(const Duration(seconds: 2));
      final channels = <dynamic>[]; // Simulated channels

      // Track scan result
      final duration = DateTime.now().difference(startTime);
      await _analytics.trackScanComplete(
        channels.length, // working
        0, // failed
        duration,
      );

      return channels;
    } catch (e, stack) {
      // Track failed scan
      final duration = DateTime.now().difference(startTime);
      await _analytics.trackScanComplete(0, 0, duration);

      await _crashlytics.recordError(
        e,
        stack,
        reason: 'Playlist scan failed',
      );

      rethrow;
    }
  }
}

// ============================================================================
// Example 3: Track filter usage (type only — no PII)
// ============================================================================

class ExampleFilterManager {
  final _analytics = getIt<AnalyticsService>();

  Future<void> applyCategoryFilter(String category) async {
    // Only the *type* of filter is tracked, never the value
    await _analytics.trackFilterUsed('category');
  }

  Future<void> applyCountryFilter(String country) async {
    await _analytics.trackFilterUsed('country');
  }

  Future<void> applyMediaTypeFilter(String mediaType) async {
    await _analytics.trackFilterUsed('media_type');
  }
}

// ============================================================================
// Example 4: Error handling with crash tracking
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

    // Track crash in analytics (first stack line only)
    await _analytics.trackCrash(error, stack);
  }
}

// ============================================================================
// Example 5: App initialisation
// ============================================================================

Future<void> exampleAppInitialization() async {
  final analyticsService = getIt<AnalyticsService>();
  final crashlytics = getIt<CrashlyticsService>();

  // Check service status
  if (analyticsService.isConfigured) {
    print('✅ Supabase Analytics enabled');
  } else {
    print('⚠️ Analytics disabled (SUPABASE_URL / SUPABASE_ANON_KEY not set)');
  }

  if (crashlytics.isFirebaseAvailable) {
    print('✅ Firebase Crashlytics enabled');
  } else {
    print('⚠️ Firebase Crashlytics in fallback mode (using logger)');
  }

  // Track app start
  await analyticsService.trackAppLaunch();

  // Set initial crash context
  await crashlytics.setCustomKey('app_version', '2.0.0');
  await crashlytics.setCustomKey('environment', 'production');
}

// ============================================================================
// Example 6: Widget with analytics
// ============================================================================

class ExampleAnalyticsWidget extends StatefulWidget {
  const ExampleAnalyticsWidget({Key? key}) : super(key: key);

  @override
  State<ExampleAnalyticsWidget> createState() => _ExampleAnalyticsWidgetState();
}

class _ExampleAnalyticsWidgetState extends State<ExampleAnalyticsWidget> {
  final _analytics = getIt<AnalyticsService>();

  void _handleButtonPress(String buttonName) async {
    // Track any custom event via the generic method
    await _analytics.trackEvent('button_pressed', {
      'button_name': buttonName,
    });
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
// Example 7: Custom analytics event
// ============================================================================

class ExampleCustomEvent {
  final _analytics = getIt<AnalyticsService>();

  Future<void> trackVideoPlayback({
    required int durationSeconds,
    required String quality,
  }) async {
    // Use the generic trackEvent for custom telemetry.
    // Never include channel names, URLs (unless hashed), or user data.
    await _analytics.trackEvent('video_playback', {
      'duration_seconds': durationSeconds,
      'quality': quality,
    });
  }
}

// ============================================================================
// Quick smoke-test (not for production)
// ============================================================================

void main() async {
  print('=== Analytics Service Examples ===\n');

  final analyticsService = AnalyticsService.instance;
  final crashlytics = CrashlyticsService.instance;

  await analyticsService.initialize();
  await crashlytics.initialize();

  print('Analytics initialised : ${analyticsService.isInitialized}');
  print('Analytics configured  : ${analyticsService.isConfigured}');
  print('Crashlytics initialised: ${crashlytics.isInitialized}');

  // Track events
  print('\n=== Tracking Events ===');
  await analyticsService.trackAppLaunch();
  await analyticsService.trackChannelPlay('http://example.com/stream.m3u8');
  await analyticsService.trackFilterUsed('category');

  // Record error
  print('\n=== Recording Error ===');
  try {
    throw Exception('Example error');
  } catch (e, stack) {
    await analyticsService.trackCrash(e, stack);
    await crashlytics.recordError(e, stack, reason: 'Testing error reporting');
  }

  // Flush remaining events
  await analyticsService.flush();

  print('\n✅ Examples complete! Check logs for output.');
}

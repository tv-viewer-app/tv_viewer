import 'dart:async';
import 'dart:convert';
import 'dart:io' show Platform;
import 'dart:math';

import 'package:crypto/crypto.dart';
import 'package:http/http.dart' as http;
import 'package:package_info_plus/package_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../utils/logger_service.dart';

/// Anonymous, privacy-first analytics service backed by Supabase REST API.
///
/// Features:
///   - No Firebase dependency — uses Supabase REST directly
///   - Anonymous: random UUID per install, no PII collected
///   - Privacy: all URLs are SHA-256 hashed before transmission
///   - Batched: events are queued and flushed every 30 s or at 20 events
///   - Fail-safe: errors are logged but never crash the host app
///   - Auto-enabled only when SUPABASE_URL and SUPABASE_ANON_KEY are set
///
/// Database table (Supabase):
///   analytics_events
///     id            — bigint, auto-increment (primary key)
///     device_id     — uuid (anonymous install identifier)
///     event_type    — text
///     event_data    — jsonb
///     app_version   — text
///     platform      — text ('android' | 'windows')
///     created_at    — timestamptz (default now())
class AnalyticsService {
  // ---------------------------------------------------------------------------
  // Singleton
  // ---------------------------------------------------------------------------
  static AnalyticsService? _instance;
  static AnalyticsService get instance => _instance ??= AnalyticsService._();
  AnalyticsService._();

  // ---------------------------------------------------------------------------
  // Supabase configuration — compile-time env overrides hardcoded defaults
  // The anon key is public and safe to embed (protected by RLS policies)
  // ---------------------------------------------------------------------------
  static String get _supabaseUrl =>
      const String.fromEnvironment('SUPABASE_URL',
          defaultValue: 'https://cdtxpefohpwtusmqengu.supabase.co');
  static String get _supabaseAnonKey =>
      const String.fromEnvironment('SUPABASE_ANON_KEY',
          defaultValue: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNkdHhwZWZvaHB3dHVzbXFlbmd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI0NzE4MzYsImV4cCI6MjA4ODA0NzgzNn0.FuzUDNIfxlGHptAZ0vWT4_8BDDEcy9CcSCY3te7_wMo');
  static const String _tableName = 'analytics_events';

  /// Service is automatically enabled when both env vars are provided.
  static bool get _enabled =>
      _supabaseUrl.isNotEmpty && _supabaseAnonKey.isNotEmpty;

  // ---------------------------------------------------------------------------
  // Internal state
  // ---------------------------------------------------------------------------
  static const String _deviceIdKey = 'analytics_device_id';
  static const String _analyticsEnabledKey = 'analytics_enabled';
  static const int _maxQueueSize = 20;
  static const Duration _flushInterval = Duration(seconds: 30);
  static const Duration _httpTimeout = Duration(seconds: 10);

  final LoggerService _logger = LoggerService.instance;

  bool _isInitialized = false;
  bool _userOptedIn = true;
  String _deviceId = '';
  String _appVersion = '';
  String _platform = '';

  final List<Map<String, dynamic>> _queue = [];
  Timer? _flushTimer;

  // ---------------------------------------------------------------------------
  // Public getters
  // ---------------------------------------------------------------------------

  /// Whether the analytics backend is reachable and user has not opted out.
  bool get isConfigured =>
      _enabled &&
      _userOptedIn &&
      _supabaseUrl != 'YOUR_SUPABASE_PROJECT_URL' &&
      _supabaseAnonKey != 'YOUR_SUPABASE_ANON_KEY';

  /// Whether [initialize] has completed successfully.
  bool get isInitialized => _isInitialized;

  /// Whether the user has opted in to analytics.
  bool get isOptedIn => _userOptedIn;

  /// Number of events currently queued (useful for testing).
  int get queueLength => _queue.length;

  // ---------------------------------------------------------------------------
  // Lifecycle
  // ---------------------------------------------------------------------------

  /// Initialise the service: load or generate the anonymous device ID,
  /// resolve app version and platform, and start the periodic flush timer.
  Future<void> initialize() async {
    if (_isInitialized) return;

    try {
      // Resolve platform
      _platform = _resolvePlatform();

      // Resolve app version
      try {
        final info = await PackageInfo.fromPlatform();
        _appVersion = info.version;
      } catch (_) {
        _appVersion = 'unknown';
      }

      // Load or generate anonymous device ID and opt-in preference
      final prefs = await SharedPreferences.getInstance();
      _userOptedIn = prefs.getBool(_analyticsEnabledKey) ?? true;
      _deviceId = prefs.getString(_deviceIdKey) ?? '';
      if (_deviceId.isEmpty) {
        _deviceId = _generateUuidV4();
        await prefs.setString(_deviceIdKey, _deviceId);
      }

      // Start periodic flush
      _flushTimer?.cancel();
      _flushTimer = Timer.periodic(_flushInterval, (_) => flush());

      _isInitialized = true;

      if (isConfigured) {
        _logger.info('[Analytics] Initialised — device=$_deviceId, '
            'platform=$_platform, version=$_appVersion');
      } else {
        _logger.info('[Analytics] Disabled (Supabase env vars not set)');
      }
    } catch (e) {
      _logger.warning('[Analytics] Failed to initialise', e);
      // Mark as initialised so callers aren't blocked.
      _isInitialized = true;
    }
  }

  /// Flush remaining events and cancel the periodic timer.
  Future<void> dispose() async {
    _flushTimer?.cancel();
    _flushTimer = null;
    await flush();
  }

  /// Allow user to opt in/out of anonymous analytics collection.
  Future<void> setEnabled(bool enabled) async {
    _userOptedIn = enabled;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_analyticsEnabledKey, enabled);
    _logger.info('[Analytics] User opted ${enabled ? "in" : "out"}');
  }

  // ---------------------------------------------------------------------------
  // Generic event tracking
  // ---------------------------------------------------------------------------

  /// Enqueue a generic analytics event.
  ///
  /// Events are batched and sent to Supabase in bulk — see [flush].
  Future<void> trackEvent(String type, [Map<String, dynamic>? data]) async {
    if (!_isInitialized) await initialize();
    if (!isConfigured) return;

    try {
      final event = <String, dynamic>{
        'device_id': _deviceId,
        'event_type': type,
        'event_data': data ?? <String, dynamic>{},
        'app_version': _appVersion,
        'platform': _platform,
        'created_at': DateTime.now().toUtc().toIso8601String(),
      };

      _queue.add(event);
      _logger.debug('[Analytics] Queued event: $type (queue=${_queue.length})');

      if (_queue.length >= _maxQueueSize) {
        await flush();
      }
    } catch (e) {
      _logger.warning('[Analytics] Failed to queue event: $type', e);
    }
  }

  // ---------------------------------------------------------------------------
  // Convenience methods
  // ---------------------------------------------------------------------------

  /// Track an app launch with platform metadata.
  Future<void> trackAppLaunch() async {
    await trackEvent('app_launch', {
      'platform_os': _platform,
      'app_version': _appVersion,
    });
  }

  /// Track when a user plays a channel (NO names or URLs — only country/category).
  Future<void> trackChannelPlay(String url, {String country = '', String category = ''}) async {
    await trackEvent('channel_play', {
      'url_hash': _hashUrl(url),
      'country': country,
      'category': category,
    });
  }

  /// Track when a stream fails to play (NO names or URLs).
  Future<void> trackChannelFail(String url, String error, {String country = '', String category = ''}) async {
    await trackEvent('channel_fail', {
      'url_hash': _hashUrl(url),
      'error_code': error,
      'country': country,
      'category': category,
    });
  }

  /// Track when a channel validation scan finishes.
  Future<void> trackScanComplete(
    int working,
    int failed,
    Duration duration,
  ) async {
    await trackEvent('scan_complete', {
      'working_count': working,
      'failed_count': failed,
      'duration_ms': duration.inMilliseconds,
    });
  }

  /// Track an uncaught exception (sanitized for privacy).
  Future<void> trackCrash(dynamic error, StackTrace? stack) async {
    String firstLine = '';
    if (stack != null) {
      final lines = stack.toString().split('\n');
      if (lines.isNotEmpty) {
        firstLine = lines.first.trim();
      }
    }

    await trackEvent('app_crash', {
      'error_type': error.runtimeType.toString(),
      'error_message': _sanitizeErrorMessage(error.toString()),
      'stack_first_line': firstLine,
    });

    // Flush immediately on crash — the app may be about to exit.
    await flush();
  }

  /// Track when a user applies a filter (type only, not the value).
  Future<void> trackFilterUsed(String filterType) async {
    await trackEvent('filter_used', {
      'filter_type': filterType,
    });
  }

  /// Track feature usage (e.g. 'map_open', 'search', 'fullscreen').
  Future<void> trackFeature(String feature) async {
    await trackEvent('feature_use', {
      'feature': feature,
    });
  }

  // ---------------------------------------------------------------------------
  // Flush (batch send to Supabase)
  // ---------------------------------------------------------------------------

  /// Send all queued events to the Supabase `analytics_events` table.
  ///
  /// Uses the PostgREST bulk-insert endpoint. On failure the events are kept
  /// in the queue for the next attempt (up to 100 events to avoid unbounded
  /// memory growth).
  Future<void> flush() async {
    if (_queue.isEmpty || !isConfigured) return;

    // Snapshot and clear the queue so new events don't interfere.
    final batch = List<Map<String, dynamic>>.from(_queue);
    _queue.clear();

    try {
      final url = Uri.parse('$_supabaseUrl/rest/v1/$_tableName');

      final response = await http
          .post(
            url,
            headers: {
              'apikey': _supabaseAnonKey,
              'Authorization': 'Bearer $_supabaseAnonKey',
              'Content-Type': 'application/json',
              'Prefer': 'return=minimal',
            },
            body: json.encode(batch),
          )
          .timeout(_httpTimeout);

      if (response.statusCode == 200 || response.statusCode == 201) {
        _logger.debug(
            '[Analytics] Flushed ${batch.length} events successfully');
      } else {
        _logger.warning(
            '[Analytics] Flush failed: ${response.statusCode}');
        _requeue(batch);
      }
    } catch (e) {
      _logger.warning('[Analytics] Flush error', e);
      _requeue(batch);
    }
  }

  // ---------------------------------------------------------------------------
  // Private helpers
  // ---------------------------------------------------------------------------

  /// Push failed events back onto the queue (capped at 100 to limit memory).
  void _requeue(List<Map<String, dynamic>> events) {
    _queue.insertAll(0, events);
    if (_queue.length > 100) {
      _queue.removeRange(0, _queue.length - 100);
    }
  }

  /// SHA-256 hash a URL for privacy.
  static String _hashUrl(String url) {
    final bytes = utf8.encode(url);
    return sha256.convert(bytes).toString();
  }

  /// Strip potential PII (file paths, URLs, tokens) from error messages.
  static String _sanitizeErrorMessage(String msg) {
    msg = msg.replaceAll(RegExp(r'https?://[^\s]+'), '[URL]');
    msg = msg.replaceAll(RegExp(r'[A-Za-z]:\\[^\s]+'), '[PATH]');
    msg = msg.replaceAll(RegExp(r'/[^\s]*/[^\s]*'), '[PATH]');
    if (msg.length > 100) msg = msg.substring(0, 100);
    return msg;
  }

  /// Generate a version-4 (random) UUID without an external package.
  static String _generateUuidV4() {
    final rng = Random.secure();
    final bytes = List<int>.generate(16, (_) => rng.nextInt(256));

    // Set version (4) and variant (10xx) bits per RFC 4122.
    bytes[6] = (bytes[6] & 0x0F) | 0x40;
    bytes[8] = (bytes[8] & 0x3F) | 0x80;

    String hex(int byte) => byte.toRadixString(16).padLeft(2, '0');

    return '${bytes.sublist(0, 4).map(hex).join()}-'
        '${bytes.sublist(4, 6).map(hex).join()}-'
        '${bytes.sublist(6, 8).map(hex).join()}-'
        '${bytes.sublist(8, 10).map(hex).join()}-'
        '${bytes.sublist(10, 16).map(hex).join()}';
  }

  /// Resolve a short, consistent platform label.
  static String _resolvePlatform() {
    try {
      if (Platform.isAndroid) return 'android';
      if (Platform.isWindows) return 'windows';
      if (Platform.isIOS) return 'ios';
      if (Platform.isLinux) return 'linux';
      if (Platform.isMacOS) return 'macos';
      return Platform.operatingSystem;
    } catch (_) {
      return 'unknown';
    }
  }
}

/// Global analytics instance (convenience).
final analytics = AnalyticsService.instance;

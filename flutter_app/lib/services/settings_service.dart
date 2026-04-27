import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../utils/logger_service.dart';

/// Centralized settings service for TV Viewer app.
///
/// Manages all user-configurable settings via SharedPreferences.
/// Uses a singleton pattern for consistent access across the app.
class SettingsService {
  SettingsService._();
  static final SettingsService instance = SettingsService._();

  // ── SharedPreferences keys ───────────────────────────────────────
  static const String _keyStreamTimeout = 'stream_timeout';
  static const String _keyRequestTimeout = 'request_timeout';
  static const String _keyThemeMode = 'theme_mode';
  static const String _keyDefaultGroupBy = 'default_group_by';
  static const String _keyCustomRepos = 'custom_repos';
  static const String _keyAnalyticsEnabled = 'analytics_enabled';

  // ── Default values ───────────────────────────────────────────────
  static const int defaultStreamTimeout = 10;
  static const int defaultRequestTimeout = 10;
  static const String defaultThemeMode = 'system'; // 'dark', 'light', 'system'
  static const String defaultGroupBy = 'category'; // 'category', 'country'
  static const bool defaultAnalyticsEnabled = true;

  SharedPreferences? _prefs;

  /// Initialize the service (call once at app startup).
  Future<void> initialize() async {
    _prefs = await SharedPreferences.getInstance();
    logger.info('SettingsService initialized');
  }

  /// Ensure prefs are loaded (lazy init if not called explicitly).
  Future<SharedPreferences> _getPrefs() async {
    _prefs ??= await SharedPreferences.getInstance();
    return _prefs!;
  }

  // ── Stream Settings ──────────────────────────────────────────────

  /// Stream check timeout in seconds (3–30).
  Future<int> getStreamTimeout() async {
    final prefs = await _getPrefs();
    return prefs.getInt(_keyStreamTimeout) ?? defaultStreamTimeout;
  }

  Future<void> setStreamTimeout(int seconds) async {
    final prefs = await _getPrefs();
    await prefs.setInt(_keyStreamTimeout, seconds.clamp(3, 30));
  }

  /// HTTP request timeout in seconds (3–30).
  Future<int> getRequestTimeout() async {
    final prefs = await _getPrefs();
    return prefs.getInt(_keyRequestTimeout) ?? defaultRequestTimeout;
  }

  Future<void> setRequestTimeout(int seconds) async {
    final prefs = await _getPrefs();
    await prefs.setInt(_keyRequestTimeout, seconds.clamp(3, 30));
  }

  // ── Display Settings ─────────────────────────────────────────────

  /// Theme mode: 'dark', 'light', or 'system'.
  Future<String> getThemeMode() async {
    final prefs = await _getPrefs();
    return prefs.getString(_keyThemeMode) ?? defaultThemeMode;
  }

  Future<void> setThemeMode(String mode) async {
    final prefs = await _getPrefs();
    await prefs.setString(_keyThemeMode, mode);
  }

  /// Default group-by: 'category' or 'country'.
  Future<String> getDefaultGroupBy() async {
    final prefs = await _getPrefs();
    return prefs.getString(_keyDefaultGroupBy) ?? defaultGroupBy;
  }

  Future<void> setDefaultGroupBy(String groupBy) async {
    final prefs = await _getPrefs();
    await prefs.setString(_keyDefaultGroupBy, groupBy);
  }

  // ── Repository Management ────────────────────────────────────────

  /// Get custom repo URLs. Returns null if user hasn't customized repos.
  Future<List<String>?> getCustomRepos() async {
    final prefs = await _getPrefs();
    final json = prefs.getString(_keyCustomRepos);
    if (json == null) return null;
    try {
      final List<dynamic> decoded = jsonDecode(json);
      return decoded.cast<String>();
    } catch (e) {
      logger.error('Failed to decode custom repos', e);
      return null;
    }
  }

  /// Save custom repo URLs.
  Future<void> setCustomRepos(List<String> repos) async {
    final prefs = await _getPrefs();
    await prefs.setString(_keyCustomRepos, jsonEncode(repos));
  }

  /// Remove custom repos (revert to defaults).
  Future<void> clearCustomRepos() async {
    final prefs = await _getPrefs();
    await prefs.remove(_keyCustomRepos);
  }

  // ── Privacy Settings ─────────────────────────────────────────────

  /// Whether analytics/telemetry is enabled.
  Future<bool> getAnalyticsEnabled() async {
    final prefs = await _getPrefs();
    return prefs.getBool(_keyAnalyticsEnabled) ?? defaultAnalyticsEnabled;
  }

  Future<void> setAnalyticsEnabled(bool enabled) async {
    final prefs = await _getPrefs();
    await prefs.setBool(_keyAnalyticsEnabled, enabled);
  }
}

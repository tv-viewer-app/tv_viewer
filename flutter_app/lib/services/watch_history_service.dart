import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';
import '../utils/logger_service.dart';

/// Service for managing watch history persistence.
///
/// Tracks recently played channels with play counts and timestamps.
/// Stores up to [maxEntries] entries in SharedPreferences as JSON.
/// Oldest entries (by last_played) are evicted when the limit is exceeded.
///
/// Ported from Python: utils/history.py (WatchHistory class).
class WatchHistoryService {
  static const String _historyKey = 'watch_history';
  static const int maxEntries = 50;

  // ── Public API ──────────────────────────────────────────────────────

  /// Record (or update) a channel play in history.
  ///
  /// [channel] must be a Map with at least a 'url' key.
  /// 'name', 'country', 'category', and 'logo' are optional but recommended.
  static Future<bool> recordPlay(Map<String, dynamic> channel) async {
    try {
      final url = channel['url'] as String?;
      if (url == null || url.isEmpty) return false;

      final entries = await _loadEntries();
      final now = DateTime.now().millisecondsSinceEpoch;

      final existing = entries[url];
      if (existing != null) {
        existing['play_count'] = (existing['play_count'] as int? ?? 0) + 1;
        existing['last_played'] = now;
        // Update mutable metadata in case it changed
        existing['name'] = channel['name'] ?? existing['name'] ?? '';
        existing['country'] = channel['country'] ?? existing['country'] ?? '';
        existing['category'] = channel['category'] ?? existing['category'] ?? '';
        existing['logo'] = channel['logo'] ?? existing['logo'];
      } else {
        entries[url] = {
          'name': channel['name'] ?? '',
          'url': url,
          'country': channel['country'] ?? '',
          'category': channel['category'] ?? '',
          'logo': channel['logo'],
          'last_played': now,
          'play_count': 1,
        };
      }

      _enforceLimit(entries);
      return await _saveEntries(entries);
    } catch (e) {
      logger.warning('Error recording play in watch history', e);
      return false;
    }
  }

  /// Return up to [limit] entries sorted by last_played descending.
  static Future<List<Map<String, dynamic>>> getRecent({int limit = 20}) async {
    try {
      final entries = await _loadEntries();
      final list = entries.values.toList()
        ..sort((a, b) {
          final aTime = a['last_played'] as int? ?? 0;
          final bTime = b['last_played'] as int? ?? 0;
          return bTime.compareTo(aTime);
        });
      return list.take(limit).toList();
    } catch (e) {
      logger.warning('Error getting recent watch history', e);
      return [];
    }
  }

  /// Return up to [limit] entries sorted by play_count descending.
  static Future<List<Map<String, dynamic>>> getMostPlayed({int limit = 10}) async {
    try {
      final entries = await _loadEntries();
      final list = entries.values.toList()
        ..sort((a, b) {
          final aCount = a['play_count'] as int? ?? 0;
          final bCount = b['play_count'] as int? ?? 0;
          return bCount.compareTo(aCount);
        });
      return list.take(limit).toList();
    } catch (e) {
      logger.warning('Error getting most played watch history', e);
      return [];
    }
  }

  /// Remove a specific entry by URL.
  static Future<bool> remove(String url) async {
    try {
      final entries = await _loadEntries();
      if (entries.remove(url) != null) {
        return await _saveEntries(entries);
      }
      return true;
    } catch (e) {
      logger.warning('Error removing watch history entry', e);
      return false;
    }
  }

  /// Remove all history entries.
  static Future<bool> clear() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return await prefs.remove(_historyKey);
    } catch (e) {
      logger.warning('Error clearing watch history', e);
      return false;
    }
  }

  // ── Persistence helpers ─────────────────────────────────────────────

  /// Load history entries from SharedPreferences, keyed by URL.
  static Future<Map<String, Map<String, dynamic>>> _loadEntries() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_historyKey);
    if (raw == null || raw.isEmpty) return {};

    try {
      final decoded = json.decode(raw);
      // Support both list format and {entries: [...]} format
      final List<dynamic> entriesList;
      if (decoded is List) {
        entriesList = decoded;
      } else if (decoded is Map && decoded.containsKey('entries')) {
        entriesList = decoded['entries'] as List<dynamic>? ?? [];
      } else {
        return {};
      }

      final map = <String, Map<String, dynamic>>{};
      for (final item in entriesList) {
        if (item is Map<String, dynamic>) {
          final url = item['url'] as String?;
          if (url != null && url.isNotEmpty) {
            map[url] = Map<String, dynamic>.from(item);
          }
        }
      }
      return map;
    } catch (e) {
      logger.warning('Error parsing watch history JSON', e);
      return {};
    }
  }

  /// Persist entries to SharedPreferences.
  static Future<bool> _saveEntries(Map<String, Map<String, dynamic>> entries) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final data = json.encode({'entries': entries.values.toList()});
      return await prefs.setString(_historyKey, data);
    } catch (e) {
      logger.warning('Error saving watch history', e);
      return false;
    }
  }

  /// Drop oldest entries (by last_played) when over [maxEntries].
  static void _enforceLimit(Map<String, Map<String, dynamic>> entries) {
    if (entries.length <= maxEntries) return;

    // Sort URLs by last_played ascending (oldest first)
    final sortedUrls = entries.keys.toList()
      ..sort((a, b) {
        final aTime = entries[a]!['last_played'] as int? ?? 0;
        final bTime = entries[b]!['last_played'] as int? ?? 0;
        return aTime.compareTo(bTime);
      });

    final excess = entries.length - maxEntries;
    for (var i = 0; i < excess; i++) {
      entries.remove(sortedUrls[i]);
    }
  }
}

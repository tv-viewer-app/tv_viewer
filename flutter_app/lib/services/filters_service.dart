import 'package:shared_preferences/shared_preferences.dart';

import '../utils/logger_service.dart';
import '../utils/prefs_lock.dart';

/// Persists the user's last-used filter selections across launches.
///
/// Mirrors [FavoritesService] — uses SharedPreferences (app-private on Android,
/// AppData on Windows/Linux). The search query is intentionally NOT persisted
/// because it's transient.
///
/// All keys are stored under the `tv_viewer_filters_*` namespace so they are
/// easy to reset (and don't collide with `favorite_channels`, etc.).
class FiltersService {
  static const String _kCategory = 'tv_viewer_filters_category';
  static const String _kCountry = 'tv_viewer_filters_country';
  static const String _kLanguage = 'tv_viewer_filters_language';
  static const String _kMediaType = 'tv_viewer_filters_media_type';
  static const String _kStatus = 'tv_viewer_filters_status';
  static const String _kFavOnly = 'tv_viewer_filters_favorites_only';
  static const String _kShowAllChannels = 'tv_viewer_filters_show_all_channels';

  /// Snapshot of the persisted selection (all default to `'All'`/`false`).
  static Future<FiltersSnapshot> load() async {
    try {
      final p = await SharedPreferences.getInstance();
      return FiltersSnapshot(
        category: p.getString(_kCategory) ?? 'All',
        country: p.getString(_kCountry) ?? 'All',
        language: p.getString(_kLanguage) ?? 'All',
        mediaType: p.getString(_kMediaType) ?? 'All',
        status: p.getString(_kStatus) ?? 'All',
        favoritesOnly: p.getBool(_kFavOnly) ?? false,
        showAllChannels: p.getBool(_kShowAllChannels) ?? false,
      );
    } catch (e) {
      logger.warning('FiltersService.load failed', e);
      return const FiltersSnapshot();
    }
  }

  static Future<void> saveCategory(String v) => _putString(_kCategory, v);
  static Future<void> saveCountry(String v) => _putString(_kCountry, v);
  static Future<void> saveLanguage(String v) => _putString(_kLanguage, v);
  static Future<void> saveMediaType(String v) => _putString(_kMediaType, v);
  static Future<void> saveStatus(String v) => _putString(_kStatus, v);

  static Future<void> saveFavoritesOnly(bool v) async {
    try {
      final p = await SharedPreferences.getInstance();
      await p.safeSetBool(_kFavOnly, v);
    } catch (e) {
      logger.warning('FiltersService.saveFavoritesOnly failed', e);
    }
  }

  static Future<void> saveShowAllChannels(bool v) async {
    try {
      final p = await SharedPreferences.getInstance();
      await p.safeSetBool(_kShowAllChannels, v);
    } catch (e) {
      logger.warning('FiltersService.saveShowAllChannels failed', e);
    }
  }

  /// Reset all filter prefs to their defaults (used by "Clear filters").
  static Future<void> clear() async {
    try {
      final p = await SharedPreferences.getInstance();
      await p.safeRemove(_kCategory);
      await p.safeRemove(_kCountry);
      await p.safeRemove(_kLanguage);
      await p.safeRemove(_kMediaType);
      await p.safeRemove(_kStatus);
      await p.safeRemove(_kFavOnly);
      await p.safeRemove(_kShowAllChannels);
    } catch (e) {
      logger.warning('FiltersService.clear failed', e);
    }
  }

  static Future<void> _putString(String key, String value) async {
    try {
      final p = await SharedPreferences.getInstance();
      await p.safeSetString(key, value);
    } catch (e) {
      logger.warning('FiltersService set "$key" failed', e);
    }
  }
}

/// Immutable view of persisted filter values.
class FiltersSnapshot {
  final String category;
  final String country;
  final String language;
  final String mediaType;
  final String status;
  final bool favoritesOnly;
  final bool showAllChannels;

  const FiltersSnapshot({
    this.category = 'All',
    this.country = 'All',
    this.language = 'All',
    this.mediaType = 'All',
    this.status = 'All',
    this.favoritesOnly = false,
    this.showAllChannels = false,
  });
}

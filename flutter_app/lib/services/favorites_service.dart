import 'package:shared_preferences/shared_preferences.dart';
import '../utils/logger_service.dart';

/// Service for managing channel favorites persistence
/// Stores favorite channel URLs in SharedPreferences
class FavoritesService {
  static const String _favoritesKey = 'favorite_channels';

  /// Load favorite channel URLs from SharedPreferences
  static Future<Set<String>> loadFavorites() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final List<String>? favoritesList = prefs.getStringList(_favoritesKey);
      
      if (favoritesList != null) {
        return favoritesList.toSet();
      }
      return {};
    } catch (e) {
      logger.warning('Error loading favorites', e);
      return {};
    }
  }

  /// Save favorite channel URLs to SharedPreferences
  static Future<bool> saveFavorites(Set<String> favoriteUrls) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return await prefs.setStringList(_favoritesKey, favoriteUrls.toList());
    } catch (e) {
      logger.warning('Error saving favorites', e);
      return false;
    }
  }

  /// Add a channel URL to favorites
  static Future<bool> addFavorite(String channelUrl) async {
    try {
      final favorites = await loadFavorites();
      favorites.add(channelUrl);
      return await saveFavorites(favorites);
    } catch (e) {
      logger.warning('Error adding favorite', e);
      return false;
    }
  }

  /// Remove a channel URL from favorites
  static Future<bool> removeFavorite(String channelUrl) async {
    try {
      final favorites = await loadFavorites();
      favorites.remove(channelUrl);
      return await saveFavorites(favorites);
    } catch (e) {
      logger.warning('Error removing favorite', e);
      return false;
    }
  }

  /// Check if a channel URL is in favorites
  static Future<bool> isFavorite(String channelUrl) async {
    try {
      final favorites = await loadFavorites();
      return favorites.contains(channelUrl);
    } catch (e) {
      logger.warning('Error checking favorite', e);
      return false;
    }
  }

  /// Clear all favorites
  static Future<bool> clearFavorites() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return await prefs.remove(_favoritesKey);
    } catch (e) {
      logger.warning('Error clearing favorites', e);
      return false;
    }
  }
}

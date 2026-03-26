import 'package:shared_preferences/shared_preferences.dart';
import '../utils/logger_service.dart';

/// Service for managing M3U repository sources
/// Stores custom repository URLs in SharedPreferences
class RepositoryService {
  static const String _repositoriesKey = 'custom_repositories';
  
  /// Default M3U repositories (same as previous hardcoded values)
  static const List<String> defaultRepositories = [
    'https://iptv-org.github.io/iptv/index.m3u',
    'https://iptv-org.github.io/iptv/index.category.m3u',
  ];
  
  /// Fallback repositories if defaults fail
  static const List<String> fallbackRepositories = [
    'https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us.m3u',
    'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8',
  ];

  /// Load repository URLs from SharedPreferences
  /// Returns default repositories on first launch
  static Future<List<String>> loadRepositories() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final List<String>? storedRepos = prefs.getStringList(_repositoriesKey);
      
      if (storedRepos != null && storedRepos.isNotEmpty) {
        logger.info('Loaded ${storedRepos.length} custom repositories from storage');
        return storedRepos;
      }
      
      // First launch - initialize with defaults
      logger.info('No custom repositories found, using defaults');
      await saveRepositories(defaultRepositories);
      return defaultRepositories;
    } catch (e) {
      logger.error('Error loading repositories', e);
      return defaultRepositories;
    }
  }

  /// Save repository URLs to SharedPreferences
  static Future<bool> saveRepositories(List<String> repositories) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final success = await prefs.setStringList(_repositoriesKey, repositories);
      if (success) {
        logger.info('Saved ${repositories.length} repositories to storage');
      }
      return success;
    } catch (e) {
      logger.error('Error saving repositories', e);
      return false;
    }
  }

  /// Add a new repository URL
  static Future<bool> addRepository(String url) async {
    try {
      // Validate URL format
      if (!_isValidUrl(url)) {
        logger.warning('Invalid repository URL: $url');
        return false;
      }
      
      final repositories = await loadRepositories();
      
      // Check if already exists
      if (repositories.contains(url)) {
        logger.info('Repository already exists: $url');
        return false;
      }
      
      repositories.add(url);
      return await saveRepositories(repositories);
    } catch (e) {
      logger.error('Error adding repository', e);
      return false;
    }
  }

  /// Remove a repository URL
  static Future<bool> removeRepository(String url) async {
    try {
      final repositories = await loadRepositories();
      
      // Don't allow removing all repositories
      if (repositories.length <= 1) {
        logger.warning('Cannot remove last repository');
        return false;
      }
      
      repositories.remove(url);
      return await saveRepositories(repositories);
    } catch (e) {
      logger.error('Error removing repository', e);
      return false;
    }
  }

  /// Update a repository URL (replace old with new)
  static Future<bool> updateRepository(String oldUrl, String newUrl) async {
    try {
      if (!_isValidUrl(newUrl)) {
        logger.warning('Invalid repository URL: $newUrl');
        return false;
      }
      
      final repositories = await loadRepositories();
      final index = repositories.indexOf(oldUrl);
      
      if (index == -1) {
        logger.warning('Repository not found: $oldUrl');
        return false;
      }
      
      repositories[index] = newUrl;
      return await saveRepositories(repositories);
    } catch (e) {
      logger.error('Error updating repository', e);
      return false;
    }
  }

  /// Reset to default repositories
  static Future<bool> resetToDefaults() async {
    try {
      logger.info('Resetting to default repositories');
      return await saveRepositories(defaultRepositories);
    } catch (e) {
      logger.error('Error resetting to defaults', e);
      return false;
    }
  }

  /// Add all fallback repositories to the current list
  static Future<bool> addFallbacks() async {
    try {
      final repositories = await loadRepositories();
      bool added = false;
      
      for (final fallback in fallbackRepositories) {
        if (!repositories.contains(fallback)) {
          repositories.add(fallback);
          added = true;
        }
      }
      
      if (added) {
        logger.info('Added fallback repositories');
        return await saveRepositories(repositories);
      }
      
      return false;
    } catch (e) {
      logger.error('Error adding fallbacks', e);
      return false;
    }
  }

  /// Validate URL format
  static bool _isValidUrl(String url) {
    try {
      final uri = Uri.parse(url);
      return uri.hasScheme && 
             (uri.scheme == 'http' || uri.scheme == 'https') &&
             uri.hasAuthority;
    } catch (e) {
      return false;
    }
  }

  /// Get all available repositories (current + fallbacks)
  static Future<List<String>> getAllAvailableRepositories() async {
    final current = await loadRepositories();
    final all = <String>[...current];
    
    // Add fallbacks that aren't already in the list
    for (final fallback in fallbackRepositories) {
      if (!all.contains(fallback)) {
        all.add(fallback);
      }
    }
    
    return all;
  }
}

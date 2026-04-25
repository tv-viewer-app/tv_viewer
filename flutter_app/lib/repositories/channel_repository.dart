import '../models/channel.dart';

/// Abstract repository interface for channel data access
/// 
/// This interface defines the contract for channel data operations,
/// separating business logic from data access implementation details.
/// Implementations can use different data sources (API, cache, database).
abstract class ChannelRepository {
  /// Fetch all channels from remote data sources
  /// 
  /// Returns a list of channels from all configured repositories.
  /// May throw exceptions if all data sources fail.
  Future<List<Channel>> fetchChannels({
    void Function(int current, int total)? onProgress,
  });

  /// Get channels from local cache
  /// 
  /// Returns cached channels if available, empty list otherwise.
  /// Does not throw exceptions - returns empty list on error.
  Future<List<Channel>> getCachedChannels();

  /// Save channels to local cache
  /// 
  /// Persists the channel list for offline access.
  /// Returns true if successful, false otherwise.
  Future<bool> cacheChannels(List<Channel> channels);

  /// Validate if a stream URL is accessible
  /// 
  /// Performs a lightweight check to verify stream availability.
  /// Returns true if the stream responds successfully, false otherwise.
  Future<bool> validateChannelStream(String url);

  /// Get favorite channel URLs
  /// 
  /// Returns a set of URLs that have been marked as favorites.
  Future<Set<String>> getFavorites();

  /// Add a channel URL to favorites
  /// 
  /// Returns true if successful, false otherwise.
  Future<bool> addFavorite(String channelUrl);

  /// Remove a channel URL from favorites
  /// 
  /// Returns true if successful, false otherwise.
  Future<bool> removeFavorite(String channelUrl);

  /// Check if a channel URL is favorited
  /// 
  /// Returns true if the URL is in favorites, false otherwise.
  Future<bool> isFavorite(String channelUrl);

  /// Clear all cached data
  /// 
  /// Removes all cached channels and favorites.
  /// Use with caution - this cannot be undone.
  Future<void> clearCache();
}

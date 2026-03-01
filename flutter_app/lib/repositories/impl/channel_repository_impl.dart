import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../../models/channel.dart';
import '../../services/m3u_service.dart';
import '../../services/favorites_service.dart';
import '../../utils/logger_service.dart';
import '../channel_repository.dart';

/// Default implementation of ChannelRepository
/// 
/// This implementation uses:
/// - M3UService for remote channel fetching
/// - SharedPreferences for local caching
/// - FavoritesService for favorites persistence
class ChannelRepositoryImpl implements ChannelRepository {
  static const String _channelsCacheKey = 'channels_cache';

  @override
  Future<List<Channel>> fetchChannels({
    void Function(int current, int total)? onProgress,
  }) async {
    logger.info('ChannelRepository: Fetching channels from remote sources');
    
    try {
      final channels = await M3UService.fetchAllChannels(
        onProgress: onProgress,
      );
      
      logger.info('ChannelRepository: Fetched ${channels.length} channels');
      return channels;
    } catch (e, stackTrace) {
      logger.error('ChannelRepository: Error fetching channels', e, stackTrace);
      rethrow;
    }
  }

  @override
  Future<List<Channel>> getCachedChannels() async {
    logger.debug('ChannelRepository: Loading channels from cache');
    
    try {
      final prefs = await SharedPreferences.getInstance();
      final json = prefs.getString(_channelsCacheKey);
      
      if (json != null) {
        final List<dynamic> data = jsonDecode(json);
        final channels = data.map((e) => Channel.fromJson(e)).toList();
        logger.info('ChannelRepository: Loaded ${channels.length} channels from cache');
        return channels;
      }
      
      logger.debug('ChannelRepository: No cached channels found');
      return [];
    } catch (e, stackTrace) {
      logger.error('ChannelRepository: Error loading cache', e, stackTrace);
      return []; // Return empty list on error, don't throw
    }
  }

  @override
  Future<bool> cacheChannels(List<Channel> channels) async {
    logger.debug('ChannelRepository: Caching ${channels.length} channels');
    
    try {
      final prefs = await SharedPreferences.getInstance();
      final json = jsonEncode(channels.map((c) => c.toJson()).toList());
      final success = await prefs.setString(_channelsCacheKey, json);
      
      if (success) {
        logger.info('ChannelRepository: Successfully cached ${channels.length} channels');
      } else {
        logger.warning('ChannelRepository: Failed to cache channels');
      }
      
      return success;
    } catch (e, stackTrace) {
      logger.error('ChannelRepository: Error caching channels', e, stackTrace);
      return false;
    }
  }

  @override
  Future<bool> validateChannelStream(String url) async {
    logger.debug('ChannelRepository: Validating stream: $url');
    
    try {
      final isValid = await M3UService.checkStream(url);
      logger.debug('ChannelRepository: Stream $url is ${isValid ? "valid" : "invalid"}');
      return isValid;
    } catch (e, stackTrace) {
      logger.error('ChannelRepository: Error validating stream', e, stackTrace);
      return false;
    }
  }

  @override
  Future<Set<String>> getFavorites() async {
    logger.debug('ChannelRepository: Loading favorites');
    
    try {
      final favorites = await FavoritesService.loadFavorites();
      logger.debug('ChannelRepository: Loaded ${favorites.length} favorites');
      return favorites;
    } catch (e, stackTrace) {
      logger.error('ChannelRepository: Error loading favorites', e, stackTrace);
      return {};
    }
  }

  @override
  Future<bool> addFavorite(String channelUrl) async {
    logger.debug('ChannelRepository: Adding favorite: $channelUrl');
    
    try {
      final success = await FavoritesService.addFavorite(channelUrl);
      if (success) {
        logger.info('ChannelRepository: Successfully added favorite');
      } else {
        logger.warning('ChannelRepository: Failed to add favorite');
      }
      return success;
    } catch (e, stackTrace) {
      logger.error('ChannelRepository: Error adding favorite', e, stackTrace);
      return false;
    }
  }

  @override
  Future<bool> removeFavorite(String channelUrl) async {
    logger.debug('ChannelRepository: Removing favorite: $channelUrl');
    
    try {
      final success = await FavoritesService.removeFavorite(channelUrl);
      if (success) {
        logger.info('ChannelRepository: Successfully removed favorite');
      } else {
        logger.warning('ChannelRepository: Failed to remove favorite');
      }
      return success;
    } catch (e, stackTrace) {
      logger.error('ChannelRepository: Error removing favorite', e, stackTrace);
      return false;
    }
  }

  @override
  Future<bool> isFavorite(String channelUrl) async {
    logger.debug('ChannelRepository: Checking if favorite: $channelUrl');
    
    try {
      final isFav = await FavoritesService.isFavorite(channelUrl);
      return isFav;
    } catch (e, stackTrace) {
      logger.error('ChannelRepository: Error checking favorite', e, stackTrace);
      return false;
    }
  }

  @override
  Future<void> clearCache() async {
    logger.info('ChannelRepository: Clearing all cache');
    
    try {
      final prefs = await SharedPreferences.getInstance();
      
      // Clear channels cache
      await prefs.remove(_channelsCacheKey);
      
      // Clear favorites
      await FavoritesService.clearFavorites();
      
      logger.info('ChannelRepository: Cache cleared successfully');
    } catch (e, stackTrace) {
      logger.error('ChannelRepository: Error clearing cache', e, stackTrace);
      rethrow;
    }
  }
}

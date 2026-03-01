import '../../models/channel.dart';
import '../../services/m3u_service.dart';
import '../../utils/logger_service.dart';
import '../playlist_repository.dart';

/// Default implementation of PlaylistRepository
/// 
/// This implementation wraps M3UService to provide playlist operations
/// while maintaining a clean repository interface.
class PlaylistRepositoryImpl implements PlaylistRepository {
  /// List of default M3U playlist repository URLs
  static const List<String> defaultPlaylistUrls = [
    'https://iptv-org.github.io/iptv/index.m3u',
    'https://iptv-org.github.io/iptv/index.category.m3u',
  ];

  @override
  Future<List<Channel>> fetchFromUrl(String url) async {
    logger.info('PlaylistRepository: Fetching playlist from $url');
    
    try {
      final channels = await M3UService.fetchFromUrl(url);
      logger.info('PlaylistRepository: Fetched ${channels.length} channels from $url');
      return channels;
    } catch (e, stackTrace) {
      logger.error('PlaylistRepository: Error fetching from $url', e, stackTrace);
      rethrow;
    }
  }

  @override
  List<Channel> parseM3U(String content) {
    logger.debug('PlaylistRepository: Parsing M3U content');
    
    try {
      final channels = M3UService.parseM3U(content);
      logger.info('PlaylistRepository: Parsed ${channels.length} channels');
      return channels;
    } catch (e, stackTrace) {
      logger.error('PlaylistRepository: Error parsing M3U', e, stackTrace);
      rethrow;
    }
  }

  @override
  Future<List<Channel>> fetchAllChannels({
    void Function(int current, int total)? onProgress,
  }) async {
    logger.info('PlaylistRepository: Fetching from ${defaultPlaylistUrls.length} playlists');
    
    try {
      final channels = await M3UService.fetchAllChannels(
        onProgress: onProgress,
      );
      
      logger.info('PlaylistRepository: Fetched total of ${channels.length} channels');
      return channels;
    } catch (e, stackTrace) {
      logger.error('PlaylistRepository: Error fetching all channels', e, stackTrace);
      rethrow;
    }
  }

  @override
  List<Channel> deduplicateChannels(List<Channel> channels) {
    logger.debug('PlaylistRepository: Deduplicating ${channels.length} channels');
    
    try {
      // Deduplicate by URL, keeping the first occurrence (most complete metadata)
      final seen = <String>{};
      final deduplicated = <Channel>[];
      for (final channel in channels) {
        if (seen.add(channel.url)) {
          deduplicated.add(channel);
        }
      }
      final removed = channels.length - deduplicated.length;
      
      if (removed > 0) {
        logger.info('PlaylistRepository: Removed $removed duplicates');
      }
      
      return deduplicated;
    } catch (e, stackTrace) {
      logger.error('PlaylistRepository: Error deduplicating', e, stackTrace);
      // Return original list on error
      return channels;
    }
  }

  @override
  String exportAsM3U(List<Channel> channels) {
    logger.info('PlaylistRepository: Exporting ${channels.length} channels as M3U');
    
    try {
      final buffer = StringBuffer();
      buffer.writeln('#EXTM3U');

      for (final channel in channels) {
        // Only export working channels
        if (!channel.isWorking) continue;
        
        // Build EXTINF line with metadata
        final attributes = <String>[];
        
        if (channel.logo != null && channel.logo!.isNotEmpty) {
          attributes.add('tvg-logo="${channel.logo}"');
        }
        
        if (channel.country != null && channel.country!.isNotEmpty) {
          attributes.add('tvg-country="${channel.country}"');
        }
        
        if (channel.language != null && channel.language!.isNotEmpty) {
          attributes.add('tvg-language="${channel.language}"');
        }
        
        final category = channel.category ?? 'Other';
        attributes.add('group-title="$category"');
        
        final attributesStr = attributes.isNotEmpty ? ' ${attributes.join(' ')}' : '';
        
        buffer.writeln('#EXTINF:-1$attributesStr,${channel.name}');
        buffer.writeln(channel.url);
      }

      final m3uContent = buffer.toString();
      logger.info('PlaylistRepository: Exported M3U content (${m3uContent.length} bytes)');
      return m3uContent;
    } catch (e, stackTrace) {
      logger.error('PlaylistRepository: Error exporting M3U', e, stackTrace);
      rethrow;
    }
  }
}

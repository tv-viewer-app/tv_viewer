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
        logger.info('PlaylistRepository: Removed $removed URL duplicates');
      }
      
      // Phase 2: Consolidate channels with similar names into multi-URL entries
      final consolidated = consolidateByName(deduplicated);
      
      return consolidated;
    } catch (e, stackTrace) {
      logger.error('PlaylistRepository: Error deduplicating', e, stackTrace);
      return channels;
    }
  }
  
  /// Quality/variant suffixes to strip when consolidating channel names
  static final _qualitySuffix = RegExp(
    r'\b(alt\s*\d*|backup|mirror|'
    r'\d{3,4}[pi]|'
    r'HD|FHD|UHD|4K|SD|'
    r'h\.?26[45]|hevc|avc|'
    r'mpeg\d?|mp3|aac\+?|flac|mono|stereo|'
    r'multi\s*[-_]?\s*audio|'
    r'subtitl\w*|dubbed|subs?|cc|closed\s*cap\w*|'
    r'low|high|med|'
    r'stream\s*\d+|'
    r'v\d+|'
    r'option\s*\d+|'
    r'feed\s*\d+|'
    r'\d+k)\s*$',
    caseSensitive: false,
  );

  /// Trailing parenthesized/bracketed annotations
  static final _parenSuffix = RegExp(r'\s*[\(\[][^\)\]]*[\)\]]\s*$');

  /// Strip quality/variant suffixes to get canonical channel name.
  /// Multi-pass: strips trailing [...], (...), then known variant words.
  static String _normalizeChannelName(String name) {
    if (name.isEmpty) return '';
    var normalized = name.trim();
    for (var i = 0; i < 4; i++) {
      final prev = normalized;
      normalized = normalized.replaceAll(_parenSuffix, '').trim();
      normalized = normalized.replaceAll(_qualitySuffix, '').trim();
      normalized = normalized.replaceAll(RegExp(r'[\s\-–—|/]+$'), '');
      if (normalized == prev) break;
    }
    return normalized.isNotEmpty ? normalized : name;
  }
  
  /// Merge channels with same base name into single multi-URL entries
  List<Channel> consolidateByName(List<Channel> channels) {
    final groups = <String, Channel>{};
    final groupOrder = <String>[];
    
    for (final ch in channels) {
      final baseName = _normalizeChannelName(ch.name);
      final country = (ch.country ?? 'Unknown').toLowerCase();
      final key = '${baseName.toLowerCase()}|$country';
      
      if (!groups.containsKey(key)) {
        // First occurrence — use as base, ensure urls list is populated
        final urls = ch.urls.isNotEmpty ? List<String>.from(ch.urls) : [ch.url];
        groups[key] = ch.copyWith(
          name: baseName,
          urls: urls,
          workingUrlIndex: 0,
        );
        groupOrder.add(key);
      } else {
        // Merge URLs into existing entry
        final existing = groups[key]!;
        final existingUrls = List<String>.from(existing.urls);
        final seen = existingUrls.toSet();
        
        for (final url in ch.urls) {
          if (url.isNotEmpty && !seen.contains(url)) {
            seen.add(url);
            existingUrls.add(url);
          }
        }
        
        // Update with merged URLs, prefer working status
        groups[key] = existing.copyWith(
          urls: existingUrls,
          isWorking: existing.isWorking || ch.isWorking,
          logo: existing.logo ?? ch.logo,
        );
      }
    }
    
    final result = groupOrder.map((k) => groups[k]!).toList();
    final merged = channels.length - result.length;
    if (merged > 0) {
      logger.info('PlaylistRepository: Consolidated $merged channels by name → ${result.length} unique');
    }
    return result;
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

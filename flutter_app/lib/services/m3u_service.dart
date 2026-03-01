import 'package:http/http.dart' as http;
import '../models/channel.dart';
import '../utils/error_handler.dart';
import '../utils/logger_service.dart';

/// Service for fetching and parsing M3U playlists
class M3UService {
  static const List<String> defaultRepositories = [
    // Main indices
    'https://iptv-org.github.io/iptv/index.m3u',
    'https://iptv-org.github.io/iptv/index.category.m3u',
    'https://iptv-org.github.io/iptv/index.country.m3u',
    'https://iptv-org.github.io/iptv/index.language.m3u',
    // Categories
    'https://iptv-org.github.io/iptv/categories/news.m3u',
    'https://iptv-org.github.io/iptv/categories/sports.m3u',
    'https://iptv-org.github.io/iptv/categories/entertainment.m3u',
    'https://iptv-org.github.io/iptv/categories/movies.m3u',
    'https://iptv-org.github.io/iptv/categories/music.m3u',
    'https://iptv-org.github.io/iptv/categories/kids.m3u',
    'https://iptv-org.github.io/iptv/categories/documentary.m3u',
    'https://iptv-org.github.io/iptv/categories/general.m3u',
    // Country-specific
    'https://iptv-org.github.io/iptv/countries/il.m3u',
    'https://iptv-org.github.io/iptv/languages/heb.m3u',
    // Community sources
    'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8',
  ];

  /// Custom Israeli channels with verified working CDN URLs
  static const List<Map<String, String>> customChannels = [
    // TV Channels
    {'name': 'Kan 11 News', 'url': 'https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/kan11/live.livx/playlist.m3u8', 'group': 'News', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Kan 11 Subtitled', 'url': 'https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/kan11_subs/live.livx/playlist.m3u8', 'group': 'General', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Kan Kids / Educational', 'url': 'https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/kan_edu/live.livx/playlist.m3u8', 'group': 'Kids', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Makan 33', 'url': 'https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/makan/live.livx/playlist.m3u8', 'group': 'News', 'country': 'Israel', 'language': 'Arabic'},
    {'name': 'Reshet 13', 'url': 'https://reshet.g-mana.live/media/87f59c77-03f6-4bad-a648-897e095e7360/mainManifest.m3u8', 'group': 'General', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Reshet 13 Alt', 'url': 'https://d18b0e6mopany4.cloudfront.net/out/v1/2f2bc414a3db4698a8e94b89eaf2da2a/index.m3u8', 'group': 'General', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Channel 14', 'url': 'https://ch14channel14.encoders.immergo.tv/app/2/streamPlaylist.m3u8', 'group': 'News', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Channel 14 Alt', 'url': 'https://r.il.cdn-redge.media/livehls/oil/ch14/live/ch14/live.livx/playlist.m3u8', 'group': 'News', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Channel 10 Business', 'url': 'https://r.il.cdn-redge.media/livehls/oil/calcala-live/live/channel10/live.livx/playlist.m3u8', 'group': 'News', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Kan 11 4K', 'url': 'https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/kan11_4k/live.livx/playlist.m3u8', 'group': 'General', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Knesset Channel', 'url': 'https://kneset.gostreaming.tv/p2-kneset/_definst_/myStream/index.m3u8', 'group': 'News', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Ynet Live', 'url': 'https://ynet-live-01.ynet-pic1.yit.co.il/ynet/live.m3u8', 'group': 'News', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Hala TV', 'url': 'https://gstream4.panet.co.il/edge/halaTV/chunks.m3u8', 'group': 'General', 'country': 'Israel', 'language': 'Arabic'},
    {'name': 'Kabbalah TV Hebrew', 'url': 'https://edge3.uk.kab.tv/live/tv66-heb-high/playlist.m3u8', 'group': 'Religious', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM TV', 'url': 'https://cdn.cybercdn.live/Radios_100FM/Video/playlist.m3u8', 'group': 'Music', 'country': 'Israel', 'language': 'Hebrew'},
    // Radio Channels
    {'name': 'Kan Bet / Reshet Bet', 'url': 'https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_reshet_bet/live.livx/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Kan Gimel', 'url': 'https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_gimel/live.livx/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Kan 88', 'url': 'https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_88/live.livx/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Kan Tarbut', 'url': 'https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_tarbut/live.livx/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Kan Moreshet', 'url': 'https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_moreshet/live.livx/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Kan Kol Hamuzika', 'url': 'https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_kol_hamuzika/live.livx/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Kan Reka', 'url': 'https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_reka/live.livx/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Radio Makan', 'url': 'https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/radio_makan/live.livx/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Arabic'},
    {'name': 'Galgalatz', 'url': 'https://glzwizzlv.bynetcdn.com/glglz_mp3', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Galei Zahal', 'url': 'https://glzwizzlv.bynetcdn.com/glz_mp3', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM Radio', 'url': 'https://cdn.cybercdn.live/Radios_100FM/Audio/icecast.audio', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM Radio HLS', 'url': 'https://cdn.cybercdn.live/Radios_100FM/Audio/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '103FM Radio', 'url': 'https://cdn.cybercdn.live/103FM/Live/icecast.audio', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '103FM Radio HLS', 'url': 'https://cdn.cybercdn.live/103FM/Live/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
  ];

  /// Fetch channels from an M3U URL
  static Future<List<Channel>> fetchFromUrl(String url) async {
    logger.info('Fetching M3U playlist from: $url');
    
    try {
      final response = await http.get(
        Uri.parse(url),
        headers: {'User-Agent': 'TV Viewer/1.9.2'},
      ).timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        // SEC-010: Enforce 50MB content size limit to prevent OOM on Android
        const maxContentSize = 50 * 1024 * 1024; // 50MB
        if (response.body.length > maxContentSize) {
          final error = ErrorHandler.m3uError(
            'too_large',
            'M3U content exceeds 50MB limit (${response.body.length} bytes) for URL: $url',
          );
          logger.error('M3U fetch rejected: ${error.getDetailedLog()}');
          throw error;
        }
        logger.info('M3U playlist fetched successfully (${response.body.length} bytes)');
        
        // Validate content before parsing
        if (response.body.isEmpty) {
          final error = ErrorHandler.m3uError('empty', 'Response body is empty for URL: $url');
          logger.error('M3U fetch failed: ${error.getDetailedLog()}');
          throw error;
        }
        
        if (!response.body.contains('#EXTM3U') && !response.body.contains('#EXTINF')) {
          final error = ErrorHandler.m3uError(
            'invalid',
            'Content does not appear to be a valid M3U playlist for URL: $url',
          );
          logger.warning('M3U validation warning: ${error.userMessage}');
          // Continue parsing anyway - some playlists might work without header
        }
        
        final channels = parseM3U(response.body);
        logger.info('Parsed ${channels.length} channels from M3U');
        return channels;
      } else {
        // Handle HTTP error status codes
        final error = ErrorHandler.handleHttpStatusCode(response.statusCode, url);
        logger.error('M3U fetch failed: ${error.getDetailedLog()}');
        throw error;
      }
    } catch (e, stackTrace) {
      if (e is AppError) {
        rethrow; // Already handled
      }
      
      final error = ErrorHandler.handle(e, stackTrace);
      logger.error('Error fetching M3U from $url', e, stackTrace);
      logger.error('Error details: ${error.getDetailedLog()}');
      throw error;
    }
  }

  /// Parse M3U content into Channel objects
  static List<Channel> parseM3U(String content) {
    logger.debug('Parsing M3U content (${content.length} bytes)');
    
    try {
      final channels = <Channel>[];
      final lines = content.split('\n');

      String? currentInfo;

      for (final line in lines) {
        final trimmed = line.trim();

        if (trimmed.startsWith('#EXTINF:')) {
          currentInfo = trimmed;
        } else if (trimmed.isNotEmpty &&
            !trimmed.startsWith('#') &&
            currentInfo != null) {
          // This is a URL
          if (trimmed.startsWith('http://') ||
              trimmed.startsWith('https://') ||
              trimmed.startsWith('rtmp://') ||
              trimmed.startsWith('rtsp://')) {
            try {
              channels.add(Channel.fromM3ULine(currentInfo, trimmed));
            } catch (e) {
              logger.warning('Failed to parse channel line: $currentInfo -> $trimmed', e);
              // Continue parsing other channels
            }
          }
          currentInfo = null;
        }
      }

      if (channels.isEmpty) {
        logger.warning('No channels found in M3U content');
        throw ErrorHandler.m3uError(
          'no_channels',
          'No valid channels found in M3U content (${lines.length} lines processed)',
        );
      }

      logger.info('Successfully parsed ${channels.length} channels from M3U');
      return channels;
    } catch (e, stackTrace) {
      if (e is AppError) {
        rethrow;
      }
      
      final error = ErrorHandler.m3uError(
        'parse',
        'Failed to parse M3U content: ${e.toString()}',
      );
      logger.error('M3U parsing failed', e, stackTrace);
      throw error;
    }
  }

  /// Fetch channels from all default repositories
  static Future<List<Channel>> fetchAllChannels({
    void Function(int current, int total)? onProgress,
  }) async {
    logger.info('Fetching channels from ${defaultRepositories.length} repositories');
    
    final allChannels = <Channel>[];
    final seenUrls = <String>{};
    final errors = <String, AppError>{};

    for (int i = 0; i < defaultRepositories.length; i++) {
      onProgress?.call(i, defaultRepositories.length);
      
      final repoUrl = defaultRepositories[i];
      logger.info('Fetching from repository ${i + 1}/${defaultRepositories.length}: $repoUrl');

      try {
        final channels = await fetchFromUrl(repoUrl);

        for (final channel in channels) {
          if (!seenUrls.contains(channel.url)) {
            seenUrls.add(channel.url);
            allChannels.add(channel);
          }
        }
        
        logger.info('Repository ${i + 1}: Added ${channels.length} channels (${allChannels.length} total)');
      } catch (e) {
        if (e is AppError) {
          errors[repoUrl] = e;
          logger.error('Failed to fetch from repository $repoUrl: ${e.userMessage}');
        } else {
          final appError = ErrorHandler.handle(e);
          errors[repoUrl] = appError;
          logger.error('Failed to fetch from repository $repoUrl', e);
        }
        // Continue with other repositories
      }
    }

    onProgress?.call(defaultRepositories.length, defaultRepositories.length);
    
    // Add custom Israeli channels (verified working CDN URLs)
    for (final custom in customChannels) {
      final url = custom['url']!;
      if (!seenUrls.contains(url)) {
        seenUrls.add(url);
        final group = custom['group'] ?? '';
        allChannels.add(Channel(
          name: custom['name']!,
          url: url,
          category: group,
          country: custom['country'],
          language: custom['language'],
          mediaType: group.toLowerCase() == 'radio' ? 'Radio' : 'TV',
        ));
      }
    }
    logger.info('Added ${customChannels.length} custom channels');
    
    // Log summary
    logger.info('Fetch complete: ${allChannels.length} total channels from ${defaultRepositories.length - errors.length}/${defaultRepositories.length} repositories');
    if (errors.isNotEmpty) {
      logger.warning('Failed repositories: ${errors.keys.join(', ')}');
    }
    
    // If no channels at all, throw an error
    if (allChannels.isEmpty) {
      final error = ErrorHandler.m3uError(
        'no_channels',
        'Failed to fetch channels from all ${defaultRepositories.length} repositories. Errors: ${errors.values.map((e) => e.code).join(', ')}',
      );
      logger.error('All repositories failed: ${error.getDetailedLog()}');
      throw error;
    }
    
    return allChannels;
  }

  /// Check if a stream URL is accessible
  static Future<bool> checkStream(String url) async {
    try {
      logger.debug('Checking stream accessibility: $url');
      
      final response = await http.head(
        Uri.parse(url),
        headers: {'User-Agent': 'TV Viewer/1.9.2'},
      ).timeout(const Duration(seconds: 5));

      final isAccessible = response.statusCode == 200 ||
          response.statusCode == 206 ||
          response.statusCode == 302 ||
          response.statusCode == 301;
      
      if (isAccessible) {
        logger.debug('Stream check passed: $url (status ${response.statusCode})');
      } else {
        logger.debug('Stream check failed: $url (status ${response.statusCode})');
      }
      
      return isAccessible;
    } catch (e) {
      logger.debug('Stream check error for $url: ${e.toString()}');
      return false;
    }
  }
}

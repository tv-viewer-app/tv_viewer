import 'package:http/http.dart' as http;
import '../models/channel.dart';
import '../utils/error_handler.dart';
import '../utils/logger_service.dart';

/// Service for fetching and parsing M3U playlists
class M3UService {
  static const List<String> defaultRepositories = [
    'https://iptv-org.github.io/iptv/index.m3u',
    'https://iptv-org.github.io/iptv/index.category.m3u',
  ];

  /// Fetch channels from an M3U URL
  static Future<List<Channel>> fetchFromUrl(String url) async {
    logger.info('Fetching M3U playlist from: $url');
    
    try {
      final response = await http.get(
        Uri.parse(url),
        headers: {'User-Agent': 'TV Viewer/1.5.0'},
      ).timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
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
        headers: {'User-Agent': 'TV Viewer/1.5.0'},
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

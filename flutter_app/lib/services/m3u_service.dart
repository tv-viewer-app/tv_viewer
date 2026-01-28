import 'package:http/http.dart' as http;
import '../models/channel.dart';

/// Service for fetching and parsing M3U playlists
class M3UService {
  static const List<String> defaultRepositories = [
    'https://iptv-org.github.io/iptv/index.m3u',
    'https://iptv-org.github.io/iptv/index.category.m3u',
  ];

  /// Fetch channels from an M3U URL
  static Future<List<Channel>> fetchFromUrl(String url) async {
    try {
      final response = await http.get(
        Uri.parse(url),
        headers: {'User-Agent': 'TV Viewer/1.4.4'},
      ).timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        return parseM3U(response.body);
      }
    } catch (e) {
      print('Error fetching M3U from $url: $e');
    }
    return [];
  }

  /// Parse M3U content into Channel objects
  static List<Channel> parseM3U(String content) {
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
          channels.add(Channel.fromM3ULine(currentInfo, trimmed));
        }
        currentInfo = null;
      }
    }

    return channels;
  }

  /// Fetch channels from all default repositories
  static Future<List<Channel>> fetchAllChannels({
    void Function(int current, int total)? onProgress,
  }) async {
    final allChannels = <Channel>[];
    final seenUrls = <String>{};

    for (int i = 0; i < defaultRepositories.length; i++) {
      onProgress?.call(i, defaultRepositories.length);

      final channels = await fetchFromUrl(defaultRepositories[i]);

      for (final channel in channels) {
        if (!seenUrls.contains(channel.url)) {
          seenUrls.add(channel.url);
          allChannels.add(channel);
        }
      }
    }

    onProgress?.call(defaultRepositories.length, defaultRepositories.length);
    return allChannels;
  }

  /// Check if a stream URL is accessible
  static Future<bool> checkStream(String url) async {
    try {
      final response = await http.head(
        Uri.parse(url),
        headers: {'User-Agent': 'TV Viewer/1.4.4'},
      ).timeout(const Duration(seconds: 5));

      return response.statusCode == 200 ||
          response.statusCode == 206 ||
          response.statusCode == 302 ||
          response.statusCode == 301;
    } catch (e) {
      return false;
    }
  }
}

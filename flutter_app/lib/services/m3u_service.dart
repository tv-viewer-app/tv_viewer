import 'package:http/http.dart' as http;
import '../models/channel.dart';
import '../utils/error_handler.dart';
import '../utils/logger_service.dart';
import 'fmstream_service.dart';
import 'shared_db_service.dart';

/// Service for fetching and parsing M3U playlists
class M3UService {
  static const List<String> defaultRepositories = [
    // Primary comprehensive index (contains all non-NSFW channels)
    'https://iptv-org.github.io/iptv/index.m3u',
    // Country-specific priority sources
    'https://iptv-org.github.io/iptv/countries/il.m3u',
    'https://iptv-org.github.io/iptv/countries/us.m3u',
    'https://iptv-org.github.io/iptv/countries/uk.m3u',
    'https://iptv-org.github.io/iptv/languages/heb.m3u',
    'https://gist.githubusercontent.com/serginholssfilmes/ba590a457da0192f4c14a19f1d3704ec/raw',
    // Free-TV curated playlists (quality-focused, HD where possible)
    'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8',
    'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlists/playlist_usa.m3u8',
    'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlists/playlist_uk.m3u8',
    'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlists/playlist_israel.m3u8',
    'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlists/playlist_france.m3u8',
    'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlists/playlist_germany.m3u8',
    'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlists/playlist_spain.m3u8',
    'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlists/playlist_italy.m3u8',
    'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlists/playlist_zz_news_en.m3u8',
    'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlists/playlist_zz_movies.m3u8',
    'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlists/playlist_zz_documentaries_en.m3u8',
    // Community sources
    'https://raw.githubusercontent.com/djthawks/IPTV-1/master/all/grouped_by_content.m3u',
    'https://raw.githubusercontent.com/djthawks/IPTV-1/master/all/international.m3u',
    'https://raw.githubusercontent.com/RokuIL/Live-From-Israel/master/NextPVRChannels.m3u8',
    'https://raw.githubusercontent.com/iptv-org/iptv/master/streams/il.m3u',
    'https://de1.api.radio-browser.info/m3u/stations/bycountry/israel',
    'https://de1.api.radio-browser.info/m3u/stations/bycountry/united%20states',
    'https://de1.api.radio-browser.info/m3u/stations/bycountry/united%20kingdom',
    // Smart TV platform channels
    'https://www.apsattv.com/xumo.m3u',
    'https://www.apsattv.com/lg.m3u',
    'https://www.apsattv.com/rok.m3u',
    'https://www.apsattv.com/redbox.m3u',
    'https://www.apsattv.com/xiaomi.m3u',
    'https://www.apsattv.com/tablo.m3u',
    'https://www.apsattv.com/vizio.m3u',
    'https://www.apsattv.com/firetv.m3u',
    'https://www.apsattv.com/klowd.m3u',
  ];

  /// Adult/NSFW repositories — only fetched when adult content is enabled
  static const List<String> adultRepositories = [
    'https://iptv-org.github.io/iptv/categories/xxx.m3u',
    'https://iptv-org.github.io/iptv/index.nsfw.m3u',
    'https://cdn.adultiptv.net/lists/all.m3u8',
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
    {'name': 'Reshet 13 Subtitled', 'url': 'https://reshet.g-mana.live/media/4607e158-e4d4-4e18-9160-3dc3ea9bc677/mainManifest.m3u8', 'group': 'General', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Reshet 13 Comedy', 'url': 'https://d15ds134q59udk.cloudfront.net/out/v1/fbba879221d045598540ee783b140fe2/index.m3u8', 'group': 'Entertainment', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Reshet 13 Nofesh', 'url': 'https://d1yd8hohnldm33.cloudfront.net/out/v1/19dee23c2cc24f689bd4e1288661ee0c/index.m3u8', 'group': 'Entertainment', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Reshet 13 Reality', 'url': 'https://d2dffl3588mvfk.cloudfront.net/out/v1/d8e15050ca4148aab0ee387a5e2eb46b/index.m3u8', 'group': 'Entertainment', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Big Brother Israel', 'url': 'https://d2lckchr9cxrss.cloudfront.net/out/v1/c73af7694cce4767888c08a7534b503c/index.m3u8', 'group': 'Entertainment', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Channel 14', 'url': 'https://ch14channel14.encoders.immergo.tv/app/2/streamPlaylist.m3u8', 'group': 'News', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Channel 14 Alt', 'url': 'https://r.il.cdn-redge.media/livehls/oil/ch14/live/ch14/live.livx/playlist.m3u8', 'group': 'News', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Channel 10 Business', 'url': 'https://r.il.cdn-redge.media/livehls/oil/calcala-live/live/channel10/live.livx/playlist.m3u8', 'group': 'News', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Kan 11 4K', 'url': 'https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/kan11_4k/live.livx/playlist.m3u8', 'group': 'General', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Knesset Channel', 'url': 'https://kneset.gostreaming.tv/p2-kneset/_definst_/myStream/index.m3u8', 'group': 'News', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': 'Ynet Live', 'url': 'https://hls-video-ynet.ynethd.com/ynet/live.m3u8', 'group': 'News', 'country': 'Israel', 'language': 'Hebrew'},
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
    // 100FM Digital Sub-Channels (gb25.streamgates.net CDN)
    {'name': '100FM Hits', 'url': 'https://gb25.streamgates.net/radios-audio/100Hits/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM Hip Hop', 'url': 'https://gb25.streamgates.net/radios-audio/100HipHop/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM Dance', 'url': 'https://gb25.streamgates.net/radios-audio/100Dance/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM Trance', 'url': 'https://gb25.streamgates.net/radios-audio/100Trance/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM Club', 'url': 'https://gb25.streamgates.net/radios-audio/100Club/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM Top 40', 'url': 'https://gb25.streamgates.net/radios-audio/100Top40/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM 90s', 'url': 'https://gb25.streamgates.net/radios-audio/10090s/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM 80s', 'url': 'https://gb25.streamgates.net/radios-audio/10080s/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM Workout', 'url': 'https://gb25.streamgates.net/radios-audio/100Workout/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM Chillout', 'url': 'https://gb25.streamgates.net/radios-audio/100Chillout/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM Retro', 'url': 'https://gb25.streamgates.net/radios-audio/100Retro/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM Latin', 'url': 'https://gb25.streamgates.net/radios-audio/100Latin/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM Jazz', 'url': 'https://gb25.streamgates.net/radios-audio/100Jazz/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM Deep', 'url': 'https://gb25.streamgates.net/radios-audio/100Deep/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM Classic Rock', 'url': 'https://gb25.streamgates.net/radios-audio/100ClassicRock/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM TikTok', 'url': 'https://gb25.streamgates.net/radios-audio/100TikTok/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM DJ Set', 'url': 'https://gb25.streamgates.net/radios-audio/100DJSet/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM K-Pop', 'url': 'https://gb25.streamgates.net/radios-audio/100KPop/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
    {'name': '100FM Mizrachit', 'url': 'https://gb25.streamgates.net/radios-audio/100Mizrachit/playlist.m3u8', 'group': 'Radio', 'country': 'Israel', 'language': 'Hebrew'},
  ];

  /// Fetch channels from an M3U URL
  static Future<List<Channel>> fetchFromUrl(String url) async {
    logger.info('Fetching M3U playlist from: $url');
    
    try {
      final response = await http.get(
        Uri.parse(url),
        headers: {'User-Agent': 'TV Viewer/2.2.3'},
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
    bool includeAdult = false,
  }) async {
    // Try Supabase shared database first for unified channel list
    final sharedDb = SharedDbService();
    List<Channel> supabaseChannels = [];
    try {
      final dbChannels = await sharedDb.fetchChannels();
      if (dbChannels.isNotEmpty) {
        for (final ch in dbChannels) {
          final urls = ch['urls'];
          final urlList = urls is List ? urls.cast<String>() : <String>[];
          if (urlList.isEmpty) continue;
          supabaseChannels.add(Channel(
            name: ch['name'] as String? ?? '',
            url: urlList.first,
            urls: urlList,
            category: ch['category'] as String? ?? 'Other',
            country: ch['country'] as String?,
            logo: ch['logo'] as String?,
            mediaType: (ch['media_type'] as String?) ?? 'TV',
          ));
        }
        logger.info('Loaded ${supabaseChannels.length} channels from Supabase');
      }
    } catch (e) {
      logger.warning('Supabase channel fetch failed (falling back to M3U): $e');
    }

    final repos = [...defaultRepositories];
    if (includeAdult) {
      repos.addAll(adultRepositories);
    }

    logger.info('Fetching channels from ${repos.length} repositories (adult: $includeAdult)');
    
    final allChannels = <Channel>[];
    final seenUrls = <String>{};
    final errors = <String, AppError>{};

    for (int i = 0; i < repos.length; i++) {
      onProgress?.call(i, repos.length);
      final repoUrl = repos[i];
      logger.info('Fetching from repository ${i + 1}/${repos.length}: $repoUrl');

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

    onProgress?.call(repos.length, repos.length);
    
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
    
    // Fetch FMStream radio stations (#32)
    try {
      logger.info('Fetching FMStream.org radio stations...');
      final fmStations = await FMStreamService.fetchFromFMStream();
      int added = 0;
      for (final station in fmStations) {
        if (!seenUrls.contains(station.url)) {
          seenUrls.add(station.url);
          allChannels.add(station);
          added++;
        }
      }
      logger.info('FMStream: Added $added radio stations (${fmStations.length} fetched, ${fmStations.length - added} duplicates)');
    } catch (e) {
      logger.warning('FMStream fetch failed (non-fatal): $e');
    }
    
    // Log summary
    logger.info('Fetch complete: ${allChannels.length} total channels from ${repos.length - errors.length}/${repos.length} repositories');
    if (errors.isNotEmpty) {
      logger.warning('Failed repositories: ${errors.keys.join(', ')}');
    }
    
    // If no channels at all (from both Supabase and M3U), throw an error
    if (allChannels.isEmpty && supabaseChannels.isEmpty) {
      final error = ErrorHandler.m3uError(
        'no_channels',
        'Failed to fetch channels from all ${repos.length} repositories. Errors: ${errors.values.map((e) => e.code).join(', ')}',
      );
      logger.error('All repositories failed: ${error.getDetailedLog()}');
      throw error;
    }
    
    // Consolidate channels with same normalized name into multi-URL entries
    // Merge Supabase channels with freshly-fetched M3U channels
    final mergedChannels = <Channel>[];
    final mergedUrls = <String>{};
    
    // Start with Supabase channels (authoritative, already consolidated)
    for (final ch in supabaseChannels) {
      for (final u in ch.urls) {
        mergedUrls.add(u);
      }
      mergedChannels.add(ch);
    }
    
    // Add M3U channels not already in Supabase
    for (final ch in allChannels) {
      if (!mergedUrls.contains(ch.url)) {
        mergedUrls.add(ch.url);
        mergedChannels.add(ch);
      }
    }
    
    final consolidated = _consolidateChannels(mergedChannels);
    logger.info('Consolidated ${mergedChannels.length} → ${consolidated.length} channels (${supabaseChannels.length} from Supabase)');
    
    // Contribute newly discovered channels back to Supabase
    if (allChannels.length > supabaseChannels.length) {
      _contributeNewChannels(sharedDb, allChannels, supabaseChannels);
    }
    
    return consolidated;
  }

  /// Fire-and-forget: contribute newly discovered M3U channels to Supabase
  static void _contributeNewChannels(
    SharedDbService sharedDb,
    List<Channel> m3uChannels,
    List<Channel> supabaseChannels,
  ) {
    final existingUrls = <String>{};
    for (final ch in supabaseChannels) {
      for (final u in ch.urls) {
        existingUrls.add(u);
      }
    }
    final newChannels = m3uChannels
        .where((ch) => !existingUrls.contains(ch.url))
        .map((ch) => <String, dynamic>{
              'name': ch.name,
              'url': ch.url,
              'urls': ch.urls,
              'category': ch.category,
              'country': ch.country ?? 'Unknown',
              'logo': ch.logo ?? '',
              'media_type': ch.mediaType,
              'source': 'flutter-m3u',
            })
        .toList();
    if (newChannels.isNotEmpty) {
      logger.info('Contributing ${newChannels.length} new channels to Supabase');
      sharedDb.contributeChannels(newChannels);
    }
  }

  /// Quality/variant suffixes to strip when normalizing channel names
  static final _qualitySuffixPattern = RegExp(
    r'\s*[\(\[](720p|1080p|480p|360p|4k|hd|sd|fhd|uhd|h\.?265|h\.?264|hevc|'
    r'alt|backup|sub|subtitled|כתוביות|mirror|low|high|multi)[)\]]'
    r'|\s+(720p|1080p|480p|360p|4k|hd|sd|fhd|uhd|h\.?265|h\.?264|hevc)$'
    r'|\s+alt$',
    caseSensitive: false,
  );

  /// Explicit alias groups: channels that should merge into one multi-URL entry.
  /// Key = canonical name, values = alternative names (case-insensitive).
  static const Map<String, List<String>> _channelAliases = {
    'kan 11': ['kan 11 news', 'kan 11 subtitled', 'kan 11 4k', 'כאן 11', 'kan 11 israel'],
    'kan kids': ['kan kids / kan educational', 'kan kids / educational', 'kan educational', 'kan edu', 'כאן חינוכית'],
    'reshet 13': ['reshet 13 alt', 'reshet 13 subtitled'],
  };

  /// Build reverse lookup: alias → canonical name
  static Map<String, String>? _aliasLookup;
  static Map<String, String> _getAliasLookup() {
    if (_aliasLookup != null) return _aliasLookup!;
    _aliasLookup = {};
    for (final entry in _channelAliases.entries) {
      _aliasLookup![entry.key] = entry.key;
      for (final alias in entry.value) {
        _aliasLookup![alias] = entry.key;
      }
    }
    return _aliasLookup!;
  }

  /// Normalize a channel name for grouping (strip quality/variant suffixes)
  /// Handles Hebrew/Arabic aliases separated by dash (e.g., "כאן 11 - Kan 11")
  static String _normalizeNameForGrouping(String name) {
    String normalized = name.trim();
    // Multi-pass strip quality suffixes
    for (int i = 0; i < 3; i++) {
      final before = normalized;
      normalized = normalized.replaceAll(_qualitySuffixPattern, '').trim();
      if (normalized == before) break;
    }
    // Handle " - " separator: keep Latin-dominant part (like Python version)
    if (normalized.contains(' - ') || normalized.contains(' – ') || normalized.contains(' — ')) {
      final parts = normalized.split(RegExp(r'\s+[-–—]\s+'));
      if (parts.length >= 2) {
        String? bestLatin;
        for (final part in parts) {
          final stripped = part.trim();
          if (stripped.isEmpty) continue;
          final latinChars = stripped.codeUnits.where((c) => (c >= 65 && c <= 90) || (c >= 97 && c <= 122)).length;
          final alphaChars = stripped.runes.where((r) => String.fromCharCode(r).contains(RegExp(r'[\p{L}]', unicode: true))).length;
          if (alphaChars > 0 && latinChars / alphaChars > 0.5) {
            bestLatin ??= stripped;
          }
        }
        if (bestLatin != null) normalized = bestLatin;
      }
    }
    final key = normalized.toLowerCase().trim();
    // Check explicit alias mapping
    final lookup = _getAliasLookup();
    return lookup[key] ?? key;
  }

  /// Consolidate channels: merge entries with same normalized name + country
  /// into single multi-URL Channel objects for failover
  static List<Channel> _consolidateChannels(List<Channel> channels) {
    // Group by normalized name + country
    final groups = <String, List<Channel>>{};
    for (final ch in channels) {
      final key = '${_normalizeNameForGrouping(ch.name)}|${(ch.country ?? '').toLowerCase()}';
      groups.putIfAbsent(key, () => []).add(ch);
    }

    final result = <Channel>[];
    for (final group in groups.values) {
      if (group.length == 1) {
        result.add(group.first);
        continue;
      }
      // Merge all URLs, preserving order (first seen = primary)
      final allUrls = <String>[];
      final seenUrls = <String>{};
      for (final ch in group) {
        for (final url in ch.urls) {
          if (seenUrls.add(url)) {
            allUrls.add(url);
          }
        }
      }
      // Use first channel's metadata as canonical, with all URLs
      final primary = group.first;
      result.add(primary.copyWith(urls: allUrls));
    }
    return result;
  }

  /// Check if a stream URL is accessible
  static Future<bool> checkStream(String url) async {
    try {
      logger.debug('Checking stream accessibility: $url');
      
      final response = await http.head(
        Uri.parse(url),
        headers: {'User-Agent': 'TV Viewer/2.2.3'},
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

import 'package:http/http.dart' as http;
import '../models/channel.dart';
import '../utils/error_handler.dart';
import '../utils/logger_service.dart';

/// Service for fetching and parsing FMStream.org radio directory
class FMStreamService {
  static const String fmstreamBaseUrl = 'https://fmstream.org';
  static const String fmstreamDirectoryUrl = 'https://fmstream.org/index.html';
  
  /// Fetch radio stations from FMStream.org
  static Future<List<Channel>> fetchFromFMStream({
    void Function(int current, int total)? onProgress,
  }) async {
    logger.info('Fetching radio stations from FMStream.org');
    
    try {
      onProgress?.call(0, 100);
      
      // Fetch HTML directory
      logger.info('Fetching FMStream directory from: $fmstreamDirectoryUrl');
      final response = await http.get(
        Uri.parse(fmstreamDirectoryUrl),
        headers: {
          'User-Agent': 'TV Viewer/2.0.0',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        },
      ).timeout(const Duration(seconds: 30));
      
      onProgress?.call(30, 100);
      
      if (response.statusCode == 200) {
        logger.info('FMStream directory fetched successfully (${response.body.length} bytes)');
        
        // Validate content before parsing
        if (response.body.isEmpty) {
          final error = _fmstreamError('empty', 'Response body is empty from FMStream.org');
          logger.error('FMStream fetch failed: ${error.getDetailedLog()}');
          throw error;
        }
        
        onProgress?.call(40, 100);
        
        // Parse HTML and extract stations
        final stations = parseHTML(response.body);
        
        onProgress?.call(80, 100);
        
        // Deduplicate stations by URL
        final deduplicatedStations = deduplicateStations(stations);
        
        onProgress?.call(100, 100);
        
        logger.info('Successfully fetched ${deduplicatedStations.length} radio stations from FMStream.org (${stations.length} before dedup)');
        return deduplicatedStations;
      } else {
        // Handle HTTP error status codes
        final error = ErrorHandler.handleHttpStatusCode(response.statusCode, fmstreamDirectoryUrl);
        logger.error('FMStream fetch failed: ${error.getDetailedLog()}');
        throw error;
      }
    } catch (e, stackTrace) {
      if (e is AppError) {
        rethrow; // Already handled
      }
      
      final error = ErrorHandler.handle(e, stackTrace);
      logger.error('Error fetching from FMStream.org', e, stackTrace);
      logger.error('Error details: ${error.getDetailedLog()}');
      throw error;
    }
  }
  
  /// Parse HTML directory listing and extract radio stations
  static List<Channel> parseHTML(String html) {
    logger.debug('Parsing FMStream HTML (${html.length} bytes)');
    
    try {
      final stations = <Channel>[];
      
      // Extract stations using multiple parsing strategies for robustness
      
      // Strategy 1: Parse directory links to station pages
      final stationsFromLinks = _extractStationsFromLinks(html);
      stations.addAll(stationsFromLinks);
      logger.debug('Strategy 1 (directory links): Found ${stationsFromLinks.length} stations');
      
      // Strategy 2: Parse embedded playlist/stream links
      final stationsFromStreams = _extractStationsFromStreamLinks(html);
      stations.addAll(stationsFromStreams);
      logger.debug('Strategy 2 (stream links): Found ${stationsFromStreams.length} stations');
      
      // Strategy 3: Parse table/list structures (common in radio directories)
      final stationsFromTables = _extractStationsFromTables(html);
      stations.addAll(stationsFromTables);
      logger.debug('Strategy 3 (tables): Found ${stationsFromTables.length} stations');
      
      if (stations.isEmpty) {
        logger.warning('No stations found in FMStream HTML');
        throw _fmstreamError(
          'no_stations',
          'No valid radio stations found in FMStream.org directory',
        );
      }
      
      logger.info('Successfully parsed ${stations.length} stations from FMStream HTML');
      return stations;
    } catch (e, stackTrace) {
      if (e is AppError) {
        rethrow;
      }
      
      final error = _fmstreamError(
        'parse',
        'Failed to parse FMStream HTML: ${e.toString()}',
      );
      logger.error('FMStream HTML parsing failed', e, stackTrace);
      throw error;
    }
  }
  
  /// Extract stations from directory page links
  /// Looks for links to individual station pages
  static List<Channel> _extractStationsFromLinks(String html) {
    final stations = <Channel>[];
    
    try {
      // Pattern 1: Standard anchor tags with station info
      // <a href="station.html">Station Name</a>
      // <a href="station.html">Station Name - Country</a>
      final linkPattern = RegExp(
        r"""<a\s+[^>]*href=["']([\w\-/\.]+\.(?:html?|php|asp)[^"']*?)["'][^>]*>([^<]+)</a>""",
        caseSensitive: false,
      );
      
      for (final match in linkPattern.allMatches(html)) {
        final linkUrl = match.group(1);
        final linkText = match.group(2)?.trim() ?? '';
        
        if (linkUrl == null || linkText.isEmpty) continue;
        
        // Skip navigation links, indices, etc.
        if (_isNavigationLink(linkText)) continue;
        
        // Extract station info from link text and URL
        final stationInfo = _parseStationInfo(linkText, linkUrl, html);
        if (stationInfo != null) {
          stations.add(stationInfo);
        }
      }
      
      // Pattern 2: Links with data attributes (modern HTML)
      final dataLinkPattern = RegExp(
        r"""<a\s+[^>]*data-station=["']([^"']+)["'][^>]*data-url=["']([^"']+)["'][^>]*>""",
        caseSensitive: false,
      );
      
      for (final match in dataLinkPattern.allMatches(html)) {
        final stationName = match.group(1)?.trim();
        final streamUrl = match.group(2)?.trim();
        
        if (stationName != null && streamUrl != null && streamUrl.isNotEmpty) {
          stations.add(_createChannel(
            name: stationName,
            url: streamUrl,
            country: _extractCountryFromContext(match.start, html),
            genre: _extractGenreFromContext(match.start, html),
          ));
        }
      }
    } catch (e) {
      logger.warning('Error extracting stations from links', e);
    }
    
    return stations;
  }
  
  /// Extract stations from direct stream links in HTML
  static List<Channel> _extractStationsFromStreamLinks(String html) {
    final stations = <Channel>[];
    final seenUrls = <String>{};
    
    try {
      // Pattern for stream URLs: .pls, .m3u, /stream, etc.
      final streamPattern = RegExp(
        r"""(https?://[^\s"'<>]+\.(?:pls|m3u|mp3|aac|ogg)(?:\?[^\s"'<>]*)?|https?://[^\s"'<>]+/stream(?:/[^\s"'<>]*)?)""",
        caseSensitive: false,
      );
      
      for (final match in streamPattern.allMatches(html)) {
        final streamUrl = match.group(1);
        if (streamUrl == null || seenUrls.contains(streamUrl)) continue;
        
        seenUrls.add(streamUrl);
        
        // Extract station name from surrounding context
        final context = _getContextAroundMatch(match.start, html, 200);
        final stationName = _extractStationNameFromContext(context, streamUrl);
        final country = _extractCountryFromContext(match.start, html);
        final genre = _extractGenreFromContext(match.start, html);
        final bitrate = _extractBitrateFromContext(match.start, html);
        
        stations.add(_createChannel(
          name: stationName,
          url: streamUrl,
          country: country,
          genre: genre,
          bitrate: bitrate,
        ));
      }
    } catch (e) {
      logger.warning('Error extracting stations from stream links', e);
    }
    
    return stations;
  }
  
  /// Extract stations from table structures
  static List<Channel> _extractStationsFromTables(String html) {
    final stations = <Channel>[];
    
    try {
      // Pattern for table rows with station data
      // <tr><td>Station Name</td><td>Country</td><td>Genre</td><td><a href="stream">Play</a></td></tr>
      final tableRowPattern = RegExp(
        r'<tr[^>]*>(.*?)</tr>',
        caseSensitive: false,
        dotAll: true,
      );
      
      for (final rowMatch in tableRowPattern.allMatches(html)) {
        final rowContent = rowMatch.group(1) ?? '';
        
        // Extract cells
        final cellPattern = RegExp(r'<td[^>]*>(.*?)</td>', caseSensitive: false, dotAll: true);
        final cells = cellPattern.allMatches(rowContent).map((m) => m.group(1)?.trim() ?? '').toList();
        
        if (cells.length < 2) continue;
        
        // Try to identify station data
        String? stationName;
        String? country;
        String? genre;
        String? streamUrl;
        int? bitrate;
        
        for (final cell in cells) {
          // Check for stream URL
          final urlMatch = RegExp(r"""href=["'](https?://[^"']+)["']""", caseSensitive: false).firstMatch(cell);
          if (urlMatch != null) {
            streamUrl = urlMatch.group(1);
          }
          
          // Check for bitrate
          final bitrateMatch = RegExp(r'(\d+)\s*k?bps', caseSensitive: false).firstMatch(cell);
          if (bitrateMatch != null) {
            bitrate = int.tryParse(bitrateMatch.group(1) ?? '');
          }
          
          // Extract text content (remove HTML tags)
          final textContent = cell.replaceAll(RegExp(r'<[^>]*>'), '').trim();
          if (textContent.isEmpty) continue;
          
          // Heuristics to identify cell content
          if (stationName == null && textContent.length > 2 && !_isCountryName(textContent) && !_isGenreName(textContent)) {
            stationName = textContent;
          } else if (country == null && _isCountryName(textContent)) {
            country = textContent;
          } else if (genre == null && _isGenreName(textContent)) {
            genre = textContent;
          }
        }
        
        // Create channel if we have at least name and URL
        if (stationName != null && streamUrl != null && streamUrl.isNotEmpty) {
          stations.add(_createChannel(
            name: stationName,
            url: streamUrl,
            country: country,
            genre: genre,
            bitrate: bitrate,
          ));
        }
      }
    } catch (e) {
      logger.warning('Error extracting stations from tables', e);
    }
    
    return stations;
  }
  
  /// Parse station info from link text and URL
  static Channel? _parseStationInfo(String linkText, String linkUrl, String fullHtml) {
    try {
      // Extract station name and metadata from link text
      String stationName = linkText;
      String? country;
      String? genre;
      
      // Pattern: "Station Name - Country" or "Station Name (Country)"
      final nameCountryMatch = RegExp(r'^(.+?)\s*[-–]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$').firstMatch(linkText);
      if (nameCountryMatch != null) {
        stationName = nameCountryMatch.group(1)?.trim() ?? stationName;
        country = nameCountryMatch.group(2)?.trim();
      }
      
      final nameCountryParenMatch = RegExp(r'^(.+?)\s*\(([^)]+)\)$').firstMatch(linkText);
      if (nameCountryParenMatch != null) {
        stationName = nameCountryParenMatch.group(1)?.trim() ?? stationName;
        final info = nameCountryParenMatch.group(2)?.trim();
        if (info != null && _isCountryName(info)) {
          country = info;
        } else if (info != null && _isGenreName(info)) {
          genre = info;
        }
      }
      
      // Try to extract stream URL from station page
      // For now, construct a potential stream URL
      String? streamUrl;
      
      if (linkUrl.startsWith('http')) {
        streamUrl = linkUrl;
      } else {
        streamUrl = '$fmstreamBaseUrl/$linkUrl';
      }
      
      // If this is a station page, we need to fetch it to get the actual stream URL
      // For now, try to find stream references near this link in the HTML
      final linkIndex = fullHtml.indexOf(linkText);
      if (linkIndex != -1) {
        final context = _getContextAroundMatch(linkIndex, fullHtml, 500);
        final contextStreamUrl = _extractStreamUrlFromContext(context);
        if (contextStreamUrl != null) {
          streamUrl = contextStreamUrl;
        }
      }
      
      // Only create channel if we have a valid stream URL
      if (streamUrl != null && _isValidStreamUrl(streamUrl)) {
        return _createChannel(
          name: stationName,
          url: streamUrl,
          country: country,
          genre: genre,
        );
      }
    } catch (e) {
      logger.debug('Error parsing station info from link: $linkText', e);
    }
    
    return null;
  }
  
  /// Create a Channel object with Radio media type
  static Channel _createChannel({
    required String name,
    required String url,
    String? country,
    String? genre,
    int? bitrate,
  }) {
    return Channel(
      name: name.trim(),
      url: url.trim(),
      category: genre,
      country: country,
      mediaType: 'Radio', // Always Radio for FMStream
      bitrate: bitrate,
    );
  }
  
  /// Deduplicate stations by URL, preferring higher bitrate
  static List<Channel> deduplicateStations(List<Channel> stations) {
    final urlToStation = <String, Channel>{};
    
    for (final station in stations) {
      final existing = urlToStation[station.url];
      
      if (existing == null) {
        // First occurrence - add it
        urlToStation[station.url] = station;
      } else {
        // Duplicate found - prefer higher bitrate or better metadata
        final shouldReplace = _shouldReplaceStation(existing, station);
        
        if (shouldReplace) {
          urlToStation[station.url] = station;
        }
      }
    }
    
    final deduped = urlToStation.values.toList();
    final removed = stations.length - deduped.length;
    if (removed > 0) {
      logger.info('Deduplication: removed $removed duplicate stations');
    }
    
    return deduped;
  }
  
  /// Determine if new station should replace existing one
  /// Prefers higher bitrate, then metadata completeness
  static bool _shouldReplaceStation(Channel existing, Channel newStation) {
    // Prefer higher bitrate
    if (newStation.bitrate != null && existing.bitrate != null) {
      if (newStation.bitrate! > existing.bitrate!) {
        return true;
      } else if (newStation.bitrate! < existing.bitrate!) {
        return false;
      }
    } else if (newStation.bitrate != null && existing.bitrate == null) {
      return true;
    } else if (newStation.bitrate == null && existing.bitrate != null) {
      return false;
    }
    
    // Compare metadata completeness
    final newScore = _metadataScore(newStation);
    final existingScore = _metadataScore(existing);
    
    return newScore > existingScore;
  }
  
  /// Calculate metadata completeness score
  static int _metadataScore(Channel channel) {
    int score = 0;
    if (channel.name.isNotEmpty && channel.name != 'Unknown') score += 2;
    if (channel.category != null && channel.category!.isNotEmpty) score += 1;
    if (channel.country != null && channel.country!.isNotEmpty) score += 1;
    if (channel.logo != null && channel.logo!.isNotEmpty) score += 1;
    if (channel.bitrate != null) score += 1;
    return score;
  }
  
  /// Get text context around a match position
  static String _getContextAroundMatch(int position, String text, int range) {
    final start = (position - range).clamp(0, text.length);
    final end = (position + range).clamp(0, text.length);
    return text.substring(start, end);
  }
  
  /// Extract station name from surrounding context
  static String _extractStationNameFromContext(String context, String streamUrl) {
    // Try to find station name in context
    
    // Pattern 1: Text before the stream URL
    final beforePattern = RegExp(r"""(?:title|name|station)[=:"'>\s]+([^<>"']+)""", caseSensitive: false);
    final beforeMatch = beforePattern.firstMatch(context);
    if (beforeMatch != null) {
      final name = beforeMatch.group(1)?.trim();
      if (name != null && name.length > 2) {
        return _cleanStationName(name);
      }
    }
    
    // Pattern 2: Extract from URL (e.g., http://stream.example.com/jazz_radio)
    final urlMatch = RegExp(r'/([a-z0-9_-]+?)(?:_stream|_radio|\.\w+|$)', caseSensitive: false).firstMatch(streamUrl);
    if (urlMatch != null) {
      final name = urlMatch.group(1)?.replaceAll('_', ' ').replaceAll('-', ' ').trim();
      if (name != null && name.length > 2) {
        return _capitalizeWords(name);
      }
    }
    
    // Pattern 3: Extract from domain (e.g., jazzradio.com)
    final domainMatch = RegExp(r'https?://(?:www\.)?([a-z0-9-]+)', caseSensitive: false).firstMatch(streamUrl);
    if (domainMatch != null) {
      final domain = domainMatch.group(1)?.replaceAll('-', ' ').trim();
      if (domain != null && domain.length > 2) {
        return _capitalizeWords(domain);
      }
    }
    
    // Fallback
    return 'Radio Station';
  }
  
  /// Extract country from surrounding context
  static String? _extractCountryFromContext(int position, String html) {
    final context = _getContextAroundMatch(position, html, 300);
    
    // Pattern: country="..." or data-country="..."
    final attrMatch = RegExp(r"""country=["']([^"']+)["']""", caseSensitive: false).firstMatch(context);
    if (attrMatch != null) {
      return attrMatch.group(1)?.trim();
    }
    
    // Pattern: <span class="country">Country</span>
    final spanMatch = RegExp(r"""<span[^>]*class=["'][^"']*country[^"']*["'][^>]*>([^<]+)</span>""", caseSensitive: false).firstMatch(context);
    if (spanMatch != null) {
      final country = spanMatch.group(1)?.trim();
      if (country != null && _isCountryName(country)) {
        return country;
      }
    }
    
    // Pattern: Common country names in text
    final countryPattern = RegExp(r'\b(USA|UK|Canada|France|Germany|Spain|Italy|Australia|Japan|Brazil|Mexico|Russia|China|India|United States|United Kingdom)\b', caseSensitive: false);
    final countryMatch = countryPattern.firstMatch(context);
    if (countryMatch != null) {
      return countryMatch.group(1);
    }
    
    return null;
  }
  
  /// Extract genre from surrounding context
  static String? _extractGenreFromContext(int position, String html) {
    final context = _getContextAroundMatch(position, html, 300);
    
    // Pattern: genre="..." or data-genre="..."
    final attrMatch = RegExp(r"""genre=["']([^"']+)["']""", caseSensitive: false).firstMatch(context);
    if (attrMatch != null) {
      return attrMatch.group(1)?.trim();
    }
    
    // Pattern: <span class="genre">Genre</span>
    final spanMatch = RegExp(r"""<span[^>]*class=["'][^"']*genre[^"']*["'][^>]*>([^<]+)</span>""", caseSensitive: false).firstMatch(context);
    if (spanMatch != null) {
      final genre = spanMatch.group(1)?.trim();
      if (genre != null && _isGenreName(genre)) {
        return genre;
      }
    }
    
    // Pattern: Common genre names in text
    final genrePattern = RegExp(r'\b(Rock|Pop|Jazz|Classical|News|Talk|Sports|Hip Hop|Country|Electronic|Dance|Blues|Folk|Reggae|Latin|R&B|Metal|Alternative|Indie)\b', caseSensitive: false);
    final genreMatch = genrePattern.firstMatch(context);
    if (genreMatch != null) {
      return genreMatch.group(1);
    }
    
    return null;
  }
  
  /// Extract bitrate from surrounding context
  static int? _extractBitrateFromContext(int position, String html) {
    final context = _getContextAroundMatch(position, html, 300);
    
    // Pattern: "128kbps", "320 kbps", "64k", etc.
    final bitratePattern = RegExp(r'(\d+)\s*k?bps', caseSensitive: false);
    final bitrateMatch = bitratePattern.firstMatch(context);
    
    if (bitrateMatch != null) {
      final bitrateStr = bitrateMatch.group(1);
      if (bitrateStr != null) {
        return int.tryParse(bitrateStr);
      }
    }
    
    return null;
  }
  
  /// Extract stream URL from context
  static String? _extractStreamUrlFromContext(String context) {
    final streamPattern = RegExp(
      r"""(https?://[^\s"'<>]+\.(?:pls|m3u|mp3|aac|ogg)(?:\?[^\s"'<>]*)?|https?://[^\s"'<>]+/stream(?:/[^\s"'<>]*)?)""",
      caseSensitive: false,
    );
    
    final match = streamPattern.firstMatch(context);
    return match?.group(1);
  }
  
  /// Check if text is a navigation link (skip these)
  static bool _isNavigationLink(String text) {
    final lowerText = text.toLowerCase().trim();
    const navTerms = [
      'home', 'index', 'back', 'next', 'previous', 'menu', 'navigation',
      'top', 'bottom', 'about', 'contact', 'help', 'search', 'login',
      'register', 'browse', 'categories', 'genres', 'countries'
    ];
    
    return navTerms.any((term) => lowerText == term || lowerText.contains('$term '));
  }
  
  /// Check if text looks like a country name
  static bool _isCountryName(String text) {
    if (text.length < 2 || text.length > 50) return false;
    
    // Should start with capital letter
    if (!RegExp(r'^[A-Z]').hasMatch(text)) return false;
    
    // Common country patterns
    const commonCountries = [
      'USA', 'UK', 'United States', 'United Kingdom', 'Canada', 'France',
      'Germany', 'Spain', 'Italy', 'Australia', 'Japan', 'Brazil', 'Mexico',
      'Russia', 'China', 'India', 'Netherlands', 'Belgium', 'Switzerland',
      'Sweden', 'Norway', 'Denmark', 'Finland', 'Poland', 'Austria',
      'Portugal', 'Greece', 'Ireland', 'New Zealand', 'Argentina', 'Chile'
    ];
    
    return commonCountries.any((country) => 
      text.toLowerCase() == country.toLowerCase()
    );
  }
  
  /// Check if text looks like a genre name
  static bool _isGenreName(String text) {
    if (text.length < 3 || text.length > 30) return false;
    
    const commonGenres = [
      'Rock', 'Pop', 'Jazz', 'Classical', 'News', 'Talk', 'Sports',
      'Hip Hop', 'Country', 'Electronic', 'Dance', 'Blues', 'Folk',
      'Reggae', 'Latin', 'R&B', 'Metal', 'Alternative', 'Indie',
      'Techno', 'House', 'Trance', 'Ambient', 'World', 'Gospel',
      'Christian', 'Oldies', 'Top 40', 'Adult Contemporary', 'Easy Listening'
    ];
    
    return commonGenres.any((genre) => 
      text.toLowerCase() == genre.toLowerCase() ||
      text.toLowerCase().contains(genre.toLowerCase())
    );
  }
  
  /// Validate if URL looks like a valid stream URL
  static bool _isValidStreamUrl(String url) {
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      return false;
    }
    
    // Should contain streaming-related keywords
    final lowerUrl = url.toLowerCase();
    return lowerUrl.contains('stream') ||
           lowerUrl.contains('radio') ||
           lowerUrl.endsWith('.pls') ||
           lowerUrl.endsWith('.m3u') ||
           lowerUrl.endsWith('.mp3') ||
           lowerUrl.endsWith('.aac') ||
           lowerUrl.endsWith('.ogg') ||
           lowerUrl.contains(':8000') || // Common streaming port
           lowerUrl.contains(':8080') ||
           lowerUrl.contains(':9000');
  }
  
  /// Clean station name (remove HTML entities, extra whitespace, etc.)
  static String _cleanStationName(String name) {
    return name
        .replaceAll(RegExp(r'&nbsp;'), ' ')
        .replaceAll(RegExp(r'&amp;'), '&')
        .replaceAll(RegExp(r'&lt;'), '<')
        .replaceAll(RegExp(r'&gt;'), '>')
        .replaceAll(RegExp(r'&quot;'), '"')
        .replaceAll(RegExp(r'&#\d+;'), '')
        .replaceAll(RegExp(r'\s+'), ' ')
        .trim();
  }
  
  /// Capitalize words in a string
  static String _capitalizeWords(String text) {
    return text.split(' ').map((word) {
      if (word.isEmpty) return word;
      return word[0].toUpperCase() + word.substring(1).toLowerCase();
    }).join(' ');
  }
  
  /// Create FMStream-specific error
  static AppError _fmstreamError(String type, String details) {
    String code;
    String userMessage;
    String recoverySuggestion;
    
    switch (type) {
      case 'empty':
        code = 'ERR_FMSTREAM_001';
        userMessage = 'FMStream directory is empty';
        recoverySuggestion = 'The FMStream.org directory returned no content:\n'
            '• Check your internet connection\n'
            '• Verify FMStream.org is accessible\n'
            '• Try again later';
        break;
        
      case 'no_stations':
        code = 'ERR_FMSTREAM_002';
        userMessage = 'No radio stations found';
        recoverySuggestion = 'Could not find any radio stations in FMStream directory:\n'
            '• The directory format may have changed\n'
            '• Try refreshing the channel list\n'
            '• Contact support if issue persists';
        break;
        
      case 'parse':
        code = 'ERR_FMSTREAM_003';
        userMessage = 'Failed to parse FMStream directory';
        recoverySuggestion = 'Unable to parse the FMStream.org directory:\n'
            '• The site format may have changed\n'
            '• Check for app updates\n'
            '• Try again later';
        break;
        
      default:
        code = 'ERR_FMSTREAM_999';
        userMessage = 'Unknown FMStream error';
        recoverySuggestion = 'An unknown error occurred with FMStream:\n'
            '• Try again later\n'
            '• Contact support if issue persists';
    }
    
    return AppError(
      code: code,
      userMessage: userMessage,
      technicalDetails: details,
      recoverySuggestion: recoverySuggestion,
    );
  }
  
  /// Check if a stream URL is accessible
  static Future<bool> checkStream(String url) async {
    try {
      logger.debug('Checking FMStream radio accessibility: $url');
      
      final response = await http.head(
        Uri.parse(url),
        headers: {'User-Agent': 'TV Viewer/2.0.0'},
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

/// Channel model for IPTV streams (BL-031: Immutable)
/// v2.1.0: Multi-URL support for channel health / failover
import 'dart:convert';

class Channel {
  final String name;
  /// List of alternate stream URLs for failover (v2.1.0)
  final List<String> urls;
  /// Index into [urls] for the currently working URL (v2.1.0)
  final int workingUrlIndex;
  final String? category;
  final String? logo;
  final String? country;
  final String? language;
  final String mediaType; // 'TV' or 'Radio'
  final String status;
  final int reportCount;
  final int workingReports;
  final int brokenReports;
  final int failedReports;
  final bool isWorking;
  final DateTime? lastChecked;
  
  // Stream metadata
  final String? resolution;
  final int? bitrate;

  /// Backward-compatible getter: returns the currently active URL.
  String get url => urls.isNotEmpty
      ? urls[workingUrlIndex.clamp(0, urls.length - 1)]
      : '';

  /// Constructor accepts either [url] (single, backward compat) or [urls] (list).
  /// If both are provided, [urls] takes precedence.
  /// If neither is provided, defaults to an empty single-element list.
  Channel({
    required this.name,
    String? url,
    List<String>? urls,
    this.workingUrlIndex = 0,
    this.category,
    this.logo,
    this.country,
    this.language,
    this.mediaType = 'TV',
    this.status = 'unchecked',
    this.reportCount = 0,
    this.workingReports = 0,
    this.brokenReports = 0,
    this.failedReports = 0,
    this.isWorking = true,
    this.lastChecked,
    this.resolution,
    this.bitrate,
  }) : urls = urls ?? (url != null ? [url] : ['']);
  
  /// Normalize category by splitting on semicolons and taking first meaningful part
  /// Canonical categories — must match utils/normalize.py CANONICAL_CATEGORIES
  static const canonicalCategories = [
    'Documentary', 'Education', 'Entertainment', 'General', 'Kids',
    'Lifestyle', 'Movies', 'Music', 'Nature', 'News', 'Radio',
    'Religious', 'Shopping', 'Sports', 'Weather',
  ];

  /// Full category normalization map — ported from utils/normalize.py
  static const _categoryMap = <String, String>{
    // Xumous-prefixed
    'xumous: action & drama': 'Movies',
    'xumous: animals & nature': 'Nature',
    'xumous: automotive': 'Lifestyle',
    'xumous: black voices. black stories.': 'Entertainment',
    'xumous: classic tv': 'Entertainment',
    'xumous: combat sports': 'Sports',
    'xumous: comedy': 'Entertainment',
    'xumous: crime tv': 'Movies',
    'xumous: daytime tv': 'Entertainment',
    'xumous: faith & family': 'Religious',
    'xumous: food': 'Lifestyle',
    'xumous: game shows': 'Entertainment',
    'xumous: game show': 'Entertainment',
    'xumous: history & learning': 'Documentary',
    'xumous: home & design': 'Lifestyle',
    'xumous: horror & sci-fi': 'Movies',
    'xumous: kids': 'Kids',
    'xumous: latino': 'Entertainment',
    'xumous: local news': 'News',
    'xumous: movies': 'Movies',
    'xumous: music & radio': 'Music',
    'xumous: music': 'Music',
    'xumous: news': 'News',
    'xumous: pop culture': 'Entertainment',
    'xumous: reality tv': 'Entertainment',
    'xumous: reality': 'Entertainment',
    'xumous: sports': 'Sports',
    'xumous: travel & lifestyle': 'Lifestyle',
    'xumous: travel': 'Lifestyle',
    'xumous: food & travel': 'Lifestyle',
    'xumous: food+travel': 'Lifestyle',
    'xumous: lifestyle': 'Lifestyle',
    'xumous: documentary': 'Documentary',
    'xumous: education': 'Education',
    'xumous: shopping': 'Shopping',
    'xumous: religious': 'Religious',
    // Semicolon compounds
    'animation;entertainment': 'Kids',
    'animation;kids': 'Kids',
    'animation;kids;religious': 'Kids',
    'culture;entertainment': 'Entertainment',
    'news;entertainment': 'News',
    'sports;entertainment': 'Sports',
    'music;entertainment': 'Music',
    'music;lifestyle': 'Music',
    'documentary;education': 'Documentary',
    'kids;education': 'Kids',
    'movies;entertainment': 'Movies',
    'movies;drama': 'Movies',
    'lifestyle;entertainment': 'Lifestyle',
    'food;lifestyle': 'Lifestyle',
    'food;travel': 'Lifestyle',
    'travel;lifestyle': 'Lifestyle',
    // Messy values
    'undefined': 'General', 'other': 'General', 'uncategorized': 'General',
    'general': 'General', 'none': 'General', 'n/a': 'General', 'tv': 'General',
    // Merged categories
    'action': 'Movies', 'action & drama': 'Movies', 'adventure': 'Movies',
    'animation': 'Kids', 'animated': 'Kids', 'anime': 'Kids',
    'classic': 'Entertainment', 'classic tv': 'Entertainment',
    'classics': 'Entertainment', 'westerns + classics': 'Entertainment',
    'western': 'Entertainment', 'comedy': 'Entertainment',
    'comedy drama': 'Entertainment', 'crime': 'Movies', 'crime drama': 'Movies',
    'crime tv': 'Movies', 'drama': 'Movies', 'fiction': 'Movies',
    'horror': 'Movies', 'sci-fi': 'Movies', 'horror & sci-fi': 'Movies',
    'series': 'Entertainment', 'reality': 'Entertainment',
    'reality tv': 'Entertainment', 'talk': 'Entertainment',
    'game shows': 'Entertainment', 'game show': 'Entertainment',
    'daytime tv': 'Entertainment', 'pop culture': 'Entertainment',
    // Lifestyle merges
    'cooking': 'Lifestyle', 'food': 'Lifestyle', 'food & travel': 'Lifestyle',
    'food+travel': 'Lifestyle', 'travel': 'Lifestyle',
    'travel & lifestyle': 'Lifestyle', 'auto': 'Lifestyle',
    'automotive': 'Lifestyle', 'culture': 'Lifestyle',
    'culture + lifestyle': 'Lifestyle', 'home & design': 'Lifestyle',
    'health': 'Lifestyle', 'relax': 'Lifestyle', 'outdoor': 'Lifestyle',
    // Education merges
    'business': 'Education', 'bus./financial': 'Education',
    'technology': 'Education', 'computers': 'Education', 'tech': 'Education',
    'science': 'Education', 'gaming': 'Education',
    // Weather (its own category)
    'weather': 'Weather', 'weather & traffic': 'Weather',
    'meteo': 'Weather', 'forecast': 'Weather',
    // Direct mappings
    'movies': 'Movies', 'cinema': 'Movies', 'film': 'Movies',
    'kids': 'Kids', 'family': 'Kids', 'children': 'Kids',
    'children-music': 'Kids',
    'sports': 'Sports', 'sport': 'Sports', 'baseball': 'Sports',
    'basketball': 'Sports', 'boxing': 'Sports', 'football': 'Sports',
    'soccer': 'Sports', 'tennis': 'Sports', 'cricket': 'Sports',
    'golf': 'Sports', 'motorsport': 'Sports', 'wrestling': 'Sports',
    'combat sports': 'Sports', 'action sports': 'Sports',
    'shop': 'Shopping', 'shopping': 'Shopping', 'auction': 'Shopping',
    'teleshopping': 'Shopping',
    'documentary': 'Documentary', 'documentaries': 'Documentary',
    'history': 'Documentary', 'history & learning': 'Documentary',
    'news': 'News', 'local news': 'News', 'legislative': 'News',
    'religious': 'Religious', 'faith & family': 'Religious',
    'education': 'Education',
    'music': 'Music', 'music & radio': 'Music',
    'radio': 'Radio',
    'nature': 'Nature', 'animals': 'Nature', 'animals & nature': 'Nature',
    'wildlife': 'Nature',
    'entertainment': 'Entertainment', 'lifestyle': 'Lifestyle',
    'adult': 'General', 'xxx': 'General',
  };

  /// Name-based category patterns for channels with no/General category
  static final _namePatterns = <String, RegExp>{
    'Radio': RegExp(r'(?:\b\d{2,3}\.\d\s)|(?:\b(?:fm|radio)\b)', caseSensitive: false),
    'Music': RegExp(r'\b(?:hits|jazz|rock|oldies|hitz|reggae|hip.?hop|r&b|soul|blues|techno|edm|salsa|symphony|orchestra|mizrahi|mizrahit|playlist|classic rock|smooth jazz|country music|pop music)\b', caseSensitive: false),
    'News': RegExp(r'\b(?:news|noticias|cnn|bbc news|fox news|msnbc|cnbc|al.?jazeera|headline|infowars)\b', caseSensitive: false),
    'Sports': RegExp(r'\b(?:sport|soccer|football|basketball|tennis|cricket|golf|racing|boxing|ufc|mma|nba|nfl|mlb|nhl|espn|bein|dazn)\b', caseSensitive: false),
    'Religious': RegExp(r'\b(?:church|gospel|prayer|faith|islam|quran|torah|kabbalah|breslov|christian|bible|kol chai)\b', caseSensitive: false),
    'Kids': RegExp(r'\b(?:kids|cartoon|nick|disney|toon|boomerang|pbs kids|sesame)\b', caseSensitive: false),
    'Shopping': RegExp(r'\b(?:qvc|hsn|teleshopping|shop\s*tv|my\s*shop)\b', caseSensitive: false),
    'Weather': RegExp(r'\b(?:weather|meteo|forecast|weatherscan|wetter|metar)\b', caseSensitive: false),
  };

  static String? normalizeCategory(String? rawCategory, {String? channelName}) {
    if (rawCategory == null || rawCategory.trim().isEmpty) {
      // Try name-based inference
      if (channelName != null && channelName.isNotEmpty) {
        for (final entry in _namePatterns.entries) {
          if (entry.value.hasMatch(channelName)) return entry.key;
        }
      }
      return null;
    }

    final key = rawCategory.trim().toLowerCase();

    // Direct lookup
    var mapped = _categoryMap[key];
    if (mapped != null) return mapped;

    // Strip vendor prefix
    if (key.contains(':')) {
      final afterColon = rawCategory.split(':').last.trim().toLowerCase();
      mapped = _categoryMap[afterColon];
      if (mapped != null) return mapped;
    }

    // Semicolon split
    if (key.contains(';')) {
      final first = rawCategory.split(';').first.trim().toLowerCase();
      mapped = _categoryMap[first];
      if (mapped != null) return mapped;
    }

    // " + " split
    if (key.contains(' + ')) {
      final first = rawCategory.split(' + ').first.trim().toLowerCase();
      mapped = _categoryMap[first];
      if (mapped != null) return mapped;
    }

    // Check canonical match
    final title = rawCategory.trim();
    final titleCased = title[0].toUpperCase() + title.substring(1).toLowerCase();
    if (canonicalCategories.contains(titleCased)) return titleCased;

    // Name-based fallback
    if (channelName != null && channelName.isNotEmpty) {
      for (final entry in _namePatterns.entries) {
        if (entry.value.hasMatch(channelName)) return entry.key;
      }
    }

    return 'General';
  }
  
  /// Extract resolution from channel name (e.g., "720p", "1080p")
  static String? extractResolution(String name) {
    final match = RegExp(r'\((\d{3,4}p)\)').firstMatch(name);
    return match?.group(1);
  }
  
  /// Infer country from language if country is missing (Issue #28)
  static String? inferCountryFromLanguage(String? language) {
    if (language == null || language.isEmpty) return null;
    
    final lang = language.toLowerCase();
    
    // Comprehensive language to country mapping (ported from Python helpers.py)
    const languageCountryMap = {
      'hebrew': 'Israel', 'he': 'Israel', 'heb': 'Israel',
      'arabic': 'Middle East', 'ar': 'Middle East', 'ara': 'Middle East',
      'spanish': 'Spain', 'es': 'Spain', 'spa': 'Spain',
      'french': 'France', 'fr': 'France', 'fra': 'France',
      'german': 'Germany', 'de': 'Germany', 'deu': 'Germany',
      'italian': 'Italy', 'it': 'Italy', 'ita': 'Italy',
      'portuguese': 'Brazil', 'pt': 'Brazil', 'por': 'Brazil',
      'russian': 'Russia', 'ru': 'Russia', 'rus': 'Russia',
      'turkish': 'Turkey', 'tr': 'Turkey', 'tur': 'Turkey',
      'polish': 'Poland', 'pl': 'Poland', 'pol': 'Poland',
      'chinese': 'China', 'zh': 'China', 'zho': 'China',
      'japanese': 'Japan', 'ja': 'Japan', 'jpn': 'Japan',
      'korean': 'South Korea', 'ko': 'South Korea', 'kor': 'South Korea',
      'hindi': 'India',
      'dutch': 'Netherlands', 'nl': 'Netherlands', 'nld': 'Netherlands',
      'greek': 'Greece', 'el': 'Greece', 'ell': 'Greece',
      'thai': 'Thailand', 'th': 'Thailand', 'tha': 'Thailand',
      'vietnamese': 'Vietnam', 'vi': 'Vietnam', 'vie': 'Vietnam',
      'indonesian': 'Indonesia', 'id': 'Indonesia', 'ind': 'Indonesia',
      'malay': 'Malaysia', 'ms': 'Malaysia', 'msa': 'Malaysia',
      'filipino': 'Philippines', 'tl': 'Philippines', 'fil': 'Philippines',
      'persian': 'Iran', 'fa': 'Iran', 'fas': 'Iran', 'farsi': 'Iran',
      'tamil': 'India', 'telugu': 'India', 'bangla': 'India',
      'punjabi': 'India', 'gujarati': 'India', 'marathi': 'India',
      'kannada': 'India', 'malayalam': 'India',
      'urdu': 'Pakistan',
      'pashto': 'Afghanistan',
      'english': 'International',
    };
    
    // Try exact match first, then substring
    if (languageCountryMap.containsKey(lang)) {
      return languageCountryMap[lang];
    }
    for (final entry in languageCountryMap.entries) {
      if (lang.contains(entry.key)) {
        return entry.value;
      }
    }
    
    return null;
  }
  
  /// Detect Israeli channels from name patterns (Issue #28)
  static bool isIsraeliChannel(String name) {
    final lowerName = name.toLowerCase();
    
    // Known Israeli channel patterns
    final israeliPatterns = [
      'kan 11', 'kan11',
      'now 14', 'now14',
      'channel 12', 'channel12',
      'channel 13', 'channel13',
      'reshet 13', 'reshet13',
      'keshet 12', 'keshet12',
      'sport 5', 'sport5',
      'walla news', 'walla',
      'i24news he',
      'knesset channel',
      'makan 33',
    ];
    
    return israeliPatterns.any((pattern) => lowerName.contains(pattern));
  }
  
  /// Normalize country name (clean up, standardize)
  /// Enhanced for Issue #27: comprehensive country inference from URL + name patterns
  static String? normalizeCountry(String? country, String? language, String name, {String? url}) {
    if (country != null && country.isNotEmpty && country != 'Unknown') {
      // Clean up country name
      String normalized = country.trim();
      
      // Standardize common variations
      final lower = normalized.toLowerCase();
      if (lower == 'il' || lower == 'isr') return 'Israel';
      if (lower == 'us' || lower == 'usa') return 'United States';
      if (lower == 'uk' || lower == 'gb') return 'United Kingdom';
      if (lower == 'de' || lower == 'deu') return 'Germany';
      if (lower == 'fr' || lower == 'fra') return 'France';
      if (lower == 'es' || lower == 'esp') return 'Spain';
      if (lower == 'it' || lower == 'ita') return 'Italy';
      if (lower == 'ru' || lower == 'rus') return 'Russia';
      if (lower == 'br' || lower == 'bra') return 'Brazil';
      if (lower == 'jp' || lower == 'jpn') return 'Japan';
      if (lower == 'kr' || lower == 'kor') return 'South Korea';
      if (lower == 'cn' || lower == 'chn') return 'China';
      if (lower == 'in' || lower == 'ind') return 'India';
      if (lower == 'au' || lower == 'aus') return 'Australia';
      if (lower == 'ca' || lower == 'can') return 'Canada';
      if (lower == 'tr' || lower == 'tur') return 'Turkey';
      
      return normalized;
    }
    
    // If no country, try to infer from language
    final inferred = inferCountryFromLanguage(language);
    if (inferred != null && inferred != 'International') return inferred;
    
    // Check if channel name matches known Israeli patterns
    if (isIsraeliChannel(name)) return 'Israel';
    
    // High-confidence broadcaster name patterns (Issue #27)
    final nameLower = name.toLowerCase();
    final urlLower = (url ?? '').toLowerCase();
    final combined = '$nameLower $urlLower';
    
    final broadcasterPatterns = <String, List<RegExp>>{
      'United States': [
        RegExp(r'\b(cnn|msnbc|fox news|abc news|nbc news|cbs news)\b', caseSensitive: false),
        RegExp(r'\b(espn|nfl network|mlb network|nba tv)\b', caseSensitive: false),
        RegExp(r'\b(hbo|showtime|starz|cinemax|amc|tnt|tbs)\b', caseSensitive: false),
        RegExp(r'\b(cartoon network|nickelodeon|disney channel)\b', caseSensitive: false),
        RegExp(r'\b(discovery|history channel|nat geo|animal planet)\b', caseSensitive: false),
        RegExp(r'\b(pluto tv|filmrise|3abn|daystar|tbn)\b', caseSensitive: false),
      ],
      'United Kingdom': [
        RegExp(r'\b(bbc one|bbc two|bbc three|bbc four|bbc news)\b', caseSensitive: false),
        RegExp(r'\b(itv[1-4]?|channel 4|channel 5|sky)\b', caseSensitive: false),
      ],
      'Germany': [
        RegExp(r'\b(ard|zdf|rtl|sat\.?1|pro ?7|3sat)\b', caseSensitive: false),
      ],
      'France': [
        RegExp(r'\b(tf1|france ?[2-5]|canal\+?|bfm)\b', caseSensitive: false),
      ],
      'Spain': [
        RegExp(r'\b(tve|la ?[12]|antena ?3|telecinco|3cat)\b', caseSensitive: false),
      ],
      'Italy': [
        RegExp(r'\b(rai ?[1-5]|canale ?5|italia ?1|la ?7)\b', caseSensitive: false),
      ],
      'Russia': [
        RegExp(r'\b(russia ?[124])\b', caseSensitive: false),
      ],
      'Japan': [
        RegExp(r'\b(nhk|fuji|tv ?asahi|tbs japan)\b', caseSensitive: false),
      ],
      'South Korea': [
        RegExp(r'\b(kbs|mbc|sbs|tvn|jtbc)\b', caseSensitive: false),
      ],
      'China': [
        RegExp(r'\b(cctv|cgtn)\b', caseSensitive: false),
      ],
      'India': [
        RegExp(r'\b(zee|star ?plus|colors ?tv|sony ?tv|ndtv|dd ?national)\b', caseSensitive: false),
      ],
      'Australia': [
        RegExp(r'\b(abc ?australia|9gem|9go|9life)\b', caseSensitive: false),
      ],
      'Greece': [
        RegExp(r'\b(cosmote|ert ?[123]?|ant1|alpha|skai)\b', caseSensitive: false),
      ],
    };
    
    for (final entry in broadcasterPatterns.entries) {
      for (final pattern in entry.value) {
        if (pattern.hasMatch(combined)) {
          return entry.key;
        }
      }
    }
    
    // TLD-based detection from URL (Issue #27)
    if (url != null && url.isNotEmpty) {
      final tldMatch = RegExp(r'https?://[^/]*\.([a-z]{2})[:/]').firstMatch(urlLower);
      if (tldMatch != null) {
        final tld = tldMatch.group(1);
        const tldCountries = {
          'us': 'United States', 'uk': 'United Kingdom', 'de': 'Germany',
          'fr': 'France', 'es': 'Spain', 'it': 'Italy', 'ru': 'Russia',
          'jp': 'Japan', 'kr': 'South Korea', 'cn': 'China', 'in': 'India',
          'br': 'Brazil', 'mx': 'Mexico', 'ca': 'Canada', 'au': 'Australia',
          'tr': 'Turkey', 'nl': 'Netherlands', 'pl': 'Poland', 'il': 'Israel',
          'ae': 'UAE', 'sa': 'Saudi Arabia', 'eg': 'Egypt', 'ar': 'Argentina',
          'cl': 'Chile', 'gr': 'Greece', 'ua': 'Ukraine', 'ro': 'Romania',
          'hu': 'Hungary', 'cz': 'Czech Republic', 'th': 'Thailand',
          'vn': 'Vietnam',
        };
        if (tldCountries.containsKey(tld)) {
          return tldCountries[tld];
        }
      }
    }
    
    // Lower confidence name patterns
    const nameCountryPatterns = {
      'United States': ['usa', 'america', 'american'],
      'United Kingdom': ['british', 'britain'],
      'Germany': ['german', 'deutsch'],
      'France': ['french'],
      'Spain': ['spanish', 'spain'],
      'Italy': ['italian', 'italia'],
      'Russia': ['russian'],
      'Japan': ['japan', 'japanese'],
      'South Korea': ['korea', 'korean'],
      'China': ['china', 'chinese'],
      'India': ['india', 'indian', 'hindi', 'tamil', 'telugu'],
      'Brazil': ['brazil', 'brasil'],
      'Mexico': ['mexico', 'mexican'],
      'Turkey': ['turkey', 'turkish'],
      'UAE': ['dubai', 'abu dhabi', 'uae', 'emirates'],
      'Saudi Arabia': ['saudi'],
      'Qatar': ['qatar', 'al jazeera'],
      'Australia': ['australia', 'australian'],
      'Canada': ['canada', 'canadian'],
    };
    
    for (final entry in nameCountryPatterns.entries) {
      for (final pattern in entry.value) {
        if (nameLower.contains(pattern)) {
          return entry.key;
        }
      }
    }
    
    return inferred; // May return 'International' or null
  }

  /// Repair double-encoded UTF-8 strings (Latin-1 interpretation of UTF-8 bytes).
  /// Detects the characteristic pattern where Hebrew/Arabic/Cyrillic appear as
  /// sequences like ×§×¨×™×ª (multiplication sign + high bytes).
  static String _repairEncoding(String text) {
    // Quick check: if text has the telltale sign of Latin-1 decoded UTF-8
    // Hebrew UTF-8 bytes start with 0xD7 (×) or 0xD6, Arabic with 0xD8-0xDB
    if (!text.contains('×') && !text.contains('Ã') && !text.contains('Ø')) {
      return text; // No garbling detected
    }
    
    // Check if most characters are in the Latin-1 high range (0x80-0xFF)
    // which indicates double-encoding
    final codeUnits = text.codeUnits;
    int highByteCount = 0;
    for (final cu in codeUnits) {
      if (cu >= 0x80 && cu <= 0xFF) highByteCount++;
    }
    
    // If more than 30% of chars are high-byte Latin-1, likely double-encoded
    if (highByteCount < text.length * 0.3) return text;
    
    try {
      // Re-encode as Latin-1 bytes, then decode as UTF-8
      final bytes = codeUnits.map((c) => c & 0xFF).toList();
      final repaired = utf8.decode(bytes, allowMalformed: false);
      // Verify the result has actual Unicode text (not replacement chars)
      if (repaired.contains('\uFFFD')) return text;
      return repaired;
    } catch (_) {
      return text; // If re-decode fails, keep original
    }
  }

  factory Channel.fromM3ULine(String info, String url) {
    String name = 'Unknown';
    String? category;
    String? logo;
    String? country;
    String? language;
    String mediaType = 'TV';

    // Parse EXTINF line
    if (info.contains(',')) {
      name = info.split(',').last.trim();
    }

    // Repair double-encoded UTF-8 (Hebrew/Arabic names showing as ×§×¨×™×ª)
    name = _repairEncoding(name);

    // Parse attributes
    final groupMatch = RegExp(r'group-title="([^"]*)"').firstMatch(info);
    if (groupMatch != null) {
      category = normalizeCategory(groupMatch.group(1), channelName: name);
    }

    final logoMatch = RegExp(r'tvg-logo="([^"]*)"').firstMatch(info);
    if (logoMatch != null) {
      logo = logoMatch.group(1);
    }

    final countryMatch = RegExp(r'tvg-country="([^"]*)"').firstMatch(info);
    String? rawCountry;
    if (countryMatch != null) {
      rawCountry = countryMatch.group(1);
    }

    final langMatch = RegExp(r'tvg-language="([^"]*)"').firstMatch(info);
    if (langMatch != null) {
      language = langMatch.group(1);
    }
    
    // Detect media type from category or URL
    final lowerCategory = (category ?? '').toLowerCase();
    final lowerUrl = url.toLowerCase();
    final lowerName = name.toLowerCase();
    if (lowerCategory == 'radio' || 
        lowerUrl.contains('/radio/') ||
        lowerName.contains('radio') ||
        lowerUrl.endsWith('.mp3') ||
        lowerUrl.contains('icecast.audio')) {
      mediaType = 'Radio';
    }
    
    // Extract resolution from name
    final resolution = extractResolution(name);
    
    // Normalize/infer country (Issue #27, #28)
    country = normalizeCountry(rawCountry, language, name, url: url);

    return Channel(
      name: name,
      urls: [url],
      category: category,
      logo: logo,
      country: country,
      language: language,
      mediaType: mediaType,
      resolution: resolution,
    );
  }

  Map<String, dynamic> toJson() => {
        'name': name,
        'url': url, // backward compat: primary URL
        'urls': urls, // v2.1.0: full URL list
        'workingUrlIndex': workingUrlIndex,
        'category': category,
        'logo': logo,
        'country': country,
        'language': language,
        'mediaType': mediaType,
        'status': status,
        'reportCount': reportCount,
        'workingReports': workingReports,
        'brokenReports': brokenReports,
        'failedReports': failedReports,
        'isWorking': isWorking,
        'lastChecked': lastChecked?.toIso8601String(),
        'resolution': resolution,
        'bitrate': bitrate,
      };

  factory Channel.fromJson(Map<String, dynamic> json) {
        final rawName = json['name'] ?? 'Unknown';
        final name = _repairEncoding(rawName is String ? rawName : rawName.toString());
        final language = json['language'] as String?;
        final healthMetadata = switch (json['health_metadata'] ?? json['health_stats'] ?? json['health']) {
          Map<String, dynamic> value => value,
          Map value => Map<String, dynamic>.from(value),
          _ => const <String, dynamic>{},
        };

        int readHealthCount(List<String> keys) {
          for (final key in keys) {
            final nestedValue = healthMetadata[key];
            if (nestedValue is num) return nestedValue.toInt();
            final topLevelValue = json[key];
            if (topLevelValue is num) return topLevelValue.toInt();
          }
          return 0;
        }

        // v2.1.0: Parse both old "url" (string) and new "urls" (list) formats
        List<String> urls;
        if (json['urls'] != null && json['urls'] is List && (json['urls'] as List).isNotEmpty) {
          urls = (json['urls'] as List).map((e) => e.toString()).toList();
        } else {
          final singleUrl = json['url'] ?? '';
          urls = [singleUrl is String ? singleUrl : singleUrl.toString()];
        }
        final workingUrlIndex = json['workingUrlIndex'] ?? json['working_url_index'] ?? 0;
        final status = (json['status'] as String? ?? '').trim().toLowerCase();
        final reportCount = (json['reportCount'] as num? ?? json['report_count'] as num?)?.toInt() ?? 0;
        final workingReports = readHealthCount(['working_reports', 'workingReports']);
        final brokenReports = readHealthCount(['broken_reports', 'brokenReports']);
        final failedReports = readHealthCount(['failed_reports', 'failedReports']);
        final lastCheckedRaw = json['lastChecked'] ?? json['last_checked'];
        final lastChecked = lastCheckedRaw != null
            ? DateTime.parse(lastCheckedRaw.toString())
            : null;
        final isWorking = status.isNotEmpty
            ? status == 'working'
            : (json['is_working'] ?? json['isWorking'] ?? true) as bool;
        // Use primary URL for country normalization
        final primaryUrl = urls.isNotEmpty ? urls[0] : '';

        // Always normalize country for consistency (Issue #27)
        final rawCountry = json['country'] as String?;
        final country = normalizeCountry(rawCountry, language, name, url: primaryUrl);
        return Channel(
          name: name,
          urls: urls,
          workingUrlIndex: workingUrlIndex is int ? workingUrlIndex : 0,
          category: normalizeCategory(json['category'], channelName: name),
          logo: json['logo'],
          country: country,
          language: language,
          mediaType: json['media_type'] ?? json['mediaType'] ?? 'TV',
          status: status.isNotEmpty
              ? status
              : (isWorking ? 'working' : (lastChecked != null ? 'failed' : 'unchecked')),
          reportCount: reportCount,
          workingReports: workingReports,
          brokenReports: brokenReports,
          failedReports: failedReports,
          isWorking: isWorking,
          lastChecked: lastChecked,
          resolution: json['resolution'],
          bitrate: json['bitrate'],
        );
      }
      
  /// Get formatted bitrate string
  String? get formattedBitrate {
    if (bitrate == null) return null;
    if (bitrate! >= 1000000) {
      return '${(bitrate! / 1000000).toStringAsFixed(1)} Mbps';
    } else if (bitrate! >= 1000) {
      return '${(bitrate! / 1000).toStringAsFixed(0)} Kbps';
    }
    return '$bitrate bps';
  }

  int get totalHealthReports => workingReports + brokenReports + failedReports;

  double? get reliability =>
      totalHealthReports > 0 ? workingReports / totalHealthReports : null;

  double? get failureRate =>
      totalHealthReports > 0 ? 1 - (reliability ?? 0) : null;

  bool get hasReliabilityData => totalHealthReports > 0;

  int get healthScore {
    int score = 10;
    if (isWorking && lastChecked != null) score += 50;
    if (!isWorking && lastChecked != null) score -= 20;
    if (urls.length > 1) score += 10;
    if ((logo ?? '').isNotEmpty) score += 5;
    return score;
  }

  String get healthLabel {
    if (healthScore >= 50) return 'reliable';
    if (healthScore >= 20) return 'unstable';
    return 'offline';
  }
  
  /// BL-031: copyWith method for immutable updates
  /// v2.1.0: Added urls and workingUrlIndex params
  Channel copyWith({
    String? name,
    String? url,
    List<String>? urls,
    int? workingUrlIndex,
    String? category,
    String? logo,
    String? country,
    String? language,
    String? mediaType,
    String? status,
    int? reportCount,
    int? workingReports,
    int? brokenReports,
    int? failedReports,
    bool? isWorking,
    DateTime? lastChecked,
    String? resolution,
    int? bitrate,
  }) {
    // If a single url is provided but not urls, wrap it in a list
    List<String>? resolvedUrls = urls;
    if (resolvedUrls == null && url != null) {
      resolvedUrls = [url];
    }
    return Channel(
      name: name ?? this.name,
      urls: resolvedUrls ?? this.urls,
      workingUrlIndex: workingUrlIndex ?? this.workingUrlIndex,
      category: category ?? this.category,
      logo: logo ?? this.logo,
      country: country ?? this.country,
      language: language ?? this.language,
      mediaType: mediaType ?? this.mediaType,
      status: status ?? this.status,
      reportCount: reportCount ?? this.reportCount,
      workingReports: workingReports ?? this.workingReports,
      brokenReports: brokenReports ?? this.brokenReports,
      failedReports: failedReports ?? this.failedReports,
      isWorking: isWorking ?? this.isWorking,
      lastChecked: lastChecked ?? this.lastChecked,
      resolution: resolution ?? this.resolution,
      bitrate: bitrate ?? this.bitrate,
    );
  }
}

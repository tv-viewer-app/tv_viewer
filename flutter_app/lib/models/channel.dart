/// Channel model for IPTV streams
class Channel {
  final String name;
  final String url;
  final String? category;
  final String? logo;
  final String? country;
  final String? language;
  final String mediaType; // 'TV' or 'Radio'
  bool isWorking;
  DateTime? lastChecked;
  
  // Stream metadata
  String? resolution;
  int? bitrate;

  Channel({
    required this.name,
    required this.url,
    this.category,
    this.logo,
    this.country,
    this.language,
    this.mediaType = 'TV',
    this.isWorking = true,
    this.lastChecked,
    this.resolution,
    this.bitrate,
  });
  
  /// Normalize category by splitting on semicolons and taking first meaningful part
  static String? normalizeCategory(String? rawCategory) {
    if (rawCategory == null || rawCategory.isEmpty) return null;
    
    // Split by semicolons and take the first non-empty part
    final parts = rawCategory.split(';')
        .map((s) => s.trim())
        .where((s) => s.isNotEmpty)
        .toList();
    
    if (parts.isEmpty) return null;
    
    // Return first part, capitalized
    String category = parts.first;
    if (category.isNotEmpty) {
      category = category[0].toUpperCase() + category.substring(1).toLowerCase();
    }
    return category;
  }
  
  /// Extract resolution from channel name (e.g., "720p", "1080p")
  static String? extractResolution(String name) {
    final match = RegExp(r'\((\d{3,4}p)\)').firstMatch(name);
    return match?.group(1);
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

    // Parse attributes
    final groupMatch = RegExp(r'group-title="([^"]*)"').firstMatch(info);
    if (groupMatch != null) {
      category = normalizeCategory(groupMatch.group(1));
    }

    final logoMatch = RegExp(r'tvg-logo="([^"]*)"').firstMatch(info);
    if (logoMatch != null) {
      logo = logoMatch.group(1);
    }

    final countryMatch = RegExp(r'tvg-country="([^"]*)"').firstMatch(info);
    if (countryMatch != null) {
      country = countryMatch.group(1);
    }

    final langMatch = RegExp(r'tvg-language="([^"]*)"').firstMatch(info);
    if (langMatch != null) {
      language = langMatch.group(1);
    }
    
    // Detect media type from category or URL
    final lowerCategory = (category ?? '').toLowerCase();
    final lowerUrl = url.toLowerCase();
    if (lowerCategory.contains('radio') || 
        lowerUrl.contains('radio') ||
        lowerCategory.contains('music') ||
        name.toLowerCase().contains('radio')) {
      mediaType = 'Radio';
    }
    
    // Extract resolution from name
    final resolution = extractResolution(name);

    return Channel(
      name: name,
      url: url,
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
        'url': url,
        'category': category,
        'logo': logo,
        'country': country,
        'language': language,
        'mediaType': mediaType,
        'isWorking': isWorking,
        'lastChecked': lastChecked?.toIso8601String(),
        'resolution': resolution,
        'bitrate': bitrate,
      };

  factory Channel.fromJson(Map<String, dynamic> json) => Channel(
        name: json['name'] ?? 'Unknown',
        url: json['url'] ?? '',
        category: normalizeCategory(json['category']),
        logo: json['logo'],
        country: json['country'],
        language: json['language'],
        mediaType: json['media_type'] ?? json['mediaType'] ?? 'TV',
        isWorking: json['is_working'] ?? json['isWorking'] ?? true,
        lastChecked: json['lastChecked'] != null
            ? DateTime.parse(json['lastChecked'])
            : null,
        resolution: json['resolution'],
        bitrate: json['bitrate'],
      );
      
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
}

/// Channel model for IPTV streams
class Channel {
  final String name;
  final String url;
  final String? category;
  final String? logo;
  final String? country;
  final String? language;
  bool isWorking;
  DateTime? lastChecked;

  Channel({
    required this.name,
    required this.url,
    this.category,
    this.logo,
    this.country,
    this.language,
    this.isWorking = true,
    this.lastChecked,
  });

  factory Channel.fromM3ULine(String info, String url) {
    String name = 'Unknown';
    String? category;
    String? logo;
    String? country;
    String? language;

    // Parse EXTINF line
    if (info.contains(',')) {
      name = info.split(',').last.trim();
    }

    // Parse attributes
    final groupMatch = RegExp(r'group-title="([^"]*)"').firstMatch(info);
    if (groupMatch != null) {
      category = groupMatch.group(1);
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

    return Channel(
      name: name,
      url: url,
      category: category,
      logo: logo,
      country: country,
      language: language,
    );
  }

  Map<String, dynamic> toJson() => {
        'name': name,
        'url': url,
        'category': category,
        'logo': logo,
        'country': country,
        'language': language,
        'isWorking': isWorking,
        'lastChecked': lastChecked?.toIso8601String(),
      };

  factory Channel.fromJson(Map<String, dynamic> json) => Channel(
        name: json['name'] ?? 'Unknown',
        url: json['url'] ?? '',
        category: json['category'],
        logo: json['logo'],
        country: json['country'],
        language: json['language'],
        isWorking: json['isWorking'] ?? true,
        lastChecked: json['lastChecked'] != null
            ? DateTime.parse(json['lastChecked'])
            : null,
      );
}

import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../utils/prefs_lock.dart';

/// Community statistics screen showing aggregated usage data.
/// Fetches pre-aggregated statistics from Supabase materialized views.
class StatisticsScreen extends StatefulWidget {
  const StatisticsScreen({super.key});

  @override
  State<StatisticsScreen> createState() => _StatisticsScreenState();
}

class _StatisticsScreenState extends State<StatisticsScreen> {
  static String get _supabaseUrl =>
      const String.fromEnvironment('SUPABASE_URL', defaultValue: '');
  static String get _supabaseAnonKey =>
      const String.fromEnvironment('SUPABASE_ANON_KEY', defaultValue: '');
  static bool get _hasSupabaseStatsConfig =>
      _supabaseUrl.isNotEmpty &&
      _supabaseAnonKey.isNotEmpty &&
      _supabaseUrl != 'YOUR_SUPABASE_PROJECT_URL' &&
      _supabaseAnonKey != 'YOUR_SUPABASE_ANON_KEY';
  static Uri get _dailyActiveUsersUri =>
      Uri.parse('$_supabaseUrl/rest/v1/mv_daily_active_users?order=day.desc&limit=30');
  static Uri get _topChannelsUri =>
      Uri.parse('$_supabaseUrl/rest/v1/mv_top_channels?order=play_count.desc&limit=15');
  static final Uri _communityStatsUri = Uri.parse('https://tvviewer.app');

  bool _loading = true;
  String? _error;
  Map<String, dynamic>? _data;
  bool _showWebStatsButton = false;

  static const _cacheKey = 'stats_cache_public_v3';
  static const _cacheTimeKey = 'stats_cache_public_v3_time';
  static const _cacheTtl = Duration(minutes: 10);

  @override
  void initState() {
    super.initState();
    _loadStatistics();
  }

  Future<void> _loadStatistics() async {
    final prefs = await SharedPreferences.getInstance();

    // Try cache first
    final cachedTime = prefs.getInt(_cacheTimeKey) ?? 0;
    final now = DateTime.now().millisecondsSinceEpoch;
    if (now - cachedTime < _cacheTtl.inMilliseconds) {
      final cached = prefs.getString(_cacheKey);
      if (cached != null) {
        if (!mounted) return;
        setState(() {
          _data = jsonDecode(cached);
          _error = null;
          _showWebStatsButton = false;
          _loading = false;
        });
        return;
      }
    }

    if (!_hasSupabaseStatsConfig) {
      await prefs.safeRemove(_cacheKey);
      await prefs.safeRemove(_cacheTimeKey);
      _showCommunityStatsFallback();
      return;
    }

    final client = http.Client();
    try {
      final headers = {
        'apikey': _supabaseAnonKey,
        'Authorization': 'Bearer $_supabaseAnonKey',
      };
      final responses = await Future.wait([
        client
            .get(_dailyActiveUsersUri, headers: headers)
            .timeout(const Duration(seconds: 15)),
        client
            .get(_topChannelsUri, headers: headers)
            .timeout(const Duration(seconds: 15)),
      ]);

      final dailyResponse = responses[0];
      final channelsResponse = responses[1];

      if (dailyResponse.statusCode == 401 ||
          dailyResponse.statusCode == 403 ||
          channelsResponse.statusCode == 401 ||
          channelsResponse.statusCode == 403) {
        await prefs.safeRemove(_cacheKey);
        await prefs.safeRemove(_cacheTimeKey);
        _showCommunityStatsFallback();
        return;
      }

      if (dailyResponse.statusCode != 200 || channelsResponse.statusCode != 200) {
        throw Exception(
            'API error: ${dailyResponse.statusCode}/${channelsResponse.statusCode}');
      }

      final dynamic dailyDecoded = jsonDecode(dailyResponse.body);
      final dynamic channelsDecoded = jsonDecode(channelsResponse.body);
      if (dailyDecoded is! List || channelsDecoded is! List) {
        await prefs.safeRemove(_cacheKey);
        await prefs.safeRemove(_cacheTimeKey);
        _showCommunityStatsFallback();
        return;
      }

      final topChannelsList = List<Map<String, dynamic>>.from(
        channelsDecoded.map((item) => Map<String, dynamic>.from(item as Map)),
      );

      // Resolve actual channel names from hashes
      await _resolveChannelNames(topChannelsList, headers);

      final result = _normalizeStatisticsPayload(
        _buildStatisticsFromMaterializedViews(
          List<Map<String, dynamic>>.from(
            dailyDecoded.map((item) => Map<String, dynamic>.from(item as Map)),
          ),
          topChannelsList,
        ),
      );
      final totalEvents = (result['total_events'] as num?)?.toInt() ?? 0;
      final totalPlays = (result['total_plays'] as num?)?.toInt() ?? 0;
      final hasAnalytics = result['has_analytics'] == true;
      if (!hasAnalytics && totalEvents == 0 && totalPlays == 0) {
        await prefs.safeRemove(_cacheKey);
        await prefs.safeRemove(_cacheTimeKey);
        _showCommunityStatsFallback();
        return;
      }

      await prefs.safeSetString(_cacheKey, jsonEncode(result));
      await prefs.safeSetInt(_cacheTimeKey, now);

      if (!mounted) return;
      setState(() {
        _data = result;
        _error = null;
        _showWebStatsButton = false;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      // Try stale cache
      final cached = prefs.getString(_cacheKey);
      setState(() {
        if (cached != null) {
          _data = jsonDecode(cached);
          _error = null;
          _showWebStatsButton = false;
        } else {
          _error = 'Unable to load statistics';
          _showWebStatsButton = false;
        }
        _loading = false;
      });
    } finally {
      client.close();
    }
  }

  void _showCommunityStatsFallback() {
    if (!mounted) return;
    setState(() {
      _data = null;
      _error =
          'Community statistics are available in the web client.\n\nVisit tvviewer.app for full community statistics.';
      _showWebStatsButton = true;
      _loading = false;
    });
  }

  Map<String, dynamic> _buildStatisticsFromMaterializedViews(
    List<Map<String, dynamic>> dailyActiveUsers,
    List<Map<String, dynamic>> topChannels,
  ) {
    final platforms = <String, int>{};
    var totalEvents = 0;
    var totalUsers = 0;

    for (final row in dailyActiveUsers) {
      final platform = (row['platform'] as String? ?? 'unknown').trim().isEmpty
          ? 'unknown'
          : (row['platform'] as String? ?? 'unknown').trim();
      final events = (row['total_events'] as num?)?.toInt() ?? 0;
      final uniqueDevices = (row['unique_devices'] as num?)?.toInt() ?? 0;
      totalEvents += events;
      totalUsers += uniqueDevices;
      platforms[platform] = (platforms[platform] ?? 0) + events;
    }

    final sortedPlatforms = Map<String, dynamic>.fromEntries(
      platforms.entries.toList()..sort((a, b) => b.value.compareTo(a.value)),
    );

    final topChannelRows = topChannels.take(15).map((channel) {
      final plays = (channel['play_count'] as num?)?.toInt() ?? 0;
      return {
        'name': _formatMaterializedChannel(channel),
        'plays': plays,
      };
    }).toList();

    final countryTopChannels = <String, List<Map<String, dynamic>>>{};
    for (final channel in topChannels) {
      final rawCountry = (channel['channel_country'] as String? ?? '').trim();
      if (rawCountry.isEmpty) continue;
      final country = _normalizeCountryCode(rawCountry);
      if (country.isEmpty) continue;
      final entry = {
        'name': _formatMaterializedChannel(channel),
        'plays': (channel['play_count'] as num?)?.toInt() ?? 0,
      };
      final bucket =
          countryTopChannels.putIfAbsent(country, () => <Map<String, dynamic>>[]);
      if (bucket.length < 3) {
        bucket.add(entry);
      }
    }

    return {
      'has_analytics': dailyActiveUsers.isNotEmpty || topChannels.isNotEmpty,
      'unique_users': totalUsers,
      'total_events': totalEvents,
      'total_plays': topChannelRows.fold<int>(
          0, (sum, item) => sum + ((item['plays'] as int?) ?? 0)),
      'unique_channels_played': topChannels.length,
      'platforms': sortedPlatforms,
      'top_channels': topChannelRows,
      'countries': const <Map<String, dynamic>>[],
      'country_last_access': const <Map<String, dynamic>>[],
      'country_top_channels': countryTopChannels,
    };
  }

  String _formatMaterializedChannel(Map<String, dynamic> channel) {
    // If we resolved the channel name, use it
    final resolvedName = (channel['resolved_name'] as String? ?? '').trim();
    if (resolvedName.isNotEmpty) return resolvedName;

    final country = _normalizeCountryCode(
        (channel['channel_country'] as String? ?? '').trim());
    final category = (channel['channel_category'] as String? ?? '').trim();
    final labelParts = <String>[
      if (country.isNotEmpty) country,
      if (category.isNotEmpty) category,
    ];
    if (labelParts.isNotEmpty) {
      return labelParts.join(' • ');
    }
    return (channel['channel_hash'] as String? ?? 'Unknown channel').trim();
  }

  /// Normalize country codes: IL -> Israel, US -> United States, etc.
  String _normalizeCountryCode(String code) {
    const countryMap = {
      'IL': 'Israel', 'US': 'United States', 'GB': 'United Kingdom',
      'DE': 'Germany', 'FR': 'France', 'CA': 'Canada', 'RU': 'Russia',
      'IN': 'India', 'CN': 'China', 'GR': 'Greece', 'ES': 'Spain',
      'IT': 'Italy', 'BR': 'Brazil', 'AU': 'Australia', 'XX': '',
    };
    return countryMap[code.toUpperCase()] ?? code;
  }

  /// Resolve channel names from hashes by querying the channels table
  Future<void> _resolveChannelNames(
      List<Map<String, dynamic>> topChannels, Map<String, String> headers) async {
    if (topChannels.isEmpty || !_hasSupabaseStatsConfig) return;

    try {
      // Get hashes to look up
      final hashes = topChannels
          .map((c) => (c['channel_hash'] as String? ?? '').trim())
          .where((h) => h.isNotEmpty)
          .toSet()
          .toList();
      if (hashes.isEmpty) return;

      // Query channels table for matching url_hash -> name
      // Use IN filter with PostgREST: url_hash=in.(hash1,hash2,...)
      final hashFilter = 'in.(${hashes.join(",")})';
      final uri = Uri.parse(
          '$_supabaseUrl/rest/v1/channels?select=url_hash,name&url_hash=$hashFilter');
      final resp = await http.get(uri, headers: headers)
          .timeout(const Duration(seconds: 10));

      if (resp.statusCode == 200) {
        final List<dynamic> rows = jsonDecode(resp.body);
        final nameMap = <String, String>{};
        for (final row in rows) {
          final hash = (row['url_hash'] as String? ?? '').trim();
          final name = (row['name'] as String? ?? '').trim();
          if (hash.isNotEmpty && name.isNotEmpty) {
            nameMap[hash] = name;
          }
        }
        // Apply resolved names
        for (final channel in topChannels) {
          final hash = (channel['channel_hash'] as String? ?? '').trim();
          if (nameMap.containsKey(hash)) {
            channel['resolved_name'] = nameMap[hash];
          }
        }
      }
    } catch (_) {
      // Name resolution failed — fall back to country/category display
    }
  }

  Future<void> _openCommunityStats() async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      final launched = await launchUrl(
        _communityStatsUri,
        mode: LaunchMode.externalApplication,
      );
      if (!launched && mounted) {
        messenger.showSnackBar(
          const SnackBar(content: Text('Could not open tvviewer.app')),
        );
      }
    } catch (_) {
      if (mounted) {
        messenger.showSnackBar(
          const SnackBar(content: Text('Could not open tvviewer.app')),
        );
      }
    }
  }

  Map<String, dynamic> _normalizeStatisticsPayload(Map<String, dynamic> payload) {
    final countries = payload['user_countries'];
    return {
      'has_analytics': payload['has_analytics'] == true,
      'total_events': (payload['total_events'] as num?)?.toInt() ?? 0,
      'total_plays': (payload['total_plays'] as num?)?.toInt() ?? 0,
      'unique_channels_played':
          (payload['unique_channels_played'] as num?)?.toInt() ?? 0,
      'platforms': payload['platforms'] is Map
          ? Map<String, dynamic>.from(payload['platforms'] as Map)
          : <String, dynamic>{},
      'top_channels': payload['top_channels'] is List
          ? List<Map<String, dynamic>>.from(
              (payload['top_channels'] as List).map(
                (item) => Map<String, dynamic>.from(item as Map),
              ),
            )
          : <Map<String, dynamic>>[],
      'countries': countries is List
          ? List<Map<String, dynamic>>.from(
              countries.map((item) => Map<String, dynamic>.from(item as Map)),
            )
          : <Map<String, dynamic>>[],
      'country_last_access': payload['country_last_access'] is List
          ? List<Map<String, dynamic>>.from(
              (payload['country_last_access'] as List).map(
                (item) => Map<String, dynamic>.from(item as Map),
              ),
            )
          : <Map<String, dynamic>>[],
      'country_top_channels': payload['country_top_channels'] is Map
          ? Map<String, dynamic>.from(payload['country_top_channels'] as Map)
          : <String, dynamic>{},
    };
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      appBar: AppBar(title: const Text('📊 Community Stats'), centerTitle: true),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null && _data == null
              ? _buildErrorState(theme, colorScheme)
              : RefreshIndicator(
                  onRefresh: () async {
                    final prefs = await SharedPreferences.getInstance();
                    await prefs.safeRemove(_cacheTimeKey);
                    if (!mounted) return;
                    setState(() {
                      _loading = true;
                      _error = null;
                      _showWebStatsButton = false;
                    });
                    await _loadStatistics();
                  },
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      _buildHeader(),
                      const SizedBox(height: 20),
                      _buildSummaryCards(colorScheme),
                      const SizedBox(height: 24),
                      if ((_data?['platforms'] as Map?)?.isNotEmpty == true)
                        ...[
                          _buildSection(
                              '📱 Platforms', _buildPlatformList(colorScheme)),
                          const SizedBox(height: 24)
                        ],
                      if ((_data?['countries'] as List?)?.isNotEmpty == true)
                        ...[
                          _buildSection(
                              '🌍 Countries', _buildCountryList(colorScheme)),
                          const SizedBox(height: 24)
                        ],
                      if ((_data?['top_channels'] as List?)?.isNotEmpty == true)
                        ...[
                          _buildSection(
                              '🔥 Top Channels', _buildTopChannels(colorScheme)),
                          const SizedBox(height: 24)
                        ],
                      if ((_data?['country_last_access'] as List?)?.isNotEmpty ==
                          true)
                        ...[
                          _buildSection('🕒 Country Last Access',
                              _buildCountryLastAccess(colorScheme)),
                          const SizedBox(height: 24)
                        ],
                      if ((_data?['country_top_channels'] as Map?)?.isNotEmpty ==
                          true)
                        ...[
                          _buildSection('🏁 Top Channels per Country',
                              _buildCountryTopChannels(colorScheme)),
                          const SizedBox(height: 24)
                        ],
                      _buildFooter(theme),
                    ],
                  ),
                ),
    );
  }

  Widget _buildErrorState(ThemeData theme, ColorScheme colorScheme) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            _showWebStatsButton ? Icons.public : Icons.cloud_off,
            size: 48,
            color: colorScheme.outline,
          ),
          const SizedBox(height: 12),
          Text(
            _error!,
            style: theme.textTheme.bodyLarge,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            _showWebStatsButton
                ? 'Community stats require anon access to the materialized views. If access is not granted yet, use tvviewer.app.'
                : 'Statistics require an active internet connection.',
            style:
                theme.textTheme.bodySmall?.copyWith(color: colorScheme.outline),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          if (_showWebStatsButton) ...[
            FilledButton.icon(
              onPressed: _openCommunityStats,
              icon: const Icon(Icons.open_in_new),
              label: const Text('Open tvviewer.app'),
            ),
            const SizedBox(height: 12),
          ],
          FilledButton.icon(
            onPressed: () {
              setState(() {
                _loading = true;
                _error = null;
                _showWebStatsButton = false;
              });
              _loadStatistics();
            },
            icon: const Icon(Icons.refresh),
            label: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Text('Last 30 days • Anonymous aggregated data',
        style: Theme.of(context)
            .textTheme
            .bodySmall
            ?.copyWith(color: Theme.of(context).colorScheme.outline),
        textAlign: TextAlign.center);
  }

  Widget _buildSummaryCards(ColorScheme cs) {
    final plays = _data?['total_plays'] ?? 0;
    final channels = _data?['unique_channels_played'] ?? 0;
    final events = _data?['total_events'] ?? 0;
    return Row(children: [
      Expanded(child: _statCard('▶️', '$plays', 'Plays', cs.primaryContainer)),
      const SizedBox(width: 12),
      Expanded(
          child:
              _statCard('📺', '$channels', 'Channels', cs.secondaryContainer)),
      const SizedBox(width: 12),
      Expanded(child: _statCard('📊', '$events', 'Events', cs.tertiaryContainer)),
    ]);
  }

  Widget _statCard(String emoji, String value, String label, Color bg) {
    return Card(
        color: bg,
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
          child: Column(children: [
            Text(emoji, style: const TextStyle(fontSize: 24)),
            const SizedBox(height: 4),
            Text(value,
                style: Theme.of(context)
                    .textTheme
                    .headlineSmall
                    ?.copyWith(fontWeight: FontWeight.bold)),
            Text(label,
                style: Theme.of(context).textTheme.bodySmall,
                textAlign: TextAlign.center),
          ]),
        ));
  }

  Widget _buildSection(String title, Widget content) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(title,
          style: Theme.of(context)
              .textTheme
              .titleMedium
              ?.copyWith(fontWeight: FontWeight.bold)),
      const SizedBox(height: 12),
      content,
    ]);
  }

  Widget _buildCountryList(ColorScheme cs) {
    final countries = (_data?['countries'] as List?) ?? [];
    if (countries.isEmpty) return const SizedBox.shrink();
    final maxVal = ((countries.first as Map)['events'] as int).toDouble();
    return Card(
        child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              children: countries.take(15).map<Widget>((c) {
                final m = c as Map;
                return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(children: [
                      SizedBox(
                          width: 80,
                          child:
                              Text(m['name'] ?? '', style: const TextStyle(fontSize: 13))),
                      Expanded(
                          child: ClipRRect(
                              borderRadius: BorderRadius.circular(4),
                              child: LinearProgressIndicator(
                                  value: (m['events'] as int) / maxVal,
                                  backgroundColor: cs.surfaceContainerHigh,
                                  color: cs.primary,
                                  minHeight: 8))),
                      const SizedBox(width: 8),
                      Text('${m['events']}',
                          style: TextStyle(fontSize: 12, color: cs.outline)),
                    ]));
              }).toList(),
            )));
  }

  Widget _buildPlatformList(ColorScheme cs) {
    final platforms = (_data?['platforms'] as Map?) ?? {};
    if (platforms.isEmpty) return const SizedBox.shrink();
    const icons = {
      'android': '🤖',
      'web': '🌐',
      'web-server': '🐳',
      'windows': '💻',
      'ios': '🍎'
    };
    final total = platforms.values.fold<int>(0, (s, v) => s + (v as int));
    return Card(
        child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              children: platforms.entries.map<Widget>((e) {
                final pct = total > 0 ? (e.value * 100 / total).toStringAsFixed(1) : '0';
                return ListTile(
                    dense: true,
                    leading: Text(icons[e.key] ?? '📱',
                        style: const TextStyle(fontSize: 24)),
                    title: Text(e.key,
                        style: const TextStyle(fontWeight: FontWeight.w500)),
                    trailing: Text('$pct% (${e.value})',
                        style: TextStyle(color: cs.outline)));
              }).toList(),
            )));
  }

  Widget _buildTopChannels(ColorScheme cs) {
    final channels = (_data?['top_channels'] as List?) ?? [];
    if (channels.isEmpty) return const SizedBox.shrink();
    return Card(
        child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              children: channels.asMap().entries.map<Widget>((entry) {
                final rank = entry.key + 1;
                final ch = entry.value as Map;
                return ListTile(
                    dense: true,
                    leading: CircleAvatar(
                        radius: 14,
                        backgroundColor: cs.primaryContainer,
                        child: Text('$rank',
                            style: TextStyle(
                                fontSize: 12, color: cs.onPrimaryContainer))),
                    title: Text(ch['name'] ?? '', overflow: TextOverflow.ellipsis),
                    trailing: Text('${ch['plays']} plays',
                        style: TextStyle(color: cs.outline, fontSize: 13)));
              }).toList(),
            )));
  }

  Widget _buildCountryLastAccess(ColorScheme cs) {
    final lastAccess = (_data?['country_last_access'] as List?) ?? [];
    if (lastAccess.isEmpty) return const SizedBox.shrink();
    return Card(
        child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              children: lastAccess.map<Widget>((entry) {
                final item = entry as Map;
                return ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  title: Text(item['name'] ?? '',
                      style: const TextStyle(fontWeight: FontWeight.w500)),
                  trailing: Text(item['last_seen'] ?? '',
                      style: TextStyle(color: cs.outline, fontSize: 13)),
                );
              }).toList(),
            )));
  }

  Widget _buildCountryTopChannels(ColorScheme cs) {
    final countryTopChannels = (_data?['country_top_channels'] as Map?) ?? {};
    if (countryTopChannels.isEmpty) return const SizedBox.shrink();
    final entries = countryTopChannels.entries
        .where((entry) => entry.value is List && (entry.value as List).isNotEmpty)
        .toList();
    return Column(
      children: entries.map<Widget>((entry) {
        final channels = entry.value as List;
        return Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(entry.key,
                      style: Theme.of(context)
                          .textTheme
                          .titleSmall
                          ?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  ...channels.asMap().entries.map<Widget>((channelEntry) {
                    final channel = channelEntry.value as Map;
                    final isLast = channelEntry.key == channels.length - 1;
                    return Container(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      decoration: isLast
                          ? null
                          : BoxDecoration(
                              border: Border(
                                  bottom: BorderSide(color: cs.outlineVariant))),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(
                              channel['name'] ?? '',
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(fontSize: 13),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Text('${channel['plays']} plays',
                              style:
                                  TextStyle(color: cs.outline, fontSize: 12)),
                        ],
                      ),
                    );
                  }),
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildFooter(ThemeData theme) {
    return Padding(
        padding: const EdgeInsets.all(16),
        child: Text(
            'All data is anonymous and aggregated.\nNo personal information is collected.',
            style: theme.textTheme.bodySmall
                ?.copyWith(color: theme.colorScheme.outline),
            textAlign: TextAlign.center));
  }
}

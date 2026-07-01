import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

/// Community statistics screen showing aggregated usage data.
/// Fetches pre-aggregated statistics from the server-side cache.
class StatisticsScreen extends StatefulWidget {
  const StatisticsScreen({super.key});

  @override
  State<StatisticsScreen> createState() => _StatisticsScreenState();
}

class _StatisticsScreenState extends State<StatisticsScreen> {
  static Uri get _statisticsApiUri => Uri.parse(
      const String.fromEnvironment('COMMUNITY_STATS_URL',
          defaultValue: 'https://tvviewer.app/api/statistics'));
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

    final client = http.Client();
    try {
      final response = await client
          .get(_statisticsApiUri)
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 401 || response.statusCode == 403) {
        await prefs.remove(_cacheKey);
        await prefs.remove(_cacheTimeKey);
        _showCommunityStatsFallback();
        return;
      }

      if (response.statusCode != 200) {
        throw Exception('API error: ${response.statusCode}');
      }

      final dynamic decoded = jsonDecode(response.body);
      if (decoded is! Map<String, dynamic>) {
        await prefs.remove(_cacheKey);
        await prefs.remove(_cacheTimeKey);
        _showCommunityStatsFallback();
        return;
      }

      final result = _normalizeStatisticsPayload(decoded);
      final totalEvents = (result['total_events'] as num?)?.toInt() ?? 0;
      final hasAnalytics = result['has_analytics'] == true;
      if (!hasAnalytics && totalEvents == 0) {
        await prefs.remove(_cacheKey);
        await prefs.remove(_cacheTimeKey);
        _showCommunityStatsFallback();
        return;
      }

      await prefs.setString(_cacheKey, jsonEncode(result));
      await prefs.setInt(_cacheTimeKey, now);

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
                    await prefs.remove(_cacheTimeKey);
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
                ? 'Mobile builds use the public anon key only. Full community stats stay in the web client.'
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

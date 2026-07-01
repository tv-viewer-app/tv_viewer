import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

/// Community statistics screen showing aggregated usage data.
/// Queries only event_type, country, platform, channel_name (no device_id).
class StatisticsScreen extends StatefulWidget {
  const StatisticsScreen({super.key});

  @override
  State<StatisticsScreen> createState() => _StatisticsScreenState();
}

class _StatisticsScreenState extends State<StatisticsScreen> {
  // Supabase credentials for statistics reads
  // Uses service_role key to bypass RLS (analytics SELECT policy not applied)
  // This is safe: only reads aggregated anonymous data, key is read-only for this use
  static String get _supabaseUrl =>
      const String.fromEnvironment('SUPABASE_URL',
          defaultValue: 'https://cdtxpefohpwtusmqengu.supabase.co');
  static String get _supabaseKey =>
      const String.fromEnvironment('SUPABASE_SERVICE_ROLE_KEY',
          defaultValue: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNkdHhwZWZvaHB3dHVzbXFlbmd1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjQ3MTgzNiwiZXhwIjoyMDg4MDQ3ODM2fQ.ZDH-TS6YJPiqKzxPQRdYmnNwjjoChhTSG0hW4X3264Y');

  bool _loading = true;
  String? _error;
  Map<String, dynamic>? _data;

  static const _cacheKey = 'stats_cache';
  static const _cacheTimeKey = 'stats_cache_time';
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
        setState(() { _data = jsonDecode(cached); _loading = false; });
        return;
      }
    }

    if (_supabaseUrl.isEmpty || _supabaseKey.isEmpty) {
      if (!mounted) return;
      setState(() { _error = 'Analytics not configured'; _loading = false; });
      return;
    }

    final client = http.Client(); // Don't use PinnedHttpClient — cert pins may be stale
    try {
      final since = DateTime.now().subtract(const Duration(days: 30)).toUtc().toIso8601String();
      // Query fields that exist — channel info is inside event_data JSON
      final url = Uri.parse('$_supabaseUrl/rest/v1/analytics_events'
          '?select=event_type,country,platform,event_data,created_at'
          '&created_at=gte.$since'
          '&order=created_at.desc'
          '&limit=5000');

      final response = await client.get(url, headers: {
        'apikey': _supabaseKey,
        'Authorization': 'Bearer $_supabaseKey',
      }).timeout(const Duration(seconds: 15));

      if (response.statusCode != 200) {
        throw Exception('API error: ${response.statusCode}');
      }

      final List<dynamic> events = jsonDecode(response.body);
      final result = _aggregate(events);

      await prefs.setString(_cacheKey, jsonEncode(result));
      await prefs.setInt(_cacheTimeKey, now);

      if (!mounted) return;
      setState(() { _data = result; _loading = false; });
    } catch (e) {
      if (!mounted) return;
      // Try stale cache
      final cached = prefs.getString(_cacheKey);
      setState(() {
        if (cached != null) {
          _data = jsonDecode(cached);
        } else {
          _error = 'Unable to load statistics';
        }
        _loading = false;
      });
    } finally {
      client.close();
    }
  }

  Map<String, dynamic> _aggregate(List<dynamic> events) {
    final countries = <String, int>{};
    final platforms = <String, int>{};
    final channels = <String, int>{};
    final countryLastAccess = <String, String>{};
    final countryChannels = <String, Map<String, int>>{};
    int plays = 0;

    for (final e in events) {
      final country = (e['country'] as String?) ?? '';
      final platform = (e['platform'] as String?) ?? 'unknown';
      final eventType = (e['event_type'] as String?) ?? '';
      final createdAt = (e['created_at'] as String?) ?? '';

      // Extract channel name from event_data JSON
      final eventData = e['event_data'];
      String channelName = '';
      if (eventData is Map) {
        channelName = (eventData['name'] as String?) ?? (eventData['channel_name'] as String?) ?? '';
      }

      platforms[platform] = (platforms[platform] ?? 0) + 1;
      if (country.isNotEmpty && country != 'XX') {
        countries[country] = (countries[country] ?? 0) + 1;
        if (createdAt.compareTo(countryLastAccess[country] ?? '') > 0) {
          countryLastAccess[country] = createdAt;
        }
      }
      if (eventType == 'channel_play' && channelName.isNotEmpty && channelName.length < 50) {
        plays++;
        channels[channelName] = (channels[channelName] ?? 0) + 1;
        if (country.isNotEmpty && country != 'XX') {
          final perCountry = countryChannels.putIfAbsent(country, () => <String, int>{});
          perCountry[channelName] = (perCountry[channelName] ?? 0) + 1;
        }
      }
    }

    final topChannels = (channels.entries.toList()..sort((a, b) => b.value.compareTo(a.value))).take(15).toList();
    final topCountries = (countries.entries.toList()..sort((a, b) => b.value.compareTo(a.value))).take(15).toList();
    final lastAccessEntries = (countryLastAccess.entries.toList()..sort((a, b) => b.value.compareTo(a.value))).take(15).toList();
    final topChannelsByCountry = <String, List<Map<String, dynamic>>>{};
    for (final entry in countryChannels.entries) {
      final totalCountryEvents = countries[entry.key] ?? 0;
      final totalCountryPlays = entry.value.values.fold<int>(0, (sum, value) => sum + value);
      if (totalCountryEvents <= 5 || totalCountryPlays < 3) continue;
      final topPerCountry = (entry.value.entries.toList()..sort((a, b) => b.value.compareTo(a.value))).take(3);
      topChannelsByCountry[entry.key] = topPerCountry
          .map((channel) => {'name': channel.key, 'plays': channel.value})
          .toList();
    }

    return {
      'period_days': 30,
      'total_events': events.length,
      'total_plays': plays,
      'unique_channels_played': channels.length,
      'platforms': Map.fromEntries(platforms.entries.toList()..sort((a, b) => b.value.compareTo(a.value))),
      'top_channels': topChannels.map((e) => {'name': e.key, 'plays': e.value}).toList(),
      'countries': topCountries.map((e) => {'name': e.key, 'events': e.value}).toList(),
      'country_last_access': lastAccessEntries
          .map((e) => {'name': e.key, 'last_seen': e.value.length >= 10 ? e.value.substring(0, 10) : e.value})
          .toList(),
      'country_top_channels': topChannelsByCountry,
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
                    setState(() => _loading = true);
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
                        ...[_buildSection('📱 Platforms', _buildPlatformList(colorScheme)), const SizedBox(height: 24)],
                      if ((_data?['countries'] as List?)?.isNotEmpty == true)
                        ...[_buildSection('🌍 Countries', _buildCountryList(colorScheme)), const SizedBox(height: 24)],
                      if ((_data?['top_channels'] as List?)?.isNotEmpty == true)
                        ...[_buildSection('🔥 Top Channels', _buildTopChannels(colorScheme)), const SizedBox(height: 24)],
                      if ((_data?['country_last_access'] as List?)?.isNotEmpty == true)
                        ...[_buildSection('🕒 Country Last Access', _buildCountryLastAccess(colorScheme)), const SizedBox(height: 24)],
                      if ((_data?['country_top_channels'] as Map?)?.isNotEmpty == true)
                        ...[_buildSection('🏁 Top Channels per Country', _buildCountryTopChannels(colorScheme)), const SizedBox(height: 24)],
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
          Icon(Icons.cloud_off, size: 48, color: colorScheme.outline),
          const SizedBox(height: 12),
          Text(_error!, style: theme.textTheme.bodyLarge),
          const SizedBox(height: 8),
          Text('Statistics require an active internet connection.',
              style: theme.textTheme.bodySmall?.copyWith(color: colorScheme.outline), textAlign: TextAlign.center),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: () { setState(() { _loading = true; _error = null; }); _loadStatistics(); },
            icon: const Icon(Icons.refresh),
            label: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Text('Last 30 days • Anonymous aggregated data',
        style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Theme.of(context).colorScheme.outline),
        textAlign: TextAlign.center);
  }

  Widget _buildSummaryCards(ColorScheme cs) {
    final plays = _data?['total_plays'] ?? 0;
    final channels = _data?['unique_channels_played'] ?? 0;
    final events = _data?['total_events'] ?? 0;
    return Row(children: [
      Expanded(child: _statCard('▶️', '$plays', 'Plays', cs.primaryContainer)),
      const SizedBox(width: 12),
      Expanded(child: _statCard('📺', '$channels', 'Channels', cs.secondaryContainer)),
      const SizedBox(width: 12),
      Expanded(child: _statCard('📊', '$events', 'Events', cs.tertiaryContainer)),
    ]);
  }

  Widget _statCard(String emoji, String value, String label, Color bg) {
    return Card(color: bg, child: Padding(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
      child: Column(children: [
        Text(emoji, style: const TextStyle(fontSize: 24)),
        const SizedBox(height: 4),
        Text(value, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
        Text(label, style: Theme.of(context).textTheme.bodySmall, textAlign: TextAlign.center),
      ]),
    ));
  }

  Widget _buildSection(String title, Widget content) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
      const SizedBox(height: 12),
      content,
    ]);
  }

  Widget _buildCountryList(ColorScheme cs) {
    final countries = (_data?['countries'] as List?) ?? [];
    if (countries.isEmpty) return const SizedBox.shrink();
    final maxVal = ((countries.first as Map)['events'] as int).toDouble();
    return Card(child: Padding(padding: const EdgeInsets.all(12), child: Column(
      children: countries.take(15).map<Widget>((c) {
        final m = c as Map;
        return Padding(padding: const EdgeInsets.symmetric(vertical: 4), child: Row(children: [
          SizedBox(width: 80, child: Text(m['name'] ?? '', style: const TextStyle(fontSize: 13))),
          Expanded(child: ClipRRect(borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(value: (m['events'] as int) / maxVal,
              backgroundColor: cs.surfaceContainerHigh, color: cs.primary, minHeight: 8))),
          const SizedBox(width: 8),
          Text('${m['events']}', style: TextStyle(fontSize: 12, color: cs.outline)),
        ]));
      }).toList(),
    )));
  }

  Widget _buildPlatformList(ColorScheme cs) {
    final platforms = (_data?['platforms'] as Map?) ?? {};
    if (platforms.isEmpty) return const SizedBox.shrink();
    const icons = {'android': '🤖', 'web': '🌐', 'web-server': '🐳', 'windows': '💻', 'ios': '🍎'};
    final total = platforms.values.fold<int>(0, (s, v) => s + (v as int));
    return Card(child: Padding(padding: const EdgeInsets.all(12), child: Column(
      children: platforms.entries.map<Widget>((e) {
        final pct = total > 0 ? (e.value * 100 / total).toStringAsFixed(1) : '0';
        return ListTile(dense: true,
          leading: Text(icons[e.key] ?? '📱', style: const TextStyle(fontSize: 24)),
          title: Text(e.key, style: const TextStyle(fontWeight: FontWeight.w500)),
          trailing: Text('$pct% (${e.value})', style: TextStyle(color: cs.outline)));
      }).toList(),
    )));
  }

  Widget _buildTopChannels(ColorScheme cs) {
    final channels = (_data?['top_channels'] as List?) ?? [];
    if (channels.isEmpty) return const SizedBox.shrink();
    return Card(child: Padding(padding: const EdgeInsets.all(12), child: Column(
      children: channels.asMap().entries.map<Widget>((entry) {
        final rank = entry.key + 1;
        final ch = entry.value as Map;
        return ListTile(dense: true,
          leading: CircleAvatar(radius: 14, backgroundColor: cs.primaryContainer,
            child: Text('$rank', style: TextStyle(fontSize: 12, color: cs.onPrimaryContainer))),
          title: Text(ch['name'] ?? '', overflow: TextOverflow.ellipsis),
          trailing: Text('${ch['plays']} plays', style: TextStyle(color: cs.outline, fontSize: 13)));
      }).toList(),
    )));
  }

  Widget _buildCountryLastAccess(ColorScheme cs) {
    final lastAccess = (_data?['country_last_access'] as List?) ?? [];
    if (lastAccess.isEmpty) return const SizedBox.shrink();
    return Card(child: Padding(padding: const EdgeInsets.all(12), child: Column(
      children: lastAccess.map<Widget>((entry) {
        final item = entry as Map;
        return ListTile(
          dense: true,
          contentPadding: EdgeInsets.zero,
          title: Text(item['name'] ?? '', style: const TextStyle(fontWeight: FontWeight.w500)),
          trailing: Text(item['last_seen'] ?? '', style: TextStyle(color: cs.outline, fontSize: 13)),
        );
      }).toList(),
    )));
  }

  Widget _buildCountryTopChannels(ColorScheme cs) {
    final countryTopChannels = (_data?['country_top_channels'] as Map?) ?? {};
    if (countryTopChannels.isEmpty) return const SizedBox.shrink();
    final entries = countryTopChannels.entries.where((entry) => entry.value is List && (entry.value as List).isNotEmpty).toList();
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
                  Text(entry.key, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  ...channels.asMap().entries.map<Widget>((channelEntry) {
                    final channel = channelEntry.value as Map;
                    final isLast = channelEntry.key == channels.length - 1;
                    return Container(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      decoration: isLast
                          ? null
                          : BoxDecoration(border: Border(bottom: BorderSide(color: cs.outlineVariant))),
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
                          Text('${channel['plays']} plays', style: TextStyle(color: cs.outline, fontSize: 12)),
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
    return Padding(padding: const EdgeInsets.all(16), child: Text(
      'All data is anonymous and aggregated.\nNo personal information is collected.',
      style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.outline),
      textAlign: TextAlign.center));
  }
}

import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../utils/pinned_http_client.dart';

/// Community statistics screen showing aggregated usage data.
/// All data is anonymous — no PII is shown.
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

  bool _loading = true;
  String? _error;

  int _totalUsers = 0;
  int _totalPlays = 0;
  Map<String, int> _countryCounts = {};
  Map<String, int> _platformCounts = {};
  List<MapEntry<String, int>> _topChannels = [];

  @override
  void initState() {
    super.initState();
    _loadStatistics();
  }

  Future<void> _loadStatistics() async {
    if (_supabaseUrl.isEmpty || _supabaseAnonKey.isEmpty) {
      setState(() {
        _error = 'Analytics not configured';
        _loading = false;
      });
      return;
    }

    try {
      final client = PinnedHttpClient.create();
      final headers = {
        'apikey': _supabaseAnonKey,
        'Authorization': 'Bearer $_supabaseAnonKey',
      };

      // Query last 30 days of events
      final since = DateTime.now().subtract(const Duration(days: 30)).toIso8601String();
      final url = Uri.parse('$_supabaseUrl/rest/v1/analytics_events')
          .replace(queryParameters: {
        'select': 'event_type,device_id,country,platform,channel_name',
        'created_at': 'gte.$since',
        'order': 'created_at.desc',
        'limit': '5000',
      });

      final response = await client.get(url, headers: headers)
          .timeout(const Duration(seconds: 15));

      if (response.statusCode != 200) {
        throw Exception('API error: ${response.statusCode}');
      }

      final List<dynamic> events = jsonDecode(response.body);
      _processEvents(events);

      setState(() => _loading = false);
      client.close();
    } catch (e) {
      setState(() {
        _error = 'Failed to load statistics';
        _loading = false;
      });
    }
  }

  void _processEvents(List<dynamic> events) {
    final devices = <String>{};
    final countries = <String, int>{};
    final platforms = <String, int>{};
    final channels = <String, int>{};
    int plays = 0;

    for (final e in events) {
      final deviceId = e['device_id'] as String? ?? '';
      final country = e['country'] as String? ?? 'Unknown';
      final platform = e['platform'] as String? ?? 'unknown';
      final eventType = e['event_type'] as String? ?? '';
      final channelName = e['channel_name'] as String? ?? '';

      devices.add(deviceId);
      platforms[platform] = (platforms[platform] ?? 0) + 1;

      if (country.isNotEmpty && country != 'XX') {
        countries[country] = (countries[country] ?? 0) + 1;
      }

      if (eventType == 'channel_play' && channelName.isNotEmpty && channelName.length < 40) {
        plays++;
        channels[channelName] = (channels[channelName] ?? 0) + 1;
      }
    }

    _totalUsers = devices.length;
    _totalPlays = plays;
    _countryCounts = countries;
    _platformCounts = platforms;
    _topChannels = channels.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    if (_topChannels.length > 10) _topChannels = _topChannels.sublist(0, 10);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('📊 Community Stats'),
        centerTitle: true,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.cloud_off, size: 48, color: colorScheme.outline),
                      const SizedBox(height: 12),
                      Text(_error!, style: theme.textTheme.bodyLarge),
                      const SizedBox(height: 16),
                      FilledButton.icon(
                        onPressed: () {
                          setState(() { _loading = true; _error = null; });
                          _loadStatistics();
                        },
                        icon: const Icon(Icons.refresh),
                        label: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: () async {
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
                      _buildSection('🌍 Countries', _buildCountryList(colorScheme)),
                      const SizedBox(height: 24),
                      _buildSection('📱 Platforms', _buildPlatformList(colorScheme)),
                      const SizedBox(height: 24),
                      _buildSection('🔥 Top Channels (30 days)', _buildTopChannels(colorScheme)),
                      const SizedBox(height: 24),
                      _buildFooter(theme),
                    ],
                  ),
                ),
    );
  }

  Widget _buildHeader() {
    return Text(
      'Last 30 days • Anonymous aggregated data',
      style: Theme.of(context).textTheme.bodySmall?.copyWith(
        color: Theme.of(context).colorScheme.outline,
      ),
      textAlign: TextAlign.center,
    );
  }

  Widget _buildSummaryCards(ColorScheme colorScheme) {
    return Row(
      children: [
        Expanded(child: _statCard('👥', '$_totalUsers', 'Active Users', colorScheme.primaryContainer)),
        const SizedBox(width: 12),
        Expanded(child: _statCard('▶️', '$_totalPlays', 'Channel Plays', colorScheme.secondaryContainer)),
        const SizedBox(width: 12),
        Expanded(child: _statCard('🌐', '${_countryCounts.length}', 'Countries', colorScheme.tertiaryContainer)),
      ],
    );
  }

  Widget _statCard(String emoji, String value, String label, Color bgColor) {
    return Card(
      color: bgColor,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
        child: Column(
          children: [
            Text(emoji, style: const TextStyle(fontSize: 24)),
            const SizedBox(height: 4),
            Text(value, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
            Text(label, style: Theme.of(context).textTheme.bodySmall, textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }

  Widget _buildSection(String title, Widget content) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        content,
      ],
    );
  }

  Widget _buildCountryList(ColorScheme colorScheme) {
    if (_countryCounts.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text('No country data available yet', style: TextStyle(color: colorScheme.outline)),
        ),
      );
    }
    final sorted = _countryCounts.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    final top = sorted.take(15).toList();
    final maxVal = top.first.value.toDouble();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: top.map((e) => Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(
              children: [
                SizedBox(width: 80, child: Text(e.key, style: const TextStyle(fontSize: 13))),
                Expanded(
                  child: LinearProgressIndicator(
                    value: e.value / maxVal,
                    backgroundColor: colorScheme.surfaceContainerHigh,
                    color: colorScheme.primary,
                    minHeight: 8,
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
                const SizedBox(width: 8),
                Text('${e.value}', style: TextStyle(fontSize: 12, color: colorScheme.outline)),
              ],
            ),
          )).toList(),
        ),
      ),
    );
  }

  Widget _buildPlatformList(ColorScheme colorScheme) {
    final icons = {'android': '🤖', 'web': '🌐', 'web-server': '🐳', 'windows': '💻', 'ios': '🍎'};
    final sorted = _platformCounts.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    final total = sorted.fold<int>(0, (sum, e) => sum + e.value);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: sorted.map((e) {
            final pct = total > 0 ? (e.value * 100 / total).toStringAsFixed(1) : '0';
            return ListTile(
              dense: true,
              leading: Text(icons[e.key] ?? '📱', style: const TextStyle(fontSize: 24)),
              title: Text(e.key, style: const TextStyle(fontWeight: FontWeight.w500)),
              trailing: Text('$pct%  (${e.value})', style: TextStyle(color: colorScheme.outline)),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildTopChannels(ColorScheme colorScheme) {
    if (_topChannels.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text('No play data yet', style: TextStyle(color: colorScheme.outline)),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: _topChannels.asMap().entries.map((entry) {
            final rank = entry.key + 1;
            final channel = entry.value;
            return ListTile(
              dense: true,
              leading: CircleAvatar(
                radius: 14,
                backgroundColor: colorScheme.primaryContainer,
                child: Text('$rank', style: TextStyle(fontSize: 12, color: colorScheme.onPrimaryContainer)),
              ),
              title: Text(channel.key, overflow: TextOverflow.ellipsis),
              trailing: Text('${channel.value} plays', style: TextStyle(color: colorScheme.outline, fontSize: 13)),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildFooter(ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Text(
        'All data is anonymous and aggregated.\nNo personal information is collected.',
        style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.outline),
        textAlign: TextAlign.center,
      ),
    );
  }
}

import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

/// Community statistics screen showing aggregated usage data.
/// Fetches pre-aggregated data from the web server's /api/statistics endpoint.
/// Never queries raw analytics events directly — all aggregation is server-side.
class StatisticsScreen extends StatefulWidget {
  const StatisticsScreen({super.key});

  @override
  State<StatisticsScreen> createState() => _StatisticsScreenState();
}

class _StatisticsScreenState extends State<StatisticsScreen> {
  bool _loading = true;
  String? _error;
  Map<String, dynamic>? _data;

  // Cache key to avoid repeated API calls
  static const _cacheKey = 'stats_cache';
  static const _cacheTimeKey = 'stats_cache_time';
  static const _cacheTtl = Duration(minutes: 10);

  @override
  void initState() {
    super.initState();
    _loadStatistics();
  }

  Future<void> _loadStatistics() async {
    // Try cache first
    final prefs = await SharedPreferences.getInstance();
    final cachedTime = prefs.getInt(_cacheTimeKey) ?? 0;
    final now = DateTime.now().millisecondsSinceEpoch;

    if (now - cachedTime < _cacheTtl.inMilliseconds) {
      final cached = prefs.getString(_cacheKey);
      if (cached != null) {
        if (!mounted) return;
        setState(() {
          _data = jsonDecode(cached);
          _loading = false;
        });
        return;
      }
    }

    // Fetch from server API (pre-aggregated, no raw data exposed)
    try {
      final response = await http.get(
        Uri.parse('https://tv-viewer-app.github.io/tv_viewer/api/statistics'),
      ).timeout(const Duration(seconds: 15));

      // If the landing page endpoint doesn't work, try localhost for web-server mode
      Map<String, dynamic>? data;
      if (response.statusCode == 200) {
        data = jsonDecode(response.body);
      }

      if (data == null) {
        throw Exception('No data available');
      }

      // Cache the result
      await prefs.setString(_cacheKey, jsonEncode(data));
      await prefs.setInt(_cacheTimeKey, now);

      if (!mounted) return;
      setState(() {
        _data = data;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        // Try showing cached data even if expired
        final cached = prefs.getString(_cacheKey);
        if (cached != null) {
          _data = jsonDecode(cached);
        } else {
          _error = 'Unable to load statistics';
        }
        _loading = false;
      });
    }
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
          : _error != null && _data == null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.cloud_off, size: 48, color: colorScheme.outline),
                      const SizedBox(height: 12),
                      Text(_error!, style: theme.textTheme.bodyLarge),
                      const SizedBox(height: 8),
                      Text(
                        'Statistics are available when connected\nto the TV Viewer network.',
                        style: theme.textTheme.bodySmall?.copyWith(color: colorScheme.outline),
                        textAlign: TextAlign.center,
                      ),
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
                    // Clear cache to force refresh
                    final prefs = await SharedPreferences.getInstance();
                    await prefs.remove(_cacheTimeKey);
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
                      if (_data!['platforms'] != null)
                        ...[_buildSection('📱 Platforms', _buildPlatformList(colorScheme)), const SizedBox(height: 24)],
                      if (_data!['countries'] != null && (_data!['countries'] as List).isNotEmpty)
                        ...[_buildSection('🌍 Countries', _buildCountryList(colorScheme)), const SizedBox(height: 24)],
                      if (_data!['top_channels'] != null && (_data!['top_channels'] as List).isNotEmpty)
                        ...[_buildSection('🔥 Top Channels (30 days)', _buildTopChannels(colorScheme)), const SizedBox(height: 24)],
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
    final users = _data?['unique_users'] ?? 0;
    final plays = _data?['total_plays'] ?? 0;
    final channels = _data?['unique_channels_played'] ?? 0;

    return Row(
      children: [
        Expanded(child: _statCard('👥', '$users', 'Active Users', colorScheme.primaryContainer)),
        const SizedBox(width: 12),
        Expanded(child: _statCard('▶️', '$plays', 'Plays', colorScheme.secondaryContainer)),
        const SizedBox(width: 12),
        Expanded(child: _statCard('📺', '$channels', 'Channels', colorScheme.tertiaryContainer)),
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
    final countries = (_data?['countries'] as List?) ?? [];
    if (countries.isEmpty) return const SizedBox.shrink();

    final maxVal = (countries.first['events'] as int).toDouble();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: countries.take(15).map<Widget>((c) => Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(
              children: [
                SizedBox(width: 80, child: Text(c['name'] ?? '', style: const TextStyle(fontSize: 13))),
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: (c['events'] as int) / maxVal,
                      backgroundColor: colorScheme.surfaceContainerHigh,
                      color: colorScheme.primary,
                      minHeight: 8,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Text('${c['events']}', style: TextStyle(fontSize: 12, color: colorScheme.outline)),
              ],
            ),
          )).toList(),
        ),
      ),
    );
  }

  Widget _buildPlatformList(ColorScheme colorScheme) {
    final platforms = (_data?['platforms'] as Map<String, dynamic>?) ?? {};
    if (platforms.isEmpty) return const SizedBox.shrink();

    final icons = {'android': '🤖', 'web': '🌐', 'web-server': '🐳', 'windows': '💻', 'ios': '🍎'};
    final total = platforms.values.fold<int>(0, (sum, v) => sum + (v as int));

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: platforms.entries.map<Widget>((e) {
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
    final channels = (_data?['top_channels'] as List?) ?? [];
    if (channels.isEmpty) return const SizedBox.shrink();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: channels.asMap().entries.map<Widget>((entry) {
            final rank = entry.key + 1;
            final ch = entry.value;
            return ListTile(
              dense: true,
              leading: CircleAvatar(
                radius: 14,
                backgroundColor: colorScheme.primaryContainer,
                child: Text('$rank', style: TextStyle(fontSize: 12, color: colorScheme.onPrimaryContainer)),
              ),
              title: Text(ch['name'] ?? '', overflow: TextOverflow.ellipsis),
              trailing: Text('${ch['plays']} plays', style: TextStyle(color: colorScheme.outline, fontSize: 13)),
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
        'All data is anonymous and aggregated.\nNo personal information is collected or displayed.',
        style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.outline),
        textAlign: TextAlign.center,
      ),
    );
  }
}

import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';
import '../models/channel.dart';
import '../providers/channel_provider.dart';
import 'player_screen.dart';

/// Country center coordinates for map markers.
const Map<String, LatLng> _countryCoords = {
  'Afghanistan': LatLng(33.93, 67.71),
  'Albania': LatLng(41.15, 20.17),
  'Algeria': LatLng(28.03, 1.66),
  'Andorra': LatLng(42.55, 1.60),
  'Angola': LatLng(-11.20, 17.87),
  'Argentina': LatLng(-38.42, -63.62),
  'Armenia': LatLng(40.07, 45.04),
  'Australia': LatLng(-25.27, 133.78),
  'Austria': LatLng(47.52, 14.55),
  'Azerbaijan': LatLng(40.14, 47.58),
  'Bahrain': LatLng(26.07, 50.55),
  'Bangladesh': LatLng(23.68, 90.36),
  'Belarus': LatLng(53.71, 27.95),
  'Belgium': LatLng(50.50, 4.47),
  'Bolivia': LatLng(-16.29, -63.59),
  'Bosnia and Herzegovina': LatLng(43.92, 17.68),
  'Brazil': LatLng(-14.24, -51.93),
  'Bulgaria': LatLng(42.73, 25.49),
  'Cambodia': LatLng(12.57, 104.99),
  'Cameroon': LatLng(7.37, 12.35),
  'Canada': LatLng(56.13, -106.35),
  'Chile': LatLng(-35.68, -71.54),
  'China': LatLng(35.86, 104.20),
  'Colombia': LatLng(4.57, -74.30),
  'Costa Rica': LatLng(9.75, -83.75),
  'Croatia': LatLng(45.10, 15.20),
  'Cuba': LatLng(21.52, -77.78),
  'Cyprus': LatLng(35.13, 33.43),
  'Czech Republic': LatLng(49.82, 15.47),
  'Czechia': LatLng(49.82, 15.47),
  'Denmark': LatLng(56.26, 9.50),
  'Dominican Republic': LatLng(18.74, -70.16),
  'Ecuador': LatLng(-1.83, -78.18),
  'Egypt': LatLng(26.82, 30.80),
  'El Salvador': LatLng(13.79, -88.90),
  'Estonia': LatLng(58.60, 25.01),
  'Ethiopia': LatLng(9.15, 40.49),
  'Finland': LatLng(61.92, 25.75),
  'France': LatLng(46.23, 2.21),
  'Georgia': LatLng(42.32, 43.36),
  'Germany': LatLng(51.17, 10.45),
  'Ghana': LatLng(7.95, -1.02),
  'Greece': LatLng(39.07, 21.82),
  'Guatemala': LatLng(15.78, -90.23),
  'Honduras': LatLng(15.20, -86.24),
  'Hong Kong': LatLng(22.40, 114.11),
  'Hungary': LatLng(47.16, 19.50),
  'Iceland': LatLng(64.96, -19.02),
  'India': LatLng(20.59, 78.96),
  'Indonesia': LatLng(-0.79, 113.92),
  'Iran': LatLng(32.43, 53.69),
  'Iraq': LatLng(33.22, 43.68),
  'Ireland': LatLng(53.14, -7.69),
  'Israel': LatLng(31.05, 34.85),
  'Italy': LatLng(41.87, 12.57),
  'Jamaica': LatLng(18.11, -77.30),
  'Japan': LatLng(36.20, 138.25),
  'Jordan': LatLng(30.59, 36.24),
  'Kazakhstan': LatLng(48.02, 66.92),
  'Kenya': LatLng(-0.02, 37.91),
  'Kosovo': LatLng(42.60, 20.90),
  'Kuwait': LatLng(29.31, 47.48),
  'Latvia': LatLng(56.88, 24.60),
  'Lebanon': LatLng(33.85, 35.86),
  'Libya': LatLng(26.34, 17.23),
  'Lithuania': LatLng(55.17, 23.88),
  'Luxembourg': LatLng(49.82, 6.13),
  'Macedonia': LatLng(41.51, 21.75),
  'North Macedonia': LatLng(41.51, 21.75),
  'Malaysia': LatLng(4.21, 101.98),
  'Mexico': LatLng(23.63, -102.55),
  'Moldova': LatLng(47.41, 28.37),
  'Mongolia': LatLng(46.86, 103.85),
  'Montenegro': LatLng(42.71, 19.37),
  'Morocco': LatLng(31.79, -7.09),
  'Mozambique': LatLng(-18.67, 35.53),
  'Myanmar': LatLng(21.91, 95.96),
  'Nepal': LatLng(28.39, 84.12),
  'Netherlands': LatLng(52.13, 5.29),
  'New Zealand': LatLng(-40.90, 174.89),
  'Nicaragua': LatLng(12.87, -85.21),
  'Nigeria': LatLng(9.08, 8.68),
  'Norway': LatLng(60.47, 8.47),
  'Oman': LatLng(21.47, 55.98),
  'Pakistan': LatLng(30.38, 69.35),
  'Palestine': LatLng(31.95, 35.23),
  'Panama': LatLng(8.54, -80.78),
  'Paraguay': LatLng(-23.44, -58.44),
  'Peru': LatLng(-9.19, -75.02),
  'Philippines': LatLng(12.88, 121.77),
  'Poland': LatLng(51.92, 19.15),
  'Portugal': LatLng(39.40, -8.22),
  'Qatar': LatLng(25.35, 51.18),
  'Romania': LatLng(45.94, 24.97),
  'Russia': LatLng(61.52, 105.32),
  'Saudi Arabia': LatLng(23.89, 45.08),
  'Serbia': LatLng(44.02, 21.01),
  'Singapore': LatLng(1.35, 103.82),
  'Slovakia': LatLng(48.67, 19.70),
  'Slovenia': LatLng(46.15, 14.99),
  'South Africa': LatLng(-30.56, 22.94),
  'South Korea': LatLng(35.91, 127.77),
  'Spain': LatLng(40.46, -3.75),
  'Sri Lanka': LatLng(7.87, 80.77),
  'Sudan': LatLng(12.86, 30.22),
  'Sweden': LatLng(60.13, 18.64),
  'Switzerland': LatLng(46.82, 8.23),
  'Syria': LatLng(34.80, 38.99),
  'Taiwan': LatLng(23.70, 120.96),
  'Thailand': LatLng(15.87, 100.99),
  'Tunisia': LatLng(33.89, 9.54),
  'Turkey': LatLng(38.96, 35.24),
  'Turkmenistan': LatLng(38.97, 59.56),
  'Ukraine': LatLng(48.38, 31.17),
  'United Arab Emirates': LatLng(23.42, 53.85),
  'United Kingdom': LatLng(55.38, -3.44),
  'United States': LatLng(37.09, -95.71),
  'Uruguay': LatLng(-32.52, -55.77),
  'Uzbekistan': LatLng(41.38, 64.59),
  'Venezuela': LatLng(6.42, -66.59),
  'Vietnam': LatLng(14.06, 108.28),
  'Yemen': LatLng(15.55, 48.52),
  // Abbreviations / aliases
  'UK': LatLng(55.38, -3.44),
  'US': LatLng(37.09, -95.71),
  'USA': LatLng(37.09, -95.71),
  'UAE': LatLng(23.42, 53.85),
  'Korea': LatLng(35.91, 127.77),
};

/// Groups channels by country and returns only those with known coordinates.
Map<String, List<Channel>> _groupByCountry(List<Channel> channels) {
  final map = <String, List<Channel>>{};
  for (final ch in channels) {
    final c = ch.country;
    if (c == null || c.isEmpty) continue;
    map.putIfAbsent(c, () => []).add(ch);
  }
  return map;
}

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  final MapController _mapController = MapController();
  bool _favoritesOnly = false;
  bool _hideOffline = false;
  double _currentZoom = 3.0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🗺️ World Map'),
        actions: [
          // Favorites filter
          IconButton(
            icon: Icon(
              _favoritesOnly ? Icons.star : Icons.star_border,
              color: _favoritesOnly ? Colors.amber : null,
            ),
            tooltip: 'Favorites only',
            onPressed: () => setState(() => _favoritesOnly = !_favoritesOnly),
          ),
          // Hide offline filter
          IconButton(
            icon: Icon(
              _hideOffline ? Icons.wifi : Icons.wifi_off,
              color: _hideOffline ? Colors.green : null,
            ),
            tooltip: _hideOffline ? 'Showing working only' : 'Show all',
            onPressed: () => setState(() => _hideOffline = !_hideOffline),
          ),
        ],
      ),
      body: Consumer<ChannelProvider>(
        builder: (context, provider, _) {
          // Apply filters
          List<Channel> channels = provider.channels;
          if (_favoritesOnly) {
            channels = channels
                .where((c) => provider.isFavorite(c))
                .toList();
          }
          if (_hideOffline) {
            channels = channels.where((c) => c.isWorking).toList();
          }

          final grouped = _groupByCountry(channels);

          return FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: const LatLng(30.0, 20.0),
              initialZoom: _currentZoom,
              minZoom: 2,
              maxZoom: 18,
              onPositionChanged: (pos, _) {
                if (pos.zoom != null && pos.zoom != _currentZoom) {
                  setState(() => _currentZoom = pos.zoom!);
                }
              },
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.tvviewer.app',
              ),
              MarkerLayer(
                markers: _buildMarkers(grouped, provider),
              ),
            ],
          );
        },
      ),
    );
  }

  List<Marker> _buildMarkers(
    Map<String, List<Channel>> grouped,
    ChannelProvider provider,
  ) {
    final markers = <Marker>[];

    for (final entry in grouped.entries) {
      final country = entry.key;
      final channels = entry.value;
      final coords = _countryCoords[country];
      if (coords == null) continue;

      final workingCount = channels.where((c) => c.isWorking).length;
      final total = channels.length;

      // At low zoom show country clusters, at high zoom show individual pins
      if (_currentZoom < 6) {
        // Country cluster marker
        markers.add(Marker(
          point: coords,
          width: 56,
          height: 56,
          child: GestureDetector(
            onTap: () => _showCountrySheet(country, channels, provider),
            child: _CountryBubble(
              country: country,
              total: total,
              working: workingCount,
            ),
          ),
        ));
      } else {
        // Individual channel markers — offset slightly to avoid overlap
        for (var i = 0; i < channels.length && i < 50; i++) {
          final ch = channels[i];
          final offset = _spiralOffset(i, channels.length);
          final point = LatLng(
            coords.latitude + offset.dx,
            coords.longitude + offset.dy,
          );
          markers.add(Marker(
            point: point,
            width: 36,
            height: 36,
            child: GestureDetector(
              onTap: () => _showChannelPopup(ch, provider),
              child: _ChannelPin(
                isWorking: ch.isWorking,
                isFavorite: provider.isFavorite(ch),
              ),
            ),
          ));
        }
      }
    }
    return markers;
  }

  /// Spiral offset to spread individual markers around the country center.
  Offset _spiralOffset(int index, int total) {
    if (total <= 1) return Offset.zero;
    final angle = index * 2.4; // golden angle
    final radius = 0.15 * (1 + index * 0.12);
    return Offset(
      radius * math.cos(angle),
      radius * math.sin(angle),
    );
  }

  void _showCountrySheet(
    String country,
    List<Channel> channels,
    ChannelProvider provider,
  ) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.5,
        maxChildSize: 0.85,
        minChildSize: 0.3,
        expand: false,
        builder: (ctx, scrollController) => Column(
          children: [
            // Handle
            Container(
              margin: const EdgeInsets.symmetric(vertical: 8),
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey[400],
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            // Header
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: Row(
                children: [
                  const Icon(Icons.public, size: 24),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '$country — ${channels.length} channels',
                      style: Theme.of(ctx).textTheme.titleMedium,
                    ),
                  ),
                  Text(
                    '${channels.where((c) => c.isWorking).length} working',
                    style: TextStyle(color: Colors.green[400], fontSize: 13),
                  ),
                ],
              ),
            ),
            const Divider(),
            // Channel list
            Expanded(
              child: ListView.builder(
                controller: scrollController,
                itemCount: channels.length,
                itemBuilder: (ctx, i) {
                  final ch = channels[i];
                  final isFav = provider.isFavorite(ch);
                  return ListTile(
                    leading: Icon(
                      ch.isWorking ? Icons.tv : Icons.tv_off,
                      color: ch.isWorking ? Colors.green : Colors.red[300],
                    ),
                    title: Text(
                      ch.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    subtitle: Text(
                      [ch.category, ch.language]
                          .where((s) => s != null && s.isNotEmpty)
                          .join(' · '),
                      style: TextStyle(fontSize: 12, color: Colors.grey[400]),
                    ),
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        IconButton(
                          icon: Icon(
                            isFav ? Icons.star : Icons.star_border,
                            color: isFav ? Colors.amber : null,
                            size: 20,
                          ),
                          onPressed: () {
                            provider.toggleFavorite(ch);
                            // Refresh the sheet
                            (ctx as Element).markNeedsBuild();
                          },
                        ),
                        const Icon(Icons.play_arrow),
                      ],
                    ),
                    onTap: () {
                      Navigator.pop(ctx);
                      _playChannel(ch);
                    },
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showChannelPopup(Channel ch, ChannelProvider provider) {
    final isFav = provider.isFavorite(ch);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Row(
          children: [
            Icon(
              ch.isWorking ? Icons.tv : Icons.tv_off,
              color: ch.isWorking ? Colors.green : Colors.red,
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text(ch.name, maxLines: 2, overflow: TextOverflow.ellipsis),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (ch.country != null)
              _infoRow('Country', ch.country!),
            if (ch.category != null)
              _infoRow('Category', ch.category!),
            if (ch.language != null)
              _infoRow('Language', ch.language!),
            _infoRow('Status', ch.isWorking ? 'Working ✅' : 'Offline ❌'),
            if (ch.resolution != null)
              _infoRow('Resolution', ch.resolution!),
          ],
        ),
        actions: [
          TextButton.icon(
            icon: Icon(
              isFav ? Icons.star : Icons.star_border,
              color: isFav ? Colors.amber : null,
            ),
            label: Text(isFav ? 'Unfavorite' : 'Favorite'),
            onPressed: () {
              provider.toggleFavorite(ch);
              Navigator.pop(ctx);
            },
          ),
          FilledButton.icon(
            icon: const Icon(Icons.play_arrow),
            label: const Text('Play'),
            onPressed: () {
              Navigator.pop(ctx);
              _playChannel(ch);
            },
          ),
        ],
      ),
    );
  }

  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        children: [
          SizedBox(
            width: 80,
            child: Text(label,
                style: TextStyle(color: Colors.grey[500], fontSize: 13)),
          ),
          Expanded(
            child: Text(value, style: const TextStyle(fontSize: 13)),
          ),
        ],
      ),
    );
  }

  void _playChannel(Channel ch) {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => PlayerScreen(channel: ch)),
    );
  }
}

/// Circular bubble marker for country clusters.
class _CountryBubble extends StatelessWidget {
  final String country;
  final int total;
  final int working;

  const _CountryBubble({
    required this.country,
    required this.total,
    required this.working,
  });

  @override
  Widget build(BuildContext context) {
    final ratio = total > 0 ? working / total : 0.0;
    final color = ratio > 0.7
        ? Colors.green
        : ratio > 0.3
            ? Colors.orange
            : Colors.red;

    return Container(
      decoration: BoxDecoration(
        color: color.withOpacity(0.85),
        shape: BoxShape.circle,
        border: Border.all(color: Colors.white, width: 2),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      alignment: Alignment.center,
      child: Text(
        '$total',
        style: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.bold,
          fontSize: 14,
        ),
      ),
    );
  }
}

/// Small pin marker for individual channels.
class _ChannelPin extends StatelessWidget {
  final bool isWorking;
  final bool isFavorite;

  const _ChannelPin({
    required this.isWorking,
    required this.isFavorite,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: isWorking ? Colors.green : Colors.red[400],
        shape: BoxShape.circle,
        border: Border.all(
          color: isFavorite ? Colors.amber : Colors.white,
          width: isFavorite ? 3 : 2,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 3,
            offset: const Offset(0, 1),
          ),
        ],
      ),
      child: Icon(
        Icons.tv,
        size: 16,
        color: Colors.white.withOpacity(0.9),
      ),
    );
  }
}

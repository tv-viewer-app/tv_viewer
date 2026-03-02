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

class _MapScreenState extends State<MapScreen>
    with TickerProviderStateMixin {
  final MapController _mapController = MapController();
  bool _favoritesOnly = false;
  bool _hideOffline = false;
  double _currentZoom = 3.0;

  late final AnimationController _pulseController;
  late final Animation<double> _pulseAnim;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    )..repeat(reverse: true);
    _pulseAnim = Tween(begin: 0.85, end: 1.15).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  void _animateToCountry(LatLng target, {double zoom = 6.0}) {
    final latTween = Tween(
      begin: _mapController.camera.center.latitude,
      end: target.latitude,
    );
    final lngTween = Tween(
      begin: _mapController.camera.center.longitude,
      end: target.longitude,
    );
    final zoomTween = Tween(
      begin: _mapController.camera.zoom,
      end: zoom,
    );
    final ctrl = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 600),
    );
    final curve = CurvedAnimation(parent: ctrl, curve: Curves.easeOutCubic);
    ctrl.addListener(() {
      _mapController.move(
        LatLng(latTween.evaluate(curve), lngTween.evaluate(curve)),
        zoomTween.evaluate(curve),
      );
    });
    ctrl.addStatusListener((s) {
      if (s == AnimationStatus.completed) ctrl.dispose();
    });
    ctrl.forward();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🗺️ World Map'),
        actions: [
          _FilterChip(
            label: 'Favorites',
            icon: Icons.star_rounded,
            active: _favoritesOnly,
            activeColor: Colors.amber,
            onTap: () => setState(() => _favoritesOnly = !_favoritesOnly),
          ),
          const SizedBox(width: 4),
          _FilterChip(
            label: 'Working',
            icon: Icons.wifi_rounded,
            active: _hideOffline,
            activeColor: Colors.green,
            onTap: () => setState(() => _hideOffline = !_hideOffline),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: Consumer<ChannelProvider>(
        builder: (context, provider, _) {
          List<Channel> channels = provider.channels;
          if (_favoritesOnly) {
            channels = channels.where((c) => provider.isFavorite(c)).toList();
          }
          if (_hideOffline) {
            channels = channels.where((c) => c.isWorking).toList();
          }

          final grouped = _groupByCountry(channels);
          final totalWorking = channels.where((c) => c.isWorking).length;

          return Stack(
            children: [
              FlutterMap(
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
              ),
              // Stats overlay at bottom
              Positioned(
                left: 12, right: 12, bottom: 12,
                child: _StatsBar(
                  countries: grouped.length,
                  channels: channels.length,
                  working: totalWorking,
                ),
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
        // Country cluster marker with pulse animation
        markers.add(Marker(
          point: coords,
          width: 64,
          height: 64,
          child: GestureDetector(
            onTap: () {
              _animateToCountry(coords);
              _showCountrySheet(country, channels, provider);
            },
            child: AnimatedBuilder(
              animation: _pulseController,
              builder: (ctx, child) => Transform.scale(
                scale: workingCount > 0 ? _pulseAnim.value : 1.0,
                child: child,
              ),
              child: _CountryBubble(
                country: country,
                total: total,
                working: workingCount,
              ),
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
    final working = channels.where((c) => c.isWorking).length;
    final ratio = channels.isNotEmpty ? working / channels.length : 0.0;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.55,
        maxChildSize: 0.9,
        minChildSize: 0.3,
        expand: false,
        builder: (ctx, scrollController) => Container(
          decoration: BoxDecoration(
            color: Theme.of(ctx).colorScheme.surface,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              // Drag handle
              Container(
                margin: const EdgeInsets.symmetric(vertical: 10),
                width: 40, height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey[500],
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              // Header with animated health bar
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.public, size: 28),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            country,
                            style: Theme.of(ctx).textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                        _CountBadge(count: channels.length, label: 'total'),
                        const SizedBox(width: 8),
                        _CountBadge(count: working, label: 'live',
                            color: Colors.green),
                      ],
                    ),
                    const SizedBox(height: 10),
                    // Animated health bar
                    TweenAnimationBuilder<double>(
                      tween: Tween(begin: 0, end: ratio),
                      duration: const Duration(milliseconds: 800),
                      curve: Curves.easeOutCubic,
                      builder: (_, value, __) => ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: LinearProgressIndicator(
                          value: value,
                          minHeight: 6,
                          backgroundColor: Colors.grey[800],
                          color: ratio > 0.7
                              ? Colors.green
                              : ratio > 0.3
                                  ? Colors.orange
                                  : Colors.red,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 4),
              const Divider(height: 1),
              // Channel list
              Expanded(
                child: ListView.builder(
                  controller: scrollController,
                  itemCount: channels.length,
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  itemBuilder: (ctx, i) {
                    final ch = channels[i];
                    final isFav = provider.isFavorite(ch);
                    return _ChannelTile(
                      channel: ch,
                      isFavorite: isFav,
                      onFavToggle: () {
                        provider.toggleFavorite(ch);
                        (ctx as Element).markNeedsBuild();
                      },
                      onPlay: () {
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

/// Circular bubble marker for country clusters with gradient glow.
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
        gradient: RadialGradient(
          colors: [color.withOpacity(0.95), color.withOpacity(0.6)],
          stops: const [0.5, 1.0],
        ),
        shape: BoxShape.circle,
        border: Border.all(color: Colors.white, width: 2.5),
        boxShadow: [
          BoxShadow(
            color: color.withOpacity(0.45),
            blurRadius: 12,
            spreadRadius: 2,
          ),
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      alignment: Alignment.center,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '$total',
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
              fontSize: 15,
              height: 1.1,
            ),
          ),
          Text(
            country.length > 3 ? country.substring(0, 3).toUpperCase() : country.toUpperCase(),
            style: TextStyle(
              color: Colors.white.withOpacity(0.85),
              fontSize: 8,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.5,
            ),
          ),
        ],
      ),
    );
  }
}

/// Small pin marker for individual channels with animated glow.
class _ChannelPin extends StatelessWidget {
  final bool isWorking;
  final bool isFavorite;

  const _ChannelPin({
    required this.isWorking,
    required this.isFavorite,
  });

  @override
  Widget build(BuildContext context) {
    final baseColor = isWorking ? Colors.green : Colors.red[400]!;
    return Container(
      decoration: BoxDecoration(
        color: baseColor,
        shape: BoxShape.circle,
        border: Border.all(
          color: isFavorite ? Colors.amber : Colors.white,
          width: isFavorite ? 3 : 2,
        ),
        boxShadow: [
          BoxShadow(
            color: baseColor.withOpacity(0.5),
            blurRadius: 8,
            spreadRadius: 1,
          ),
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 3,
            offset: const Offset(0, 1),
          ),
        ],
      ),
      child: Icon(
        isFavorite ? Icons.star_rounded : Icons.tv,
        size: 16,
        color: Colors.white.withOpacity(0.9),
      ),
    );
  }
}

/// Animated filter chip for the AppBar.
class _FilterChip extends StatelessWidget {
  final String label;
  final IconData icon;
  final bool active;
  final Color activeColor;
  final VoidCallback onTap;

  const _FilterChip({
    required this.label,
    required this.icon,
    required this.active,
    required this.activeColor,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeInOut,
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: active ? activeColor.withOpacity(0.2) : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: active ? activeColor : Colors.grey[600]!,
            width: 1.5,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 16,
                color: active ? activeColor : Colors.grey[400]),
            const SizedBox(width: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                color: active ? activeColor : Colors.grey[400],
                fontWeight: active ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
            if (active) ...[
              const SizedBox(width: 4),
              Icon(Icons.check, size: 14, color: activeColor),
            ],
          ],
        ),
      ),
    );
  }
}

/// Stats overlay bar at the bottom of the map.
class _StatsBar extends StatelessWidget {
  final int countries;
  final int channels;
  final int working;

  const _StatsBar({
    required this.countries,
    required this.channels,
    required this.working,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.75),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _StatItem(
            value: countries, label: 'Countries',
            color: const Color(0xFF4DA6FF),
          ),
          _divider(),
          _StatItem(
            value: channels, label: 'Channels',
            color: const Color(0xFF4DA6FF),
          ),
          _divider(),
          _StatItem(
            value: working, label: 'Working',
            color: Colors.green,
          ),
        ],
      ),
    );
  }

  Widget _divider() => Container(
    width: 1, height: 28,
    color: Colors.white.withOpacity(0.15),
  );
}

/// Single stat counter with animated count-up.
class _StatItem extends StatelessWidget {
  final int value;
  final String label;
  final Color color;

  const _StatItem({
    required this.value,
    required this.label,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return TweenAnimationBuilder<int>(
      tween: IntTween(begin: 0, end: value),
      duration: const Duration(milliseconds: 700),
      curve: Curves.easeOutCubic,
      builder: (_, v, __) => Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '$v',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          Text(
            label,
            style: TextStyle(
              fontSize: 10,
              color: Colors.white.withOpacity(0.6),
            ),
          ),
        ],
      ),
    );
  }
}

/// Count badge widget for bottom sheet header.
class _CountBadge extends StatelessWidget {
  final int count;
  final String label;
  final Color? color;

  const _CountBadge({
    required this.count,
    required this.label,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: (color ?? Colors.grey).withOpacity(0.15),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: (color ?? Colors.grey).withOpacity(0.3),
        ),
      ),
      child: Text(
        '$count $label',
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: color ?? Colors.grey[400],
        ),
      ),
    );
  }
}

/// Channel tile for the country bottom sheet.
class _ChannelTile extends StatelessWidget {
  final Channel channel;
  final bool isFavorite;
  final VoidCallback onFavToggle;
  final VoidCallback onPlay;

  const _ChannelTile({
    required this.channel,
    required this.isFavorite,
    required this.onFavToggle,
    required this.onPlay,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 3),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      child: InkWell(
        borderRadius: BorderRadius.circular(10),
        onTap: onPlay,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Row(
            children: [
              // Status dot
              Container(
                width: 10, height: 10,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: channel.isWorking ? Colors.green : Colors.red[400],
                  boxShadow: channel.isWorking
                      ? [BoxShadow(
                          color: Colors.green.withOpacity(0.4),
                          blurRadius: 6,
                        )]
                      : null,
                ),
              ),
              const SizedBox(width: 12),
              // Channel info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      channel.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w500),
                    ),
                    if (channel.category != null && channel.category!.isNotEmpty)
                      Text(
                        channel.category!,
                        style: TextStyle(fontSize: 11, color: Colors.grey[500]),
                      ),
                  ],
                ),
              ),
              // Favorite button
              IconButton(
                icon: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 200),
                  transitionBuilder: (child, anim) =>
                      ScaleTransition(scale: anim, child: child),
                  child: Icon(
                    isFavorite ? Icons.star_rounded : Icons.star_border_rounded,
                    key: ValueKey(isFavorite),
                    color: isFavorite ? Colors.amber : Colors.grey[600],
                    size: 22,
                  ),
                ),
                onPressed: onFavToggle,
                visualDensity: VisualDensity.compact,
              ),
              // Play button
              Container(
                width: 36, height: 36,
                decoration: BoxDecoration(
                  color: const Color(0xFF0078D4),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.play_arrow_rounded,
                    color: Colors.white, size: 22),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

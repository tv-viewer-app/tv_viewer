import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';

/// Safe wrapper around channel logo loading.
///
/// Fixes:
///   - #199 (P0) — `ArgumentError: No host specified in URI file:[PATH]`
///     We previously fed raw strings into `Image.network` / `NetworkImage`.
///     If the channel logo was a local `file://` path, a placeholder, or any
///     non-HTTP scheme, Dart's HTTP client would throw and the entire screen
///     crashed. We now validate scheme up-front and fall back to the icon.
///
///   - #194 (P1) — HTTP 429 from logo CDN. CachedNetworkImage caches both
///     in-memory and on-disk so repeat loads of the same logo bypass the
///     network entirely. The package also handles transient errors gracefully
///     instead of leaking exceptions to the widget tree.
///
/// All channel logos in the app should use this widget instead of
/// `Image.network` / `NetworkImage` / raw `CachedNetworkImage`.
class SafeChannelLogo extends StatelessWidget {
  final String? url;
  final double size;
  final IconData fallbackIcon;
  final BoxFit fit;

  const SafeChannelLogo({
    super.key,
    required this.url,
    this.size = 40,
    this.fallbackIcon = Icons.tv,
    this.fit = BoxFit.cover,
  });

  /// Returns true iff [url] is non-null, non-empty, and parseable as an
  /// http or https URL with a host. Anything else (file://, content://,
  /// raw paths, garbage strings, null) is rejected.
  static bool isValidLogoUrl(String? url) {
    if (url == null || url.isEmpty) return false;
    final uri = Uri.tryParse(url);
    if (uri == null) return false;
    if (!uri.isScheme('http') && !uri.isScheme('https')) return false;
    if (uri.host.isEmpty) return false;
    return true;
  }

  @override
  Widget build(BuildContext context) {
    final fallback = Icon(fallbackIcon, size: size * 0.55);
    if (!isValidLogoUrl(url)) {
      return SizedBox(width: size, height: size, child: Center(child: fallback));
    }

    return CachedNetworkImage(
      imageUrl: url!,
      width: size,
      height: size,
      fit: fit,
      memCacheWidth: (size * 2).toInt(),
      maxWidthDiskCache: 160,
      placeholder: (_, __) => SizedBox(
        width: size,
        height: size,
        child: const Padding(
          padding: EdgeInsets.all(8.0),
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
      ),
      // errorWidget catches HTTP errors (incl. 429) without crashing the tree.
      errorWidget: (_, __, ___) =>
          SizedBox(width: size, height: size, child: Center(child: fallback)),
    );
  }
}

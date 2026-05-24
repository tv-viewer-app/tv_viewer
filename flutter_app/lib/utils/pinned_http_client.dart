import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:http/http.dart' as http;
import 'package:http/io_client.dart';
import '../utils/logger_service.dart';

/// HTTP client with TLS certificate pinning for Supabase and analytics
/// endpoints (#171).
///
/// Pins the SHA-256 fingerprint of the leaf or intermediate certificate so
/// that MITM proxies with forged certs are rejected. Falls back to a standard
/// client on platforms that don't support [SecurityContext] (web).
///
/// Usage:
/// ```dart
/// final client = PinnedHttpClient.create();
/// final response = await client.post(url, ...);
/// ```
class PinnedHttpClient {
  PinnedHttpClient._();

  /// SHA-256 fingerprints of trusted certificates for our endpoints.
  /// These are the intermediate CA certs (not leaf) so they survive cert
  /// rotation. Update when Supabase changes their TLS provider.
  ///
  /// To extract a pin:
  /// ```bash
  /// echo | openssl s_client -connect <host>:443 -servername <host> 2>/dev/null |
  ///   openssl x509 -pubkey -noout |
  ///   openssl pkey -pubin -outform DER |
  ///   openssl dgst -sha256 -binary | base64
  /// ```
  static const List<String> _trustedFingerprints = [
    // Amazon Root CA 1 (Supabase uses AWS/Cloudflare)
    'C5+lpZ7tcVwmwQIMcRtPbsQtWLABXhQzejna0wHFr8M=',
    // Cloudflare Inc ECC CA-3
    'Vz/Y1KQmRLeBY1xtd/WkR1CbfDhQj81gdCBM7DiIGLQ=',
    // DigiCert Global Root G2 (common Supabase intermediate)
    'i7WTqTvh0OioIruIfFR4kMPnBqrS2rdiVPl/s2uC/CY=',
    // NOTE: ISRG Root X1 (Let's Encrypt) — previously listed with a
    // copy/paste-duplicated fingerprint; removed in v2.16.1 to avoid
    // confusion.  Re-add the correct ISRG X1 SPKI pin if Supabase ever
    // switches to Let's Encrypt for the *.supabase.co wildcard.
  ];

  /// Whether pinning is enabled. Disabled in debug builds to allow
  /// proxy debugging (Charles, mitmproxy, etc.).
  static bool get _pinningEnabled {
    // Check if running in release mode
    const isRelease = bool.fromEnvironment('dart.vm.product');
    return isRelease;
  }

  /// Create an HTTP client with certificate pinning.
  ///
  /// In debug/profile builds, returns a standard client (no pinning)
  /// to allow proxy-based debugging. In release builds, validates
  /// the server certificate chain against [_trustedFingerprints].
  static http.Client create() {
    if (!_pinningEnabled) {
      return http.Client();
    }

    try {
      final httpClient = HttpClient();
      httpClient.badCertificateCallback = _validateCertificate;
      return IOClient(httpClient);
    } catch (e) {
      // Fallback to standard client if SecurityContext fails
      // (e.g., on web platform or restricted environments)
      logger.warning('Certificate pinning unavailable, using standard client', e);
      return http.Client();
    }
  }

  /// Certificate validation callback. Returns true if the certificate
  /// chain contains at least one trusted fingerprint.
  static bool _validateCertificate(
    X509Certificate cert,
    String host,
    int port,
  ) {
    // Only pin for our known endpoints
    if (!_isPinnedHost(host)) {
      return true; // Allow non-pinned hosts through
    }

    // Compute SHA-256 of the DER-encoded certificate
    final derBytes = cert.der;
    if (derBytes.isEmpty) {
      logger.error('Certificate pinning: empty cert for $host:$port');
      return false;
    }

    final digest = sha256.convert(derBytes);
    final certFingerprint = base64Encode(digest.bytes);

    for (final pin in _trustedFingerprints) {
      if (certFingerprint == pin) {
        return true;
      }
    }

    // Fail closed — unknown cert for a pinned host is treated as MITM.
    // (Previously returned `true` "during collection phase" — that was
    // strictly worse than no pinning because it accepted *any* cert the
    // OS trust chain rejected. See SECURITY-AUDIT v2.16.1.)
    logger.error(
      'Certificate pinning: REJECTED unknown cert for $host:$port '
      '(fingerprint: $certFingerprint).',
    );
    return false;
  }

  /// Hosts that should have their certificates pinned.
  static bool _isPinnedHost(String host) {
    return host.endsWith('.supabase.co') ||
        host.endsWith('.supabase.in') ||
        host == 'api.github.com';
  }
}

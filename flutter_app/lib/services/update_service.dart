import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:package_info_plus/package_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../utils/logger_service.dart';

/// Service that checks GitHub Releases for newer app versions.
class UpdateService {
  static const _repoOwner = 'tv-viewer-app';
  static const _repoName = 'tv_viewer';
  static const _releasesApi =
      'https://api.github.com/repos/$_repoOwner/$_repoName/releases/latest';
  static const _releasesPage =
      'https://github.com/$_repoOwner/$_repoName/releases';
  static const _checkIntervalKey = 'last_update_check';
  static const _dismissedVersionKey = 'dismissed_update_version';
  static const _checkIntervalHours = 24;

  /// Check for updates. Returns version string if a newer release exists,
  /// or null if up-to-date or check is skipped.
  static Future<String?> checkForUpdate() async {
    try {
      // Rate-limit: check at most once per 24 hours
      final prefs = await SharedPreferences.getInstance();
      final lastCheck = prefs.getInt(_checkIntervalKey) ?? 0;
      final now = DateTime.now().millisecondsSinceEpoch;
      if (now - lastCheck < _checkIntervalHours * 3600 * 1000) {
        return null;
      }

      final response = await http
          .get(Uri.parse(_releasesApi), headers: {
        'Accept': 'application/vnd.github.v3+json',
      }).timeout(const Duration(seconds: 10));

      if (response.statusCode != 200) return null;

      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final tagName = data['tag_name'] as String? ?? '';
      final latestVersion = tagName.replaceFirst(RegExp(r'^v'), '');

      // Save check timestamp
      await prefs.setInt(_checkIntervalKey, now);

      // Compare versions
      final info = await PackageInfo.fromPlatform();
      final currentVersion = info.version;

      if (_isNewer(latestVersion, currentVersion)) {
        // Check if user dismissed this version
        final dismissed = prefs.getString(_dismissedVersionKey);
        if (dismissed == latestVersion) return null;
        return latestVersion;
      }
      return null;
    } catch (e) {
      logger.debug('Update check failed (non-critical): $e');
      return null;
    }
  }

  /// Compare version strings (e.g., "2.7.0" > "2.6.4")
  static bool _isNewer(String latest, String current) {
    final latestParts = latest.split('.').map((s) => int.tryParse(s) ?? 0).toList();
    final currentParts = current.split('.').map((s) => int.tryParse(s) ?? 0).toList();

    for (int i = 0; i < 3; i++) {
      final l = i < latestParts.length ? latestParts[i] : 0;
      final c = i < currentParts.length ? currentParts[i] : 0;
      if (l > c) return true;
      if (l < c) return false;
    }
    return false;
  }

  /// Dismiss the update banner for a specific version
  static Future<void> dismissVersion(String version) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_dismissedVersionKey, version);
  }

  /// Show an update available banner in the given context
  static void showUpdateBanner(BuildContext context, String newVersion) {
    if (!context.mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentMaterialBanner()
      ..showMaterialBanner(
        MaterialBanner(
          content: Text(
            'A new version (v$newVersion) is available!',
            style: const TextStyle(fontWeight: FontWeight.w500),
          ),
          leading: const Icon(Icons.system_update, color: Color(0xFF4da6ff)),
          actions: [
            TextButton(
              onPressed: () {
                ScaffoldMessenger.of(context).hideCurrentMaterialBanner();
                dismissVersion(newVersion);
              },
              child: const Text('DISMISS'),
            ),
            FilledButton.tonal(
              onPressed: () {
                ScaffoldMessenger.of(context).hideCurrentMaterialBanner();
                launchUrl(Uri.parse(_releasesPage),
                    mode: LaunchMode.externalApplication);
              },
              child: const Text('UPDATE'),
            ),
          ],
        ),
      );
  }
}

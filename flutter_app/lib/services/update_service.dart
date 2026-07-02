import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:open_filex/open_filex.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../utils/logger_service.dart';
import '../utils/pinned_http_client.dart';

/// Result of a release lookup against GitHub.
class UpdateInfo {
  final String version; // e.g. "2.10.3"
  final String tagName; // e.g. "v2.10.3"
  final String releaseNotes; // raw markdown body
  final String? apkUrl; // direct asset URL for *.apk (Android only)
  final int? apkSize; // bytes
  final String htmlUrl; // browser fallback

  const UpdateInfo({
    required this.version,
    required this.tagName,
    required this.releaseNotes,
    required this.htmlUrl,
    this.apkUrl,
    this.apkSize,
  });
}

/// Service that checks GitHub Releases for newer app versions and (on
/// Android) downloads + launches the APK installer in-app (#207).
class UpdateService {
  static const _repoOwner = 'tv-viewer-app';
  static const _repoName = 'tv_viewer';
  static const _releasesApi =
      'https://api.github.com/repos/$_repoOwner/$_repoName/releases/latest';
  static const _releasesPage =
      'https://github.com/$_repoOwner/$_repoName/releases';
  static const _checkIntervalKey = 'last_update_check';
  static const _dismissedVersionKey = 'dismissed_update_version';
  static const _checkIntervalHours = 6;

  /// Check for updates. Returns [UpdateInfo] if a newer release exists
  /// and the user has not dismissed it. Returns null when up-to-date, when
  /// the 6-hour window has not elapsed, or on any network/parse failure.
  ///
  /// Pass [force]=true from the Settings "Check for updates" button to
  /// bypass both the 6-hour rate limit and the user-dismissed flag.
  static Future<UpdateInfo?> checkForUpdate({bool force = false}) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final now = DateTime.now().millisecondsSinceEpoch;

      if (!force) {
        final lastCheck = prefs.getInt(_checkIntervalKey) ?? 0;
        if (now - lastCheck < _checkIntervalHours * 3600 * 1000) {
          return null;
        }
      }

      final client = PinnedHttpClient.create();
      final response = await client.get(
        Uri.parse(_releasesApi),
        headers: {'Accept': 'application/vnd.github.v3+json'},
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode != 200) {
        logger.debug('Update check: HTTP ${response.statusCode}');
        return null;
      }

      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final tagName = data['tag_name'] as String? ?? '';
      final latestVersion = tagName.replaceFirst(RegExp(r'^v'), '');
      final body = data['body'] as String? ?? '';
      final htmlUrl = data['html_url'] as String? ?? _releasesPage;

      // Find the Android APK asset (if any).
      String? apkUrl;
      int? apkSize;
      final assets = data['assets'] as List<dynamic>? ?? [];
      for (final a in assets) {
        if (a is! Map) continue;
        final name = (a['name'] as String? ?? '').toLowerCase();
        if (name.endsWith('.apk')) {
          apkUrl = a['browser_download_url'] as String?;
          apkSize = a['size'] as int?;
          break;
        }
      }

      // Always record the timestamp on a successful API call so we don't
      // hammer the rate limit. (Forced checks also update it.)
      await prefs.setInt(_checkIntervalKey, now);

      final info = await PackageInfo.fromPlatform();
      final currentVersion = info.version;

      if (!_isNewer(latestVersion, currentVersion)) {
        return null;
      }

      if (!force) {
        final dismissed = prefs.getString(_dismissedVersionKey);
        if (dismissed == latestVersion) return null;
      }

      return UpdateInfo(
        version: latestVersion,
        tagName: tagName,
        releaseNotes: body,
        htmlUrl: htmlUrl,
        apkUrl: apkUrl,
        apkSize: apkSize,
      );
    } catch (e) {
      logger.debug('Update check failed (non-critical): $e');
      return null;
    }
  }

  /// Semver-ish compare ("2.10.3" > "2.10.2"). Ignores pre-release suffixes.
  static bool _isNewer(String latest, String current) {
    int n(String s) => int.tryParse(s.split('-').first) ?? 0;
    final l = latest.split('.').map(n).toList();
    final c = current.split('.').map(n).toList();
    for (int i = 0; i < 3; i++) {
      final lv = i < l.length ? l[i] : 0;
      final cv = i < c.length ? c[i] : 0;
      if (lv > cv) return true;
      if (lv < cv) return false;
    }
    return false;
  }

  /// Record that the user dismissed a specific version. Future automatic
  /// checks won't surface this version again (forced checks still will).
  static Future<void> dismissVersion(String version) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_dismissedVersionKey, version);
  }

  /// Download the APK from [info] to the app's external files dir and
  /// hand it off to the Android package installer. Returns true on success,
  /// false on any failure (caller should show an error + offer browser
  /// fallback). [onProgress] is invoked with received/total bytes (total
  /// may be 0 if the server doesn't send Content-Length).
  static Future<bool> downloadAndInstallApk(
    UpdateInfo info, {
    void Function(int received, int total)? onProgress,
  }) async {
    if (!Platform.isAndroid) return false;
    final url = info.apkUrl;
    if (url == null || url.isEmpty) return false;

    try {
      final dir = await getExternalStorageDirectory() ??
          await getApplicationCacheDirectory();
      final updates = Directory('${dir.path}/updates');
      if (!await updates.exists()) {
        await updates.create(recursive: true);
      }
      final file = File('${updates.path}/tv_viewer_${info.version}.apk');
      // If we already have a complete file from a prior attempt, skip
      // re-downloading.
      if (info.apkSize != null &&
          await file.exists() &&
          await file.length() == info.apkSize) {
        logger.info('APK already downloaded at ${file.path}');
      } else {
        final req = http.Request('GET', Uri.parse(url));
        final resp = await http.Client().send(req).timeout(
              const Duration(minutes: 5),
            );
        if (resp.statusCode != 200) {
          logger.warning('APK download HTTP ${resp.statusCode}');
          return false;
        }
        final total = resp.contentLength ?? info.apkSize ?? 0;
        final sink = file.openWrite();
        int received = 0;
        await for (final chunk in resp.stream) {
          sink.add(chunk);
          received += chunk.length;
          onProgress?.call(received, total);
        }
        await sink.flush();
        await sink.close();
        logger.info(
            'APK downloaded to ${file.path} ($received bytes, expected $total)');
      }

      // Launch the package installer. open_filex returns
      // ResultType.done on success; the system will then ask the user to
      // confirm installation.
      final result = await OpenFilex.open(
        file.path,
        type: 'application/vnd.android.package-archive',
      );
      logger.info('OpenFilex result: ${result.type} ${result.message}');
      return result.type == ResultType.done;
    } catch (e, st) {
      logger.error('downloadAndInstallApk failed', e, st);
      return false;
    }
  }

  /// Convenience: open the GitHub releases page in the browser. Fallback
  /// when in-app install isn't available or failed.
  static Future<void> openReleasesPage([String? htmlUrl]) {
    return launchUrl(
      Uri.parse(htmlUrl ?? _releasesPage),
      mode: LaunchMode.externalApplication,
    );
  }

  /// Show the rich update dialog. On Android with an APK asset, this offers
  /// the in-app install path; otherwise it falls back to the browser.
  static Future<void> showUpdateDialog(
    BuildContext context,
    UpdateInfo info,
  ) async {
    if (!context.mounted) return;
    await showDialog<void>(
      context: context,
      builder: (ctx) => _UpdateDialog(info: info),
    );
  }

  /// Show a lightweight banner that links straight to the download page.
  static void showUpdateBanner(BuildContext context, UpdateInfo info) {
    if (!context.mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentMaterialBanner()
      ..showMaterialBanner(
        MaterialBanner(
          backgroundColor:
              Theme.of(context).colorScheme.primaryContainer.withOpacity(0.35),
          content: Text(
            'A new version (v${info.version}) is available!',
            style: const TextStyle(fontWeight: FontWeight.w500),
          ),
          leading: const Icon(Icons.system_update, color: Color(0xFF4da6ff)),
          actions: [
            TextButton(
              onPressed: () {
                ScaffoldMessenger.of(context).hideCurrentMaterialBanner();
                dismissVersion(info.version);
              },
              child: const Text('LATER'),
            ),
            FilledButton.tonal(
              onPressed: () {
                ScaffoldMessenger.of(context).hideCurrentMaterialBanner();
                openReleasesPage(info.htmlUrl);
              },
              child: const Text('DOWNLOAD'),
            ),
          ],
        ),
      );
  }
}

/// Rich update dialog: shows release notes, an in-app install button
/// (Android with APK asset) and a browser fallback.
class _UpdateDialog extends StatefulWidget {
  final UpdateInfo info;
  const _UpdateDialog({required this.info});

  @override
  State<_UpdateDialog> createState() => _UpdateDialogState();
}

class _UpdateDialogState extends State<_UpdateDialog> {
  bool _downloading = false;
  int _received = 0;
  int _total = 0;
  String? _error;

  bool get _canInAppInstall =>
      Platform.isAndroid &&
      widget.info.apkUrl != null &&
      widget.info.apkUrl!.isNotEmpty;

  Future<void> _install() async {
    setState(() {
      _downloading = true;
      _error = null;
      _received = 0;
      _total = widget.info.apkSize ?? 0;
    });
    final ok = await UpdateService.downloadAndInstallApk(
      widget.info,
      onProgress: (r, t) {
        if (!mounted) return;
        setState(() {
          _received = r;
          if (t > 0) _total = t;
        });
      },
    );
    if (!mounted) return;
    if (ok) {
      // Installer launched; close the dialog so the user sees it.
      Navigator.of(context).pop();
    } else {
      setState(() {
        _downloading = false;
        _error =
            'Could not install automatically. Tap "Open in browser" to download manually.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final info = widget.info;
    final progress = (_total > 0) ? (_received / _total).clamp(0.0, 1.0) : null;
    final receivedMb = (_received / 1024 / 1024).toStringAsFixed(1);
    final totalMb = (_total / 1024 / 1024).toStringAsFixed(1);

    return AlertDialog(
      title: Row(
        children: [
          const Icon(Icons.system_update, color: Color(0xFF4da6ff)),
          const SizedBox(width: 8),
          Expanded(child: Text('Update to v${info.version}')),
        ],
      ),
      content: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 480, maxHeight: 360),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                "What's new",
                style: Theme.of(context).textTheme.titleSmall,
              ),
              const SizedBox(height: 6),
              Text(
                info.releaseNotes.isEmpty
                    ? 'No release notes provided.'
                    : info.releaseNotes,
                style: Theme.of(context).textTheme.bodySmall,
              ),
              if (_downloading) ...[
                const SizedBox(height: 16),
                LinearProgressIndicator(value: progress),
                const SizedBox(height: 6),
                Text(
                  progress == null
                      ? 'Downloading… ($receivedMb MB)'
                      : 'Downloading $receivedMb / $totalMb MB '
                          '(${(progress * 100).toStringAsFixed(0)}%)',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
              if (_error != null) ...[
                const SizedBox(height: 12),
                Text(
                  _error!,
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.error,
                    fontSize: 12,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _downloading
              ? null
              : () {
                  UpdateService.dismissVersion(info.version);
                  Navigator.of(context).pop();
                },
          child: const Text('LATER'),
        ),
        TextButton(
          onPressed: _downloading
              ? null
              : () {
                  UpdateService.openReleasesPage(info.htmlUrl);
                },
          child: const Text('OPEN IN BROWSER'),
        ),
        if (_canInAppInstall)
          FilledButton.icon(
            onPressed: _downloading ? null : _install,
            icon: const Icon(Icons.download),
            label: Text(_downloading ? 'DOWNLOADING…' : 'INSTALL'),
          ),
      ],
    );
  }
}

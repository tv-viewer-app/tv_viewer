import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/settings_service.dart';
import 'parental_settings_screen.dart';
import 'repo_management_screen.dart';

/// Settings screen with sections for stream, display, repositories,
/// privacy, parental controls, and about — matching the Windows app's
/// settings_dialog.py capabilities.
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final SettingsService _settings = SettingsService.instance;

  // Current values (loaded async)
  double _streamTimeout = 10;
  double _requestTimeout = 10;
  String _themeMode = 'system';
  String _defaultGroupBy = 'category';
  bool _analyticsEnabled = true;
  String _appVersion = '';
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    await _settings.initialize();
    final streamTimeout = await _settings.getStreamTimeout();
    final requestTimeout = await _settings.getRequestTimeout();
    final themeMode = await _settings.getThemeMode();
    final groupBy = await _settings.getDefaultGroupBy();
    final analytics = await _settings.getAnalyticsEnabled();

    String version = '';
    try {
      final info = await PackageInfo.fromPlatform();
      version = '${info.version} (${info.buildNumber})';
    } catch (_) {
      version = '2.6.4';
    }

    if (mounted) {
      setState(() {
        _streamTimeout = streamTimeout.toDouble();
        _requestTimeout = requestTimeout.toDouble();
        _themeMode = themeMode;
        _defaultGroupBy = groupBy;
        _analyticsEnabled = analytics;
        _appVersion = version;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              children: [
                // ── Stream Settings ─────────────────────────────
                _buildSectionHeader(context, 'Stream Settings', Icons.stream),
                _buildSliderTile(
                  context,
                  title: 'Stream check timeout',
                  subtitle: '${_streamTimeout.round()}s',
                  value: _streamTimeout,
                  min: 3,
                  max: 30,
                  onChanged: (v) {
                    setState(() => _streamTimeout = v);
                    _settings.setStreamTimeout(v.round());
                  },
                ),
                _buildSliderTile(
                  context,
                  title: 'Request timeout',
                  subtitle: '${_requestTimeout.round()}s',
                  value: _requestTimeout,
                  min: 3,
                  max: 30,
                  onChanged: (v) {
                    setState(() => _requestTimeout = v);
                    _settings.setRequestTimeout(v.round());
                  },
                ),
                const Divider(),

                // ── Display ─────────────────────────────────────
                _buildSectionHeader(context, 'Display', Icons.palette),
                ListTile(
                  title: const Text('Theme'),
                  subtitle: Text(_themeModeLabel(_themeMode)),
                  trailing: SegmentedButton<String>(
                    segments: const [
                      ButtonSegment(value: 'light', icon: Icon(Icons.light_mode, size: 18)),
                      ButtonSegment(value: 'system', icon: Icon(Icons.settings_suggest, size: 18)),
                      ButtonSegment(value: 'dark', icon: Icon(Icons.dark_mode, size: 18)),
                    ],
                    selected: {_themeMode},
                    onSelectionChanged: (selection) {
                      setState(() => _themeMode = selection.first);
                      _settings.setThemeMode(selection.first);
                    },
                    showSelectedIcon: false,
                    style: ButtonStyle(
                      visualDensity: VisualDensity.compact,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ),
                ),
                ListTile(
                  title: const Text('Default group by'),
                  subtitle: Text(_defaultGroupBy == 'category' ? 'Category' : 'Country'),
                  trailing: DropdownButton<String>(
                    value: _defaultGroupBy,
                    underline: const SizedBox.shrink(),
                    items: const [
                      DropdownMenuItem(value: 'category', child: Text('Category')),
                      DropdownMenuItem(value: 'country', child: Text('Country')),
                    ],
                    onChanged: (v) {
                      if (v != null) {
                        setState(() => _defaultGroupBy = v);
                        _settings.setDefaultGroupBy(v);
                      }
                    },
                  ),
                ),
                const Divider(),

                // ── Repositories ────────────────────────────────
                _buildSectionHeader(context, 'Repositories', Icons.list_alt),
                ListTile(
                  title: const Text('Manage M3U Repositories'),
                  subtitle: const Text('Add, remove, or reset channel sources'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => const RepoManagementScreen(),
                      ),
                    );
                  },
                ),
                const Divider(),

                // ── Privacy ─────────────────────────────────────
                _buildSectionHeader(context, 'Privacy', Icons.shield),
                SwitchListTile(
                  title: const Text('Analytics & Telemetry'),
                  subtitle: const Text('Help improve TV Viewer with anonymous usage data'),
                  value: _analyticsEnabled,
                  onChanged: (v) {
                    setState(() => _analyticsEnabled = v);
                    _settings.setAnalyticsEnabled(v);
                  },
                ),
                ListTile(
                  title: const Text('Privacy Policy'),
                  trailing: const Icon(Icons.open_in_new, size: 18),
                  onTap: () {
                    launchUrl(
                      Uri.parse('https://github.com/mst-ghi/tv-viewer/blob/main/PRIVACY.md'),
                      mode: LaunchMode.externalApplication,
                    );
                  },
                ),
                const Divider(),

                // ── Parental Controls ───────────────────────────
                _buildSectionHeader(context, 'Parental Controls', Icons.lock),
                ListTile(
                  title: const Text('Parental Controls'),
                  subtitle: const Text('Manage PIN, blocked categories, and age settings'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => const ParentalSettingsScreen(),
                      ),
                    );
                  },
                ),
                const Divider(),

                // ── About ───────────────────────────────────────
                _buildSectionHeader(context, 'About', Icons.info_outline),
                ListTile(
                  title: const Text('Version'),
                  subtitle: Text(_appVersion),
                ),
                ListTile(
                  title: const Text('Open Source Licenses'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    showLicensePage(
                      context: context,
                      applicationName: 'TV Viewer',
                      applicationVersion: _appVersion,
                    );
                  },
                ),
                ListTile(
                  title: const Text('GitHub'),
                  subtitle: const Text('View source code & report issues'),
                  trailing: const Icon(Icons.open_in_new, size: 18),
                  onTap: () {
                    launchUrl(
                      Uri.parse('https://github.com/mst-ghi/tv-viewer'),
                      mode: LaunchMode.externalApplication,
                    );
                  },
                ),
                const SizedBox(height: 24),
              ],
            ),
    );
  }

  Widget _buildSectionHeader(BuildContext context, String title, IconData icon) {
    final colorScheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
      child: Row(
        children: [
          Icon(icon, size: 20, color: colorScheme.primary),
          const SizedBox(width: 8),
          Text(
            title,
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  color: colorScheme.primary,
                  fontWeight: FontWeight.bold,
                ),
          ),
        ],
      ),
    );
  }

  Widget _buildSliderTile(
    BuildContext context, {
    required String title,
    required String subtitle,
    required double value,
    required double min,
    required double max,
    required ValueChanged<double> onChanged,
  }) {
    return ListTile(
      title: Text(title),
      subtitle: Row(
        children: [
          Text('${min.round()}s'),
          Expanded(
            child: Slider(
              value: value,
              min: min,
              max: max,
              divisions: (max - min).round(),
              label: '${value.round()}s',
              onChanged: onChanged,
            ),
          ),
          Text('${max.round()}s'),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.primaryContainer,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              subtitle,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: Theme.of(context).colorScheme.onPrimaryContainer,
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _themeModeLabel(String mode) {
    switch (mode) {
      case 'dark':
        return 'Dark';
      case 'light':
        return 'Light';
      default:
        return 'System default';
    }
  }
}

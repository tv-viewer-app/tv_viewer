import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:provider/provider.dart';
import '../providers/channel_provider.dart';
import '../services/onboarding_service.dart';
import '../services/feedback_service.dart';
import '../services/parental_controls_service.dart';
import 'package:package_info_plus/package_info_plus.dart' show PackageInfo;
import '../utils/logger_service.dart';
import 'package:share_plus/share_plus.dart';

class HelpScreen extends StatefulWidget {
  const HelpScreen({super.key});

  @override
  State<HelpScreen> createState() => _HelpScreenState();
}

class _HelpScreenState extends State<HelpScreen> {
  String _appVersion = 'Loading...';
  bool _isLoadingLogs = false;

  @override
  void initState() {
    super.initState();
    _loadAppVersion();
  }

  Future<void> _loadAppVersion() async {
    try {
      final packageInfo = await PackageInfo.fromPlatform();
      if (!mounted) return;
      setState(() {
        _appVersion = '${packageInfo.version} (${packageInfo.buildNumber})';
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _appVersion = '2.6.1+31'; // Fallback to hardcoded version
      });
    }
  }

  Future<void> _launchEmail() async {
    final Uri issuesUri = Uri(
      scheme: 'https',
      host: 'github.com',
      pathSegments: ['tv-viewer-app', 'tv_viewer', 'issues', 'new'],
      queryParameters: {
        'template': 'bug_report.yml',
        'title': 'Support Request (v$_appVersion)',
      },
    );

    try {
      if (await canLaunchUrl(issuesUri)) {
        await launchUrl(issuesUri, mode: LaunchMode.externalApplication);
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Could not open GitHub Issues'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Something went wrong. Please try again.'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _exportLogs() async {
    setState(() {
      _isLoadingLogs = true;
    });

    try {
      logger.info('User requested log export');
      
      // Export logs using LoggerService
      final exportedFile = await LoggerService.instance.exportLogs();
      
      if (exportedFile != null && mounted) {
        // Share the log file
        await Share.shareXFiles(
          [XFile(exportedFile.path)],
          subject: 'TV Viewer App Logs',
          text: 'Exported logs from TV Viewer app',
        );
        
        logger.info('Logs exported and shared successfully');
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Logs exported successfully'),
              backgroundColor: Colors.green,
            ),
          );
        }
      } else if (mounted) {
        logger.warning('No logs available to export');
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('No logs available to export'),
            backgroundColor: Colors.orange,
          ),
        );
      }
    } catch (e, stackTrace) {
      logger.error('Failed to export logs', e, stackTrace);
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to export logs: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoadingLogs = false;
        });
      }
    }
  }

  Future<void> _resetOnboarding() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Reset Onboarding'),
        content: const Text(
          'This will show the onboarding tooltips again on the home screen. Continue?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Reset'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await OnboardingService.resetOnboarding();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Onboarding reset. Restart the app to see tooltips.'),
            duration: Duration(seconds: 3),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Help & Support'),
        centerTitle: true,
      ),
      body: ListView(
        padding: const EdgeInsets.symmetric(vertical: 8),
        children: [
          // FAQ Section
          _buildSectionHeader('Frequently Asked Questions'),
          _buildFaqItem(
            question: 'How do I add channels to the app?',
            answer:
                'The app automatically loads channels from public IPTV sources. Tap the "Scan" button to check which channels are currently working.',
          ),
          _buildFaqItem(
            question: 'Why are some channels not working?',
            answer:
                'IPTV streams can go offline due to various reasons: server maintenance, expired links, or geographic restrictions. Use the Scan feature to check stream availability.',
          ),
          _buildFaqItem(
            question: 'How do I save my favorite channels?',
            answer:
                'Tap the heart icon next to any channel to add it to your favorites. Access favorites by tapping the heart icon in the top bar.',
          ),
          _buildFaqItem(
            question: 'Can I use an external player?',
            answer:
                'Yes! Go to Settings and enable "Use External Player". The app supports VLC, MX Player, MPV, and Just Player.',
          ),
          _buildFaqItem(
            question: 'How do I filter channels?',
            answer:
                'Use the three dropdown filters at the top: Media Type (TV/Radio), Category (News, Sports, etc.), and Country. You can also use the search bar.',
          ),
          _buildFaqItem(
            question: 'Does the app support Picture-in-Picture (PiP)?',
            answer:
                'Yes, on Android 8.0+ devices. While watching a channel, press the home button or tap the PiP icon to enable floating window mode.',
          ),
          _buildFaqItem(
            question: 'Why does the app request network permissions?',
            answer:
                'Network access is required to fetch channel lists and stream video content. No personal data is collected or transmitted.',
          ),
          _buildFaqItem(
            question: 'Can I export the channel list?',
            answer:
                'Yes, use the export function (three-dot menu on home screen) to save the channel list as an M3U file for use in other apps.',
          ),
          _buildFaqItem(
            question: 'The video is buffering constantly. What can I do?',
            answer:
                'Buffering is usually caused by slow internet or overloaded servers. Try:\n• Connecting to a faster network\n• Choosing a different channel\n• Using an external player with better buffering\n• Lowering video quality in settings',
          ),
          _buildFaqItem(
            question: 'How do I report a bug or request a feature?',
            answer:
                'Use the "Contact Support" option below to send an email. Please include app version, device model, and steps to reproduce the issue.',
          ),

          const SizedBox(height: 16),

          // Troubleshooting Section
          _buildSectionHeader('Troubleshooting'),
          _buildTroubleshootingItem(
            icon: Icons.wifi_off,
            title: 'No Internet Connection',
            description:
                'Check your WiFi or mobile data connection. The app requires internet to load channels and stream content.',
          ),
          _buildTroubleshootingItem(
            icon: Icons.play_circle_outline,
            title: 'Video Won\'t Play',
            description:
                'Try these steps:\n1. Check if the channel is marked as working (green checkmark)\n2. Run a scan to verify stream status\n3. Try playing in an external player\n4. Restart the app',
          ),
          _buildTroubleshootingItem(
            icon: Icons.slow_motion_video,
            title: 'Poor Video Quality',
            description:
                'This depends on the source stream quality. Some channels only broadcast in SD. Check the channel subtitle for resolution info.',
          ),
          _buildTroubleshootingItem(
            icon: Icons.sync_problem,
            title: 'Scan Taking Too Long',
            description:
                'Scanning 5000+ channels can take 5-10 minutes. The app checks streams in batches of 5. You can cancel anytime and work with partial results.',
          ),
          _buildTroubleshootingItem(
            icon: Icons.error_outline,
            title: 'App Crashes or Freezes',
            description:
                'Try:\n1. Clear app cache in device settings\n2. Update to the latest version\n3. Restart your device\n4. Contact support if issue persists',
          ),

          const SizedBox(height: 16),

          // Support & Info Section
          _buildSectionHeader('Support & Information'),
          ListTile(
            leading: Icon(
              Icons.feedback_outlined,
              color: Theme.of(context).colorScheme.primary,
            ),
            title: const Text('Send Feedback'),
            subtitle: const Text('Share your thoughts and suggestions'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => FeedbackService.showFeedbackDialog(context),
          ),
          ListTile(
            leading: Icon(
              Icons.star_outline,
              color: Colors.amber,
            ),
            title: const Text('Rate App'),
            subtitle: const Text('Rate us on the Play Store'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => FeedbackService.openAppStore(),
          ),
          ListTile(
            leading: Icon(
              Icons.email_outlined,
              color: Theme.of(context).colorScheme.primary,
            ),
            title: const Text('Contact Support'),
            subtitle: const Text('Send us an email'),
            trailing: const Icon(Icons.chevron_right),
            onTap: _launchEmail,
          ),
          ListTile(
            leading: Icon(
              Icons.file_download_outlined,
              color: Theme.of(context).colorScheme.primary,
            ),
            title: const Text('Export Logs'),
            subtitle: const Text('Share logs with support team'),
            trailing: _isLoadingLogs
                ? const SizedBox(
                    width: 24,
                    height: 24,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.chevron_right),
            onTap: _isLoadingLogs ? null : _exportLogs,
          ),
          ListTile(
            leading: Icon(
              Icons.refresh,
              color: Theme.of(context).colorScheme.primary,
            ),
            title: const Text('Reset Onboarding'),
            subtitle: const Text('Show welcome tooltips again'),
            trailing: const Icon(Icons.chevron_right),
            onTap: _resetOnboarding,
          ),
          ListTile(
            leading: Icon(
              Icons.info_outlined,
              color: Theme.of(context).colorScheme.primary,
            ),
            title: const Text('App Version'),
            subtitle: Text(_appVersion),
          ),

          const SizedBox(height: 16),

          // Support the Developer Section
          _buildSectionHeader('Support the Developer'),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Card(
              elevation: 2,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              color: Colors.amber.shade50,
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Text(
                      '🍺',
                      style: const TextStyle(fontSize: 40),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      'Love TV Viewer?\nBuy the developer a beer!',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: Colors.amber.shade900,
                        height: 1.4,
                      ),
                    ),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: () async {
                          try {
                            await launchUrl(
                              Uri.parse('https://ko-fi.com/tvviewerapp'),
                              mode: LaunchMode.externalApplication,
                            );
                          } catch (e) {
                            if (mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('Could not open the link'),
                                ),
                              );
                            }
                          }
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.amber.shade600,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          elevation: 2,
                          textStyle: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        child: const Text('Buy Me a Beer 🍺'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),

          const SizedBox(height: 16),

          // Request Channels Section
          Card(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: BorderSide(color: Colors.blue.shade700, width: 1),
            ),
            color: Colors.blue.shade900.withOpacity(0.3),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  const Icon(Icons.live_tv, size: 36, color: Colors.lightBlueAccent),
                  const SizedBox(height: 10),
                  const Text(
                    'Missing channels from your country?',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w500,
                      color: Colors.white70,
                    ),
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      onPressed: () async {
                        try {
                          await launchUrl(
                            Uri.parse('https://github.com/tv-viewer-app/tv_viewer/issues/new?template=channel_request.yml'),
                            mode: LaunchMode.externalApplication,
                          );
                        } catch (e) {
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('Could not open the link')),
                            );
                          }
                        }
                      },
                      icon: const Icon(Icons.add_circle_outline),
                      label: const Text('Request Channels'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.lightBlueAccent,
                        side: const BorderSide(color: Colors.lightBlueAccent),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Our bot will find and add them automatically!',
                    style: TextStyle(fontSize: 12, color: Colors.white38),
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 16),

          // Settings Section
          _buildSectionHeader('Settings'),

          const SizedBox(height: 16),

          // Legal Section
          _buildSectionHeader('Legal'),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Text(
              'TV Viewer is a free, open-source application that aggregates publicly available IPTV streams. '
              'The app does not host or provide any content. All streams are sourced from public repositories. '
              'Users are responsible for ensuring compliance with local laws and regulations.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context)
                        .colorScheme
                        .onSurface
                        .withOpacity(0.6),
                    height: 1.5,
                  ),
            ),
          ),

          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 24, 16, 12),
      child: Text(
        title,
        style: TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w600,
          color: Theme.of(context).colorScheme.primary,
          letterSpacing: 0.5,
        ),
      ),
    );
  }

  Widget _buildFaqItem({
    required String question,
    required String answer,
  }) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: Theme.of(context).colorScheme.outlineVariant,
          width: 1,
        ),
      ),
      child: ExpansionTile(
        title: Text(
          question,
          style: const TextStyle(
            fontWeight: FontWeight.w500,
            fontSize: 15,
          ),
        ),
        tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        expandedCrossAxisAlignment: CrossAxisAlignment.start,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        children: [
          Text(
            answer,
            style: TextStyle(
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.8),
              height: 1.6,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTroubleshootingItem({
    required IconData icon,
    required String title,
    required String description,
  }) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: Theme.of(context).colorScheme.outlineVariant,
          width: 1,
        ),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        leading: Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.secondaryContainer,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(
            icon,
            color: Theme.of(context).colorScheme.onSecondaryContainer,
            size: 28,
          ),
        ),
        title: Text(
          title,
          style: const TextStyle(
            fontWeight: FontWeight.w600,
            fontSize: 15,
          ),
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 8),
          child: Text(
            description,
            style: TextStyle(
              height: 1.5,
              fontSize: 13,
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.7),
            ),
          ),
        ),
      ),
    );
  }
}

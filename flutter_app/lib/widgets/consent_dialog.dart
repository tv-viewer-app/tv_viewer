import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/analytics_service.dart';

/// First-launch consent dialog for analytics and age verification.
///
/// Shows once on first app launch and stores user preferences in SharedPreferences.
/// Required for GDPR compliance and Play Store content rating.
class ConsentDialog {
  static const String _consentShownKey = 'consent_dialog_shown';
  static const String _ageVerifiedKey = 'age_verified';
  static const String _analyticsConsentKey = 'analytics_enabled';

  /// Check if consent dialog needs to be shown.
  static Future<bool> needsConsent() async {
    final prefs = await SharedPreferences.getInstance();
    return !(prefs.getBool(_consentShownKey) ?? false);
  }

  /// Show the consent dialog and return true if user accepted.
  static Future<bool> show(BuildContext context) async {
    if (!await needsConsent()) return true;

    final result = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => const _ConsentDialogWidget(),
    );

    return result ?? false;
  }
}

class _ConsentDialogWidget extends StatefulWidget {
  const _ConsentDialogWidget();

  @override
  State<_ConsentDialogWidget> createState() => _ConsentDialogWidgetState();
}

class _ConsentDialogWidgetState extends State<_ConsentDialogWidget> {
  bool _ageConfirmed = false;
  bool _analyticsOptIn = false;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Row(
        children: [
          Icon(Icons.tv, color: Theme.of(context).colorScheme.primary),
          const SizedBox(width: 8),
          const Expanded(
            child: Text(
              'Welcome to TV Viewer',
              style: TextStyle(fontSize: 18),
            ),
          ),
        ],
      ),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Content disclaimer
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.orange.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.orange.withOpacity(0.3)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.warning_amber, size: 18, color: Colors.orange.shade700),
                      const SizedBox(width: 6),
                      Text(
                        'Content Notice',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Colors.orange.shade700,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'This app streams publicly available IPTV channels. '
                    'Some content may be intended for mature audiences.',
                    style: TextStyle(fontSize: 13),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Age verification
            CheckboxListTile(
              value: _ageConfirmed,
              onChanged: (v) => setState(() => _ageConfirmed = v ?? false),
              title: const Text(
                'I confirm I am 18 years or older',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
              ),
              subtitle: const Text(
                'Required to use this app',
                style: TextStyle(fontSize: 12),
              ),
              controlAffinity: ListTileControlAffinity.leading,
              contentPadding: EdgeInsets.zero,
              dense: true,
            ),

            const Divider(),

            // Analytics opt-in
            CheckboxListTile(
              value: _analyticsOptIn,
              onChanged: (v) => setState(() => _analyticsOptIn = v ?? false),
              title: const Text(
                'Help improve TV Viewer',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
              ),
              subtitle: const Text(
                'Share anonymous usage data (no personal info, '
                'no viewing history). You can change this in Settings.',
                style: TextStyle(fontSize: 12),
              ),
              controlAffinity: ListTileControlAffinity.leading,
              contentPadding: EdgeInsets.zero,
              dense: true,
            ),

            const SizedBox(height: 8),

            // Privacy policy link
            TextButton.icon(
              onPressed: () {
                launchUrl(
                  Uri.parse('https://tv-viewer-app.github.io/tv_viewer/#privacy'),
                  mode: LaunchMode.externalApplication,
                );
              },
              icon: const Icon(Icons.privacy_tip, size: 16),
              label: const Text(
                'Privacy Policy',
                style: TextStyle(fontSize: 12),
              ),
              style: TextButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 4),
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(false),
          child: const Text('Exit'),
        ),
        FilledButton(
          onPressed: _ageConfirmed ? () => _accept(context) : null,
          child: const Text('Continue'),
        ),
      ],
    );
  }

  Future<void> _accept(BuildContext context) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(ConsentDialog._consentShownKey, true);
    await prefs.setBool(ConsentDialog._ageVerifiedKey, true);
    await prefs.setBool(ConsentDialog._analyticsConsentKey, _analyticsOptIn);

    // Update analytics opt-in
    await AnalyticsService.instance.setEnabled(_analyticsOptIn);

    if (context.mounted) {
      Navigator.of(context).pop(true);
    }
  }
}

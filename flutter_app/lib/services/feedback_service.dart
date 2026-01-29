import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

/// BL-032: Feedback service for app rating and in-app feedback
class FeedbackService {
  static const String _sessionCountKey = 'session_count';
  static const String _hasRatedKey = 'has_rated_app';
  static const String _lastPromptKey = 'last_rating_prompt';
  static const int _sessionsBeforePrompt = 5;
  static const int _daysBetweenPrompts = 30;
  
  /// Increment session count and check if we should show rating prompt
  static Future<bool> shouldShowRatingPrompt() async {
    final prefs = await SharedPreferences.getInstance();
    
    // Don't show if user already rated
    final hasRated = prefs.getBool(_hasRatedKey) ?? false;
    if (hasRated) return false;
    
    // Check last prompt date
    final lastPromptMs = prefs.getInt(_lastPromptKey) ?? 0;
    final lastPrompt = DateTime.fromMillisecondsSinceEpoch(lastPromptMs);
    final daysSinceLastPrompt = DateTime.now().difference(lastPrompt).inDays;
    
    if (daysSinceLastPrompt < _daysBetweenPrompts && lastPromptMs > 0) {
      return false;
    }
    
    // Increment session count
    final sessionCount = prefs.getInt(_sessionCountKey) ?? 0;
    await prefs.setInt(_sessionCountKey, sessionCount + 1);
    
    // Show prompt after 5 sessions
    return sessionCount >= _sessionsBeforePrompt;
  }
  
  /// Mark that rating prompt was shown
  static Future<void> markPromptShown() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_lastPromptKey, DateTime.now().millisecondsSinceEpoch);
  }
  
  /// Mark that user has rated the app
  static Future<void> markAsRated() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_hasRatedKey, true);
  }
  
  /// Open Play Store for rating (Android)
  static Future<void> openAppStore() async {
    // TODO: Replace with actual package name
    const packageName = 'com.example.tv_viewer';
    final uri = Uri.parse('https://play.google.com/store/apps/details?id=$packageName');
    
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
      await markAsRated();
    }
  }
  
  /// Show rating prompt dialog
  static Future<void> showRatingPrompt(BuildContext context) async {
    await markPromptShown();
    
    if (!context.mounted) return;
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.star, color: Colors.amber, size: 28),
            SizedBox(width: 8),
            Text('Enjoying TV Viewer?'),
          ],
        ),
        content: const Text(
          'We hope you\'re enjoying the app! Would you mind taking a moment to rate us on the Play Store? It helps us improve and reach more users.',
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              markAsRated(); // Don't ask again
            },
            child: const Text('No Thanks'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              // Ask again later (already marked as shown)
            },
            child: const Text('Later'),
          ),
          ElevatedButton.icon(
            onPressed: () {
              Navigator.pop(context);
              openAppStore();
            },
            icon: const Icon(Icons.star),
            label: const Text('Rate Now'),
          ),
        ],
      ),
    );
  }
  
  /// Show in-app feedback dialog
  static Future<void> showFeedbackDialog(BuildContext context) async {
    final feedbackController = TextEditingController();
    String feedbackType = 'Suggestion';
    
    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('Send Feedback'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Help us improve TV Viewer'),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: feedbackType,
                decoration: const InputDecoration(
                  labelText: 'Feedback Type',
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(value: 'Suggestion', child: Text('Suggestion')),
                  DropdownMenuItem(value: 'Bug Report', child: Text('Bug Report')),
                  DropdownMenuItem(value: 'Question', child: Text('Question')),
                  DropdownMenuItem(value: 'Other', child: Text('Other')),
                ],
                onChanged: (value) {
                  setState(() {
                    feedbackType = value!;
                  });
                },
              ),
              const SizedBox(height: 16),
              TextField(
                controller: feedbackController,
                maxLines: 5,
                decoration: const InputDecoration(
                  labelText: 'Your Feedback',
                  hintText: 'Tell us what you think...',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton.icon(
              onPressed: () {
                final feedback = feedbackController.text.trim();
                if (feedback.isNotEmpty) {
                  _submitFeedback(context, feedbackType, feedback);
                  Navigator.pop(context);
                }
              },
              icon: const Icon(Icons.send),
              label: const Text('Send'),
            ),
          ],
        ),
      ),
    );
  }
  
  /// Submit feedback (via email for now)
  static Future<void> _submitFeedback(
    BuildContext context,
    String type,
    String feedback,
  ) async {
    // TODO: Replace with actual support email
    final emailUri = Uri(
      scheme: 'mailto',
      path: 'support@tvviewer.com',
      query: 'subject=$type - TV Viewer Feedback&body=${Uri.encodeComponent(feedback)}',
    );
    
    if (await canLaunchUrl(emailUri)) {
      await launchUrl(emailUri);
      
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Thank you for your feedback!'),
            duration: Duration(seconds: 2),
          ),
        );
      }
    } else {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Could not open email app'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }
  
  /// Reset session counter (for testing)
  static Future<void> resetSessionCount() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_sessionCountKey);
    await prefs.remove(_hasRatedKey);
    await prefs.remove(_lastPromptKey);
  }
}

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import 'analytics_service.dart';

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
    const packageName = 'com.tvviewer.app';
    final uri = Uri.parse('https://play.google.com/store/apps/details?id=$packageName');
    
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
      await markAsRated();
      
      // Track rating event
      await AnalyticsService.instance.trackEvent('app_rated', {
        'source': 'manual',
        'timestamp': DateTime.now().toIso8601String(),
      });
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
            onPressed: () async {
              Navigator.pop(context);
              await openAppStore();
              
              // Track that user clicked "Rate Now" from prompt
              await AnalyticsService.instance.trackEvent('rating_prompt_accepted', {
                'prompt_type': 'auto',
              });
            },
            icon: const Icon(Icons.star),
            label: const Text('Rate Now'),
          ),
        ],
      ),
    );
  }
  
  /// Show in-app feedback dialog with rating
  static Future<void> showFeedbackDialog(BuildContext context) async {
    final feedbackController = TextEditingController();
    String feedbackType = 'General';
    int rating = 5;
    
    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.feedback, size: 24),
              SizedBox(width: 8),
              Text('Send Feedback'),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Help us improve TV Viewer'),
                const SizedBox(height: 20),
                
                // Rating stars
                const Text(
                  'How would you rate your experience?',
                  style: TextStyle(fontWeight: FontWeight.w500, fontSize: 13),
                ),
                const SizedBox(height: 8),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: List.generate(5, (index) {
                    final starValue = index + 1;
                    return IconButton(
                      icon: Icon(
                        starValue <= rating ? Icons.star : Icons.star_border,
                        color: Colors.amber,
                        size: 36,
                      ),
                      onPressed: () {
                        setState(() {
                          rating = starValue;
                        });
                      },
                    );
                  }),
                ),
                const SizedBox(height: 16),
                
                // Category dropdown
                DropdownButtonFormField<String>(
                  value: feedbackType,
                  decoration: const InputDecoration(
                    labelText: 'Category',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.category),
                  ),
                  items: const [
                    DropdownMenuItem(value: 'General', child: Text('General Feedback')),
                    DropdownMenuItem(value: 'Bug', child: Text('Bug Report')),
                    DropdownMenuItem(value: 'Feature Request', child: Text('Feature Request')),
                  ],
                  onChanged: (value) {
                    setState(() {
                      feedbackType = value!;
                    });
                  },
                ),
                const SizedBox(height: 16),
                
                // Feedback text field
                TextField(
                  controller: feedbackController,
                  maxLines: 5,
                  maxLength: 500,
                  decoration: const InputDecoration(
                    labelText: 'Your Feedback',
                    hintText: 'Tell us what you think...',
                    border: OutlineInputBorder(),
                    alignLabelWithHint: true,
                  ),
                ),
              ],
            ),
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
                  _submitFeedback(context, feedbackType, feedback, rating);
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
  
  /// Submit feedback (via email + analytics)
  static Future<void> _submitFeedback(
    BuildContext context,
    String type,
    String feedback,
    int rating,
  ) async {
    // Track feedback submission in analytics (backend integration)
    try {
      await AnalyticsService.instance.trackEvent('feedback_submitted', {
        'category': type,
        'rating': rating,
        'has_message': feedback.isNotEmpty,
        'message_length': feedback.length,
        'timestamp': DateTime.now().toIso8601String(),
      });
    } catch (e) {
      // Silently fail analytics - don't block feedback submission
    }
    
    // Compose email with rating info
    final emailBody = '''
Rating: ${'⭐' * rating} ($rating/5)
Category: $type

Feedback:
$feedback

---
Sent via TV Viewer Feedback System
''';
    
    final issuesUri = Uri(
      scheme: 'https',
      host: 'github.com',
      pathSegments: ['tv-viewer-app', 'tv_viewer', 'issues', 'new'],
      queryParameters: {
        'template': 'feedback.yml',
        'title': '[$type] TV Viewer Feedback',
      },
    );
    
    bool feedbackOpened = false;
    if (await canLaunchUrl(issuesUri)) {
      await launchUrl(issuesUri, mode: LaunchMode.externalApplication);
      feedbackOpened = true;
    }
    
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(feedbackOpened 
              ? 'Thank you for your feedback!' 
              : 'Could not open GitHub Issues. Visit https://github.com/tv-viewer-app/tv_viewer/issues'),
          backgroundColor: feedbackOpened ? null : Colors.orange,
          duration: const Duration(seconds: 3),
        ),
      );
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

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../widgets/star_rating.dart';
import '../services/feedback_service.dart';

/// Screen for collecting user feedback with star rating.
///
/// This screen allows users to:
/// - Rate the app with 1-5 stars
/// - Provide text feedback
/// - Optionally include device information
/// - Submit feedback via GitHub issues
class FeedbackScreen extends StatefulWidget {
  const FeedbackScreen({Key? key}) : super(key: key);

  @override
  State<FeedbackScreen> createState() => _FeedbackScreenState();
}

class _FeedbackScreenState extends State<FeedbackScreen> {
  final _feedbackController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  int _rating = 0;
  bool _includeDeviceInfo = false;
  bool _isSubmitting = false;

  @override
  void dispose() {
    _feedbackController.dispose();
    super.dispose();
  }

  Future<void> _submitFeedback() async {
    // Validate form
    if (_rating == 0) {
      _showSnackBar(
        'Please select a rating',
        isError: true,
      );
      return;
    }

    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final result = await FeedbackService.submitFeedbackWithRating(
        rating: _rating,
        feedbackText: _feedbackController.text.trim(),
        includeDeviceInfo: _includeDeviceInfo,
      );

      if (!mounted) return;

      if (result.isSuccess) {
        _showSnackBar(result.message);
        // Small delay to show the snackbar before popping
        await Future.delayed(const Duration(milliseconds: 500));
        if (mounted) {
          Navigator.of(context).pop();
        }
      } else if (result.isCopiedToClipboard) {
        _showDialog(
          title: 'Feedback Copied',
          content: result.message,
          githubUrl: result.githubUrl,
        );
      } else {
        _showSnackBar(result.message, isError: true);
      }
    } catch (e) {
      if (mounted) {
        _showSnackBar(
          'An error occurred: ${e.toString()}',
          isError: true,
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  void _showSnackBar(String message, {bool isError = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError
            ? Theme.of(context).colorScheme.error
            : Theme.of(context).colorScheme.primary,
        behavior: SnackBarBehavior.floating,
        duration: Duration(seconds: isError ? 4 : 2),
      ),
    );
  }

  void _showDialog({
    required String title,
    required String content,
    String? githubUrl,
  }) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(content),
            if (githubUrl != null) ...[
              const SizedBox(height: 16),
              Text(
                'GitHub URL:',
                style: Theme.of(context).textTheme.labelSmall,
              ),
              const SizedBox(height: 4),
              SelectableText(
                githubUrl,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.primary,
                    ),
              ),
            ],
          ],
        ),
        actions: [
          if (githubUrl != null)
            TextButton.icon(
              onPressed: () {
                Clipboard.setData(ClipboardData(text: githubUrl));
                Navigator.of(context).pop();
                _showSnackBar('URL copied to clipboard');
              },
              icon: const Icon(Icons.copy),
              label: const Text('Copy URL'),
            ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  String _getRatingDescription() {
    switch (_rating) {
      case 1:
        return 'Poor';
      case 2:
        return 'Fair';
      case 3:
        return 'Good';
      case 4:
        return 'Very Good';
      case 5:
        return 'Excellent';
      default:
        return 'Tap a star to rate';
    }
  }

  Color _getRatingColor() {
    final theme = Theme.of(context).colorScheme;
    switch (_rating) {
      case 1:
      case 2:
        return theme.error;
      case 3:
        return Colors.orange;
      case 4:
      case 5:
        return theme.primary;
      default:
        return theme.onSurfaceVariant;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Send Feedback'),
        centerTitle: true,
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            // Header
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    Icon(
                      Icons.feedback_outlined,
                      size: 48,
                      color: colorScheme.primary,
                    ),
                    const SizedBox(height: 12),
                    Text(
                      'We value your feedback!',
                      style: theme.textTheme.titleLarge,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Help us improve by sharing your experience',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 24),

            // Rating Section
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'How would you rate this app?',
                      style: theme.textTheme.titleMedium,
                    ),
                    const SizedBox(height: 16),
                    Center(
                      child: StarRating(
                        rating: _rating,
                        size: 48,
                        onRatingChanged: (rating) {
                          setState(() => _rating = rating);
                          // Haptic feedback
                          HapticFeedback.selectionClick();
                        },
                      ),
                    ),
                    const SizedBox(height: 12),
                    Center(
                      child: AnimatedSwitcher(
                        duration: const Duration(milliseconds: 200),
                        child: Text(
                          _getRatingDescription(),
                          key: ValueKey<int>(_rating),
                          style: theme.textTheme.titleSmall?.copyWith(
                            color: _getRatingColor(),
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Feedback Text Section
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Tell us more (optional)',
                      style: theme.textTheme.titleMedium,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _feedbackController,
                      decoration: InputDecoration(
                        hintText: 'What did you like? What could be better?',
                        border: const OutlineInputBorder(),
                        filled: true,
                        fillColor: colorScheme.surfaceVariant.withOpacity(0.3),
                        contentPadding: const EdgeInsets.all(16),
                      ),
                      maxLines: 6,
                      maxLength: 1000,
                      textCapitalization: TextCapitalization.sentences,
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Device Info Section
            Card(
              child: CheckboxListTile(
                title: const Text('Include device information'),
                subtitle: Text(
                  'Helps us diagnose technical issues (anonymous)',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                value: _includeDeviceInfo,
                onChanged: (value) {
                  setState(() => _includeDeviceInfo = value ?? false);
                },
                secondary: Icon(
                  Icons.phone_android,
                  color: colorScheme.primary,
                ),
              ),
            ),

            const SizedBox(height: 24),

            // Submit Button
            FilledButton.icon(
              onPressed: _isSubmitting ? null : _submitFeedback,
              icon: _isSubmitting
                  ? SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: colorScheme.onPrimary,
                      ),
                    )
                  : const Icon(Icons.send),
              label: Text(_isSubmitting ? 'Submitting...' : 'Submit Feedback'),
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.all(16),
              ),
            ),

            const SizedBox(height: 16),

            // Privacy Note
            Center(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16.0),
                child: Text(
                  'Your feedback will be submitted as a GitHub issue. '
                  'No personal information is collected without your consent.',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                  textAlign: TextAlign.center,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

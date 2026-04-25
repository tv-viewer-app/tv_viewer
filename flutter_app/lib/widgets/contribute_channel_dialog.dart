import 'package:flutter/material.dart';
import '../services/shared_db_service.dart';

/// Modal dialog for users to contribute new channel discoveries.
///
/// Collects channel name, stream URL, category, and optional country,
/// then submits to the shared database via [SharedDbService].
class ContributeChannelDialog extends StatefulWidget {
  const ContributeChannelDialog({super.key});

  /// Convenience method to show the dialog from anywhere in the app.
  static Future<void> show(BuildContext context) {
    return showDialog<void>(
      context: context,
      builder: (context) => const ContributeChannelDialog(),
    );
  }

  @override
  State<ContributeChannelDialog> createState() =>
      _ContributeChannelDialogState();
}

class _ContributeChannelDialogState extends State<ContributeChannelDialog> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _urlController = TextEditingController();
  final _countryController = TextEditingController();

  bool _isSubmitting = false;

  String _selectedCategory = 'General';

  static const List<String> _categories = [
    'News',
    'Sports',
    'Entertainment',
    'Music',
    'Kids',
    'Documentary',
    'Movies',
    'Education',
    'Religious',
    'Weather',
    'General',
    'Other',
  ];

  @override
  void dispose() {
    _nameController.dispose();
    _urlController.dispose();
    _countryController.dispose();
    super.dispose();
  }

  String? _validateName(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Channel name is required';
    }
    return null;
  }

  String? _validateUrl(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Stream URL is required';
    }
    final uri = Uri.tryParse(value.trim());
    if (uri == null ||
        !uri.hasScheme ||
        !(uri.scheme == 'http' || uri.scheme == 'https')) {
      return 'Enter a valid http or https URL';
    }
    return null;
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isSubmitting = true);

    try {
      final channelData = <String, dynamic>{
        'name': _nameController.text.trim(),
        'url': _urlController.text.trim(),
        'category': _selectedCategory,
        'country': _countryController.text.trim().isEmpty
            ? 'Unknown'
            : _countryController.text.trim(),
        'source': 'user-contribution',
      };

      final sharedDb = SharedDbService();
      final success = await sharedDb.contributeChannel(channelData);

      if (!mounted) return;

      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Channel contributed! Thanks for helping! 🎉'),
            behavior: SnackBarBehavior.floating,
          ),
        );
        Navigator.of(context).pop();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Failed to contribute channel. Please try again.'),
            behavior: SnackBarBehavior.floating,
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error: $e'),
          behavior: SnackBarBehavior.floating,
          backgroundColor: Theme.of(context).colorScheme.error,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AlertDialog(
      title: Row(
        children: [
          Icon(Icons.add_circle_outline, color: theme.colorScheme.primary),
          const SizedBox(width: 8),
          const Expanded(
            child: Text(
              'Contribute a Channel',
              style: TextStyle(fontSize: 18),
            ),
          ),
        ],
      ),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Channel Name
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Channel Name',
                  hintText: 'e.g. BBC World News',
                  prefixIcon: Icon(Icons.tv),
                  border: OutlineInputBorder(),
                ),
                validator: _validateName,
                textInputAction: TextInputAction.next,
                enabled: !_isSubmitting,
              ),
              const SizedBox(height: 16),

              // Stream URL
              TextFormField(
                controller: _urlController,
                decoration: const InputDecoration(
                  labelText: 'Stream URL',
                  hintText: 'https://example.com/stream.m3u8',
                  prefixIcon: Icon(Icons.link),
                  border: OutlineInputBorder(),
                ),
                validator: _validateUrl,
                keyboardType: TextInputType.url,
                textInputAction: TextInputAction.next,
                enabled: !_isSubmitting,
              ),
              const SizedBox(height: 16),

              // Category dropdown
              DropdownButtonFormField<String>(
                value: _selectedCategory,
                decoration: const InputDecoration(
                  labelText: 'Category',
                  prefixIcon: Icon(Icons.category),
                  border: OutlineInputBorder(),
                ),
                items: _categories
                    .map((cat) => DropdownMenuItem(
                          value: cat,
                          child: Text(cat),
                        ))
                    .toList(),
                onChanged: _isSubmitting
                    ? null
                    : (value) {
                        if (value != null) {
                          setState(() => _selectedCategory = value);
                        }
                      },
              ),
              const SizedBox(height: 16),

              // Country (optional)
              TextFormField(
                controller: _countryController,
                decoration: const InputDecoration(
                  labelText: 'Country (optional)',
                  hintText: 'e.g. United Kingdom',
                  prefixIcon: Icon(Icons.public),
                  border: OutlineInputBorder(),
                ),
                textInputAction: TextInputAction.done,
                enabled: !_isSubmitting,
                onFieldSubmitted: (_) => _submit(),
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isSubmitting ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        FilledButton.icon(
          onPressed: _isSubmitting ? null : _submit,
          icon: _isSubmitting
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                )
              : const Icon(Icons.send),
          label: const Text('Submit'),
        ),
      ],
    );
  }
}

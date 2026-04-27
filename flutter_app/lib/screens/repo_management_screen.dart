import 'package:flutter/material.dart';
import '../services/settings_service.dart';
import '../services/m3u_service.dart';

/// Screen for managing M3U repository URLs.
///
/// Allows users to add, remove, and reset channel source URLs.
/// Stores custom repos in SharedPreferences via SettingsService.
class RepoManagementScreen extends StatefulWidget {
  const RepoManagementScreen({super.key});

  @override
  State<RepoManagementScreen> createState() => _RepoManagementScreenState();
}

class _RepoManagementScreenState extends State<RepoManagementScreen> {
  final SettingsService _settings = SettingsService.instance;
  List<String> _repos = [];
  bool _isLoading = true;
  bool _isCustom = false;

  @override
  void initState() {
    super.initState();
    _loadRepos();
  }

  Future<void> _loadRepos() async {
    await _settings.initialize();
    final custom = await _settings.getCustomRepos();
    if (mounted) {
      setState(() {
        if (custom != null) {
          _repos = List<String>.from(custom);
          _isCustom = true;
        } else {
          _repos = List<String>.from(M3UService.defaultRepositories);
          _isCustom = false;
        }
        _isLoading = false;
      });
    }
  }

  Future<void> _saveRepos() async {
    await _settings.setCustomRepos(_repos);
    setState(() => _isCustom = true);
  }

  Future<void> _resetToDefaults() async {
    await _settings.clearCustomRepos();
    if (mounted) {
      setState(() {
        _repos = List<String>.from(M3UService.defaultRepositories);
        _isCustom = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Repositories reset to defaults')),
      );
    }
  }

  Future<void> _addRepo() async {
    final controller = TextEditingController();
    final result = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Repository'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            hintText: 'https://example.com/playlist.m3u',
            labelText: 'Repository URL',
            prefixIcon: Icon(Icons.link),
          ),
          keyboardType: TextInputType.url,
          autofocus: true,
          onSubmitted: (value) => Navigator.of(context).pop(value),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(controller.text),
            child: const Text('Add'),
          ),
        ],
      ),
    );

    if (result != null && result.trim().isNotEmpty) {
      final url = result.trim();
      final validationError = _validateUrl(url);
      if (validationError != null) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(validationError)),
          );
        }
        return;
      }
      if (_repos.contains(url)) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Repository already exists')),
          );
        }
        return;
      }
      setState(() => _repos.add(url));
      await _saveRepos();
    }
  }

  /// Validate URL format. Returns error message or null if valid.
  String? _validateUrl(String url) {
    final uri = Uri.tryParse(url);
    if (uri == null || !uri.hasScheme) {
      return 'Invalid URL format';
    }
    if (uri.scheme != 'http' && uri.scheme != 'https') {
      return 'URL must use http or https';
    }
    if (uri.host.isEmpty) {
      return 'URL must have a valid host';
    }
    return null; // Valid
  }

  Future<void> _removeRepo(int index) async {
    final url = _repos[index];
    setState(() => _repos.removeAt(index));
    await _saveRepos();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Removed repository'),
          action: SnackBarAction(
            label: 'Undo',
            onPressed: () {
              setState(() => _repos.insert(index, url));
              _saveRepos();
            },
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Manage Repositories'),
        actions: [
          PopupMenuButton<String>(
            onSelected: (value) {
              if (value == 'reset') {
                _resetToDefaults();
              }
            },
            itemBuilder: (_) => [
              const PopupMenuItem(
                value: 'reset',
                child: Row(
                  children: [
                    Icon(Icons.restore),
                    SizedBox(width: 8),
                    Text('Reset to Defaults'),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                // Status banner
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  color: _isCustom
                      ? colorScheme.tertiaryContainer
                      : colorScheme.surfaceContainerHighest,
                  child: Row(
                    children: [
                      Icon(
                        _isCustom ? Icons.edit : Icons.check_circle,
                        size: 16,
                        color: _isCustom
                            ? colorScheme.onTertiaryContainer
                            : colorScheme.onSurfaceVariant,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        _isCustom
                            ? 'Custom repositories (${_repos.length})'
                            : 'Default repositories (${_repos.length})',
                        style: TextStyle(
                          fontSize: 13,
                          color: _isCustom
                              ? colorScheme.onTertiaryContainer
                              : colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
                // Repo list
                Expanded(
                  child: _repos.isEmpty
                      ? Center(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.playlist_remove, size: 48, color: colorScheme.outline),
                              const SizedBox(height: 8),
                              Text(
                                'No repositories',
                                style: TextStyle(color: colorScheme.outline),
                              ),
                              const SizedBox(height: 16),
                              FilledButton.icon(
                                onPressed: _resetToDefaults,
                                icon: const Icon(Icons.restore),
                                label: const Text('Reset to Defaults'),
                              ),
                            ],
                          ),
                        )
                      : ListView.builder(
                          itemCount: _repos.length,
                          itemBuilder: (context, index) {
                            final url = _repos[index];
                            final isDefault = M3UService.defaultRepositories.contains(url);
                            return Dismissible(
                              key: ValueKey(url),
                              direction: DismissDirection.endToStart,
                              background: Container(
                                alignment: Alignment.centerRight,
                                padding: const EdgeInsets.only(right: 20),
                                color: Colors.red.shade700,
                                child: const Icon(Icons.delete, color: Colors.white),
                              ),
                              onDismissed: (_) => _removeRepo(index),
                              child: ListTile(
                                leading: Icon(
                                  isDefault ? Icons.cloud : Icons.link,
                                  color: isDefault
                                      ? colorScheme.primary
                                      : colorScheme.tertiary,
                                ),
                                title: Text(
                                  _friendlyName(url),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(fontWeight: FontWeight.w500),
                                ),
                                subtitle: Text(
                                  url,
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                  style: Theme.of(context).textTheme.bodySmall,
                                ),
                                trailing: IconButton(
                                  icon: const Icon(Icons.delete_outline, size: 20),
                                  onPressed: () => _removeRepo(index),
                                ),
                              ),
                            );
                          },
                        ),
                ),
              ],
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: _addRepo,
        tooltip: 'Add Repository',
        child: const Icon(Icons.add),
      ),
    );
  }

  /// Extract a friendly display name from a URL.
  String _friendlyName(String url) {
    try {
      final uri = Uri.parse(url);
      final segments = uri.pathSegments.where((s) => s.isNotEmpty).toList();
      if (segments.isNotEmpty) {
        return segments.last;
      }
      return uri.host;
    } catch (_) {
      return url;
    }
  }
}

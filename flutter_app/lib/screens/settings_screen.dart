import 'package:flutter/material.dart';
import '../services/repository_service.dart';
import '../utils/logger_service.dart';

/// Settings screen for managing M3U repository sources
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  List<String> _repositories = [];
  bool _isLoading = true;
  final TextEditingController _urlController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadRepositories();
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _loadRepositories() async {
    setState(() => _isLoading = true);
    
    try {
      final repos = await RepositoryService.loadRepositories();
      setState(() {
        _repositories = repos;
        _isLoading = false;
      });
    } catch (e) {
      logger.error('Error loading repositories in settings', e);
      setState(() => _isLoading = false);
    }
  }

  Future<void> _addRepository() async {
    final url = _urlController.text.trim();
    
    if (url.isEmpty) {
      _showMessage('Please enter a URL');
      return;
    }
    
    final success = await RepositoryService.addRepository(url);
    
    if (success) {
      _urlController.clear();
      await _loadRepositories();
      _showMessage('Repository added successfully');
    } else {
      _showMessage('Failed to add repository (may already exist or invalid URL)');
    }
  }

  Future<void> _removeRepository(String url) async {
    final success = await RepositoryService.removeRepository(url);
    
    if (success) {
      await _loadRepositories();
      _showMessage('Repository removed');
    } else {
      _showMessage('Cannot remove last repository');
    }
  }

  Future<void> _editRepository(String oldUrl) async {
    final controller = TextEditingController(text: oldUrl);
    
    final newUrl = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Edit Repository'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            labelText: 'Repository URL',
            hintText: 'https://example.com/playlist.m3u',
          ),
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, controller.text.trim()),
            child: const Text('Save'),
          ),
        ],
      ),
    );
    
    if (newUrl != null && newUrl.isNotEmpty && newUrl != oldUrl) {
      final success = await RepositoryService.updateRepository(oldUrl, newUrl);
      
      if (success) {
        await _loadRepositories();
        _showMessage('Repository updated');
      } else {
        _showMessage('Failed to update repository (invalid URL)');
      }
    }
  }

  Future<void> _resetToDefaults() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Reset to Defaults'),
        content: const Text(
          'This will remove all custom repositories and restore the default sources. Continue?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Reset'),
          ),
        ],
      ),
    );
    
    if (confirmed == true) {
      final success = await RepositoryService.resetToDefaults();
      
      if (success) {
        await _loadRepositories();
        _showMessage('Reset to default repositories');
      } else {
        _showMessage('Failed to reset repositories');
      }
    }
  }

  Future<void> _addFallbacks() async {
    final success = await RepositoryService.addFallbacks();
    
    if (success) {
      await _loadRepositories();
      _showMessage('Fallback repositories added');
    } else {
      _showMessage('Fallback repositories already added');
    }
  }

  void _showMessage(String message) {
    if (!mounted) return;
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Channel Sources'),
        actions: [
          PopupMenuButton<String>(
            onSelected: (value) {
              if (value == 'reset') {
                _resetToDefaults();
              } else if (value == 'add_fallbacks') {
                _addFallbacks();
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'add_fallbacks',
                child: Row(
                  children: [
                    Icon(Icons.add_circle_outline),
                    SizedBox(width: 8),
                    Text('Add Fallback Sources'),
                  ],
                ),
              ),
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
                // Info card
                Card(
                  margin: const EdgeInsets.all(16),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(
                              Icons.info_outline,
                              color: Theme.of(context).colorScheme.primary,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'M3U Repository Sources',
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'These are the sources used to fetch channel lists. '
                          'You can add custom M3U playlist URLs or use the defaults.',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                ),
                
                // Add repository section
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _urlController,
                          decoration: const InputDecoration(
                            labelText: 'Add Repository URL',
                            hintText: 'https://example.com/playlist.m3u',
                            prefixIcon: Icon(Icons.link),
                            border: OutlineInputBorder(),
                          ),
                          onSubmitted: (_) => _addRepository(),
                        ),
                      ),
                      const SizedBox(width: 8),
                      IconButton.filled(
                        onPressed: _addRepository,
                        icon: const Icon(Icons.add),
                        tooltip: 'Add Repository',
                      ),
                    ],
                  ),
                ),
                
                const SizedBox(height: 16),
                
                // Repository count
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      '${_repositories.length} ${_repositories.length == 1 ? 'repository' : 'repositories'}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
                ),
                
                const SizedBox(height: 8),
                
                // Repository list
                Expanded(
                  child: _repositories.isEmpty
                      ? Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Icon(Icons.source, size: 64, color: Colors.grey),
                              const SizedBox(height: 16),
                              const Text('No repositories configured'),
                              const SizedBox(height: 16),
                              ElevatedButton.icon(
                                onPressed: _resetToDefaults,
                                icon: const Icon(Icons.restore),
                                label: const Text('Load Defaults'),
                              ),
                            ],
                          ),
                        )
                      : ListView.builder(
                          itemCount: _repositories.length,
                          itemBuilder: (context, index) {
                            final url = _repositories[index];
                            final isDefault = RepositoryService.defaultRepositories.contains(url);
                            
                            return Card(
                              margin: const EdgeInsets.symmetric(
                                horizontal: 16,
                                vertical: 4,
                              ),
                              child: ListTile(
                                leading: Icon(
                                  isDefault ? Icons.star : Icons.link,
                                  color: isDefault ? Colors.amber : null,
                                ),
                                title: Text(
                                  url,
                                  style: const TextStyle(fontSize: 13),
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                subtitle: isDefault
                                    ? const Text(
                                        'Default repository',
                                        style: TextStyle(fontSize: 11),
                                      )
                                    : null,
                                trailing: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    IconButton(
                                      icon: const Icon(Icons.edit, size: 20),
                                      onPressed: () => _editRepository(url),
                                      tooltip: 'Edit',
                                    ),
                                    IconButton(
                                      icon: const Icon(Icons.delete, size: 20),
                                      onPressed: _repositories.length > 1
                                          ? () => _removeRepository(url)
                                          : null,
                                      tooltip: _repositories.length > 1
                                          ? 'Remove'
                                          : 'Cannot remove last repository',
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                ),
              ],
            ),
    );
  }
}

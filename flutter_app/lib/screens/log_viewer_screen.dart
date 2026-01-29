import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:share_plus/share_plus.dart';
import '../utils/logger_service.dart';

/// Screen to view and manage application logs
class LogViewerScreen extends StatefulWidget {
  const LogViewerScreen({super.key});

  @override
  State<LogViewerScreen> createState() => _LogViewerScreenState();
}

class _LogViewerScreenState extends State<LogViewerScreen> {
  String _logs = '';
  bool _isLoading = true;
  String _logSize = '';
  int _logFileCount = 0;
  LogLevel _selectedLevel = LogLevel.debug;
  
  @override
  void initState() {
    super.initState();
    _loadLogs();
  }
  
  Future<void> _loadLogs() async {
    setState(() => _isLoading = true);
    
    try {
      final logs = await logger.getLogsAsString(maxLines: 500);
      final size = await logger.getFormattedLogSize();
      final files = await logger.getAllLogFiles();
      
      setState(() {
        _logs = logs;
        _logSize = size;
        _logFileCount = files.length;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _logs = 'Error loading logs: $e';
        _isLoading = false;
      });
    }
  }
  
  Future<void> _exportLogs() async {
    try {
      final file = await logger.exportLogs();
      
      if (file != null) {
        // Share the exported file
        await Share.shareXFiles(
          [XFile(file.path)],
          subject: 'TV Viewer Logs',
          text: 'Application logs for troubleshooting',
        );
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Logs exported successfully')),
          );
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('No logs to export')),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Export failed: $e')),
        );
      }
    }
  }
  
  Future<void> _copyLogs() async {
    await Clipboard.setData(ClipboardData(text: _logs));
    
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Logs copied to clipboard')),
      );
    }
  }
  
  Future<void> _clearLogs() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Clear Logs'),
        content: const Text('Are you sure you want to delete all log files?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Clear', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
    
    if (confirmed == true) {
      await logger.clearLogs();
      await _loadLogs();
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('All logs cleared')),
        );
      }
    }
  }
  
  Future<void> _changeLogLevel(LogLevel level) async {
    logger.setMinLogLevel(level);
    setState(() => _selectedLevel = level);
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Log level changed to: ${level.label}')),
    );
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Application Logs'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
            onPressed: _loadLogs,
          ),
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert),
            onSelected: (value) {
              switch (value) {
                case 'export':
                  _exportLogs();
                  break;
                case 'copy':
                  _copyLogs();
                  break;
                case 'clear':
                  _clearLogs();
                  break;
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'export',
                child: Row(
                  children: [
                    Icon(Icons.share),
                    SizedBox(width: 8),
                    Text('Export Logs'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'copy',
                child: Row(
                  children: [
                    Icon(Icons.copy),
                    SizedBox(width: 8),
                    Text('Copy to Clipboard'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'clear',
                child: Row(
                  children: [
                    Icon(Icons.delete, color: Colors.red),
                    SizedBox(width: 8),
                    Text('Clear All Logs', style: TextStyle(color: Colors.red)),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          // Log info card
          Card(
            margin: const EdgeInsets.all(8),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildInfoItem(
                        Icons.description,
                        'Files',
                        '$_logFileCount',
                      ),
                      _buildInfoItem(
                        Icons.storage,
                        'Size',
                        _logSize,
                      ),
                      _buildInfoItem(
                        Icons.text_snippet,
                        'Lines',
                        '${_logs.split('\n').length}',
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  // Log level selector
                  Row(
                    children: [
                      const Text('Log Level: '),
                      const SizedBox(width: 8),
                      Expanded(
                        child: SegmentedButton<LogLevel>(
                          segments: const [
                            ButtonSegment(
                              value: LogLevel.debug,
                              label: Text('Debug'),
                              icon: Icon(Icons.bug_report, size: 16),
                            ),
                            ButtonSegment(
                              value: LogLevel.info,
                              label: Text('Info'),
                              icon: Icon(Icons.info, size: 16),
                            ),
                            ButtonSegment(
                              value: LogLevel.warning,
                              label: Text('Warn'),
                              icon: Icon(Icons.warning, size: 16),
                            ),
                            ButtonSegment(
                              value: LogLevel.error,
                              label: Text('Error'),
                              icon: Icon(Icons.error, size: 16),
                            ),
                          ],
                          selected: {_selectedLevel},
                          onSelectionChanged: (Set<LogLevel> newSelection) {
                            _changeLogLevel(newSelection.first);
                          },
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          
          // Logs viewer
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : Container(
                    margin: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.black87,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.grey.shade700),
                    ),
                    child: _logs.isEmpty
                        ? const Center(
                            child: Text(
                              'No logs available',
                              style: TextStyle(color: Colors.white70),
                            ),
                          )
                        : SingleChildScrollView(
                            padding: const EdgeInsets.all(12),
                            child: SelectableText(
                              _logs,
                              style: const TextStyle(
                                fontFamily: 'monospace',
                                fontSize: 11,
                                color: Colors.greenAccent,
                                height: 1.4,
                              ),
                            ),
                          ),
                  ),
          ),
          
          // Action buttons
          Padding(
            padding: const EdgeInsets.all(8),
            child: Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _exportLogs,
                    icon: const Icon(Icons.share),
                    label: const Text('Export'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _copyLogs,
                    icon: const Icon(Icons.copy),
                    label: const Text('Copy'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _clearLogs,
                    icon: const Icon(Icons.delete),
                    label: const Text('Clear'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.red,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildInfoItem(IconData icon, String label, String value) {
    return Column(
      children: [
        Icon(icon, size: 24, color: Theme.of(context).colorScheme.primary),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey.shade600,
          ),
        ),
      ],
    );
  }
}

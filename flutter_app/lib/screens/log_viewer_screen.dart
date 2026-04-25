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
    if (!mounted) return;
    setState(() => _isLoading = true);
    
    try {
      final logs = await logger.getLogsAsString(maxLines: 500);
      final size = await logger.getFormattedLogSize();
      final files = await logger.getAllLogFiles();
      
      if (!mounted) return;
      setState(() {
        _logs = logs;
        _logSize = size;
        _logFileCount = files.length;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
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
    final isLandscape = MediaQuery.of(context).orientation == Orientation.landscape;
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
            margin: EdgeInsets.all(isLandscape ? 8 : 12),
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: BorderSide(
                color: Theme.of(context).colorScheme.outlineVariant,
                width: 1,
              ),
            ),
            child: Padding(
              padding: EdgeInsets.all(isLandscape ? 12 : 20),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildInfoItem(
                        Icons.description,
                        'Files',
                        '$_logFileCount',
                        compact: isLandscape,
                      ),
                      _buildInfoItem(
                        Icons.storage,
                        'Size',
                        _logSize,
                        compact: isLandscape,
                      ),
                      _buildInfoItem(
                        Icons.text_snippet,
                        'Lines',
                        '${_logs.split('\n').length}',
                        compact: isLandscape,
                      ),
                    ],
                  ),
                  SizedBox(height: isLandscape ? 8 : 20),
                  // Log level selector
                  Row(
                    children: [
                      const Text(
                        'Log Level: ',
                        style: TextStyle(fontWeight: FontWeight.w600),
                      ),
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
                    margin: const EdgeInsets.symmetric(horizontal: 12),
                    decoration: BoxDecoration(
                      color: Colors.black87,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: Theme.of(context).colorScheme.outlineVariant,
                        width: 1,
                      ),
                    ),
                    child: _logs.isEmpty
                        ? Center(
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(
                                  Icons.article_outlined,
                                  size: 64,
                                  color: Colors.white.withOpacity(0.3),
                                ),
                                const SizedBox(height: 16),
                                const Text(
                                  'No logs available',
                                  style: TextStyle(
                                    color: Colors.white70,
                                    fontSize: 16,
                                  ),
                                ),
                              ],
                            ),
                          )
                        : SingleChildScrollView(
                            padding: const EdgeInsets.all(16),
                            child: SelectableText(
                              _logs,
                              style: const TextStyle(
                                fontFamily: 'monospace',
                                fontSize: 11,
                                color: Colors.greenAccent,
                                height: 1.5,
                              ),
                            ),
                          ),
                  ),
          ),
          
          // Action buttons
          Padding(
            padding: EdgeInsets.all(isLandscape ? 4 : 8),
            child: Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _exportLogs,
                    icon: Icon(Icons.share, size: isLandscape ? 16 : null),
                    label: Text('Export', style: TextStyle(fontSize: isLandscape ? 12 : null)),
                    style: isLandscape ? OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    ) : null,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _copyLogs,
                    icon: Icon(Icons.copy, size: isLandscape ? 16 : null),
                    label: Text('Copy', style: TextStyle(fontSize: isLandscape ? 12 : null)),
                    style: isLandscape ? OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    ) : null,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _clearLogs,
                    icon: Icon(Icons.delete, size: isLandscape ? 16 : null),
                    label: Text('Clear', style: TextStyle(fontSize: isLandscape ? 12 : null)),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.red,
                      padding: isLandscape ? const EdgeInsets.symmetric(horizontal: 8, vertical: 4) : null,
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
  
  Widget _buildInfoItem(IconData icon, String label, String value, {bool compact = false}) {
    return Column(
      children: [
        Container(
          padding: EdgeInsets.all(compact ? 6 : 10),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.primaryContainer,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(
            icon,
            size: compact ? 18 : 24,
            color: Theme.of(context).colorScheme.onPrimaryContainer,
          ),
        ),
        SizedBox(height: compact ? 4 : 8),
        Text(
          value,
          style: TextStyle(
            fontSize: compact ? 13 : 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: TextStyle(
            fontSize: compact ? 10 : 12,
            color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
          ),
        ),
      ],
    );
  }
}

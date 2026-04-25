import 'dart:io';
import 'package:flutter/material.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:share_plus/share_plus.dart';
import 'package:http/http.dart' as http;

/// BL-024: Diagnostics screen with device info, network status, and stream tester
class DiagnosticsScreen extends StatefulWidget {
  const DiagnosticsScreen({super.key});

  @override
  State<DiagnosticsScreen> createState() => _DiagnosticsScreenState();
}

class _DiagnosticsScreenState extends State<DiagnosticsScreen> {
  // Device info
  String _deviceModel = 'Loading...';
  String _osVersion = 'Loading...';
  String _screenSize = 'Loading...';
  String _appVersion = 'Loading...';
  
  // Network info
  String _connectionType = 'Checking...';
  String _connectionStatus = 'Unknown';
  
  // Stream tester
  final TextEditingController _urlController = TextEditingController();
  String _testResult = '';
  bool _isTesting = false;
  
  @override
  void initState() {
    super.initState();
    _loadDeviceInfo();
    _checkNetworkStatus();
    _listenToConnectivityChanges();
  }
  
  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }
  
  /// Load device information
  Future<void> _loadDeviceInfo() async {
    try {
      final deviceInfo = DeviceInfoPlugin();
      final packageInfo = await PackageInfo.fromPlatform();
      
      if (Platform.isAndroid) {
        final androidInfo = await deviceInfo.androidInfo;
        if (!mounted) return;
        setState(() {
          _deviceModel = '${androidInfo.manufacturer} ${androidInfo.model}';
          _osVersion = 'Android ${androidInfo.version.release} (SDK ${androidInfo.version.sdkInt})';
          _appVersion = '${packageInfo.version} (${packageInfo.buildNumber})';
        });
      } else if (Platform.isIOS) {
        final iosInfo = await deviceInfo.iosInfo;
        if (!mounted) return;
        setState(() {
          _deviceModel = '${iosInfo.name} ${iosInfo.model}';
          _osVersion = 'iOS ${iosInfo.systemVersion}';
          _appVersion = '${packageInfo.version} (${packageInfo.buildNumber})';
        });
      }
      
      // Get screen size
      if (!mounted) return;
      final size = MediaQuery.of(context).size;
      final dpr = MediaQuery.of(context).devicePixelRatio;
      setState(() {
        _screenSize = '${size.width.toInt()}x${size.height.toInt()} '
            '(${(size.width * dpr).toInt()}x${(size.height * dpr).toInt()} physical)';
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _deviceModel = 'Error loading device info';
        _osVersion = e.toString();
      });
    }
  }
  
  /// Check network status
  Future<void> _checkNetworkStatus() async {
    try {
      final connectivityResults = await Connectivity().checkConnectivity();
      if (connectivityResults.isNotEmpty) {
        _updateConnectionType(connectivityResults.first);
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _connectionType = 'Error: $e';
      });
    }
  }
  
  /// Listen to connectivity changes
  void _listenToConnectivityChanges() {
    Connectivity().onConnectivityChanged.listen((List<ConnectivityResult> results) {
      if (results.isNotEmpty) {
        _updateConnectionType(results.first);
      }
    });
  }
  
  void _updateConnectionType(ConnectivityResult result) {
    if (!mounted) return;
    setState(() {
      switch (result) {
        case ConnectivityResult.wifi:
          _connectionType = 'WiFi';
          _connectionStatus = 'Connected';
          break;
        case ConnectivityResult.mobile:
          _connectionType = 'Mobile Data';
          _connectionStatus = 'Connected';
          break;
        case ConnectivityResult.ethernet:
          _connectionType = 'Ethernet';
          _connectionStatus = 'Connected';
          break;
        case ConnectivityResult.none:
          _connectionType = 'No Connection';
          _connectionStatus = 'Disconnected';
          break;
        default:
          _connectionType = 'Unknown';
          _connectionStatus = 'Unknown';
      }
    });
  }
  
  /// Test stream URL
  Future<void> _testStreamUrl() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) {
      setState(() {
        _testResult = 'Please enter a URL';
      });
      return;
    }
    
    setState(() {
      _isTesting = true;
      _testResult = 'Testing URL...';
    });
    
    try {
      final stopwatch = Stopwatch()..start();
      
      // Try HEAD request first
      final response = await http.head(
        Uri.parse(url),
        headers: {'User-Agent': 'TV Viewer/$_appVersion'},
      ).timeout(const Duration(seconds: 10));
      
      stopwatch.stop();
      final responseTime = stopwatch.elapsedMilliseconds;
      
      if (!mounted) return;
      setState(() {
        _testResult = '✓ Stream is accessible\n'
            'Status: ${response.statusCode}\n'
            'Response Time: ${responseTime}ms\n'
            'Content-Type: ${response.headers['content-type'] ?? 'Unknown'}\n'
            'Content-Length: ${response.headers['content-length'] ?? 'Unknown'}';
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _testResult = '✗ Stream test failed\n'
            'Error: $e\n\n'
            'This could mean:\n'
            '• The URL is invalid\n'
            '• The stream is offline\n'
            '• Network connection issues\n'
            '• Firewall blocking access';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isTesting = false;
        });
      }
    }
  }
  
  /// Generate diagnostic report
  String _generateReport() {
    final buffer = StringBuffer();
    buffer.writeln('=== TV Viewer Diagnostic Report ===');
    buffer.writeln('Generated: ${DateTime.now()}');
    buffer.writeln('');
    buffer.writeln('=== Device Information ===');
    buffer.writeln('Model: $_deviceModel');
    buffer.writeln('OS: $_osVersion');
    buffer.writeln('Screen: $_screenSize');
    buffer.writeln('App Version: $_appVersion');
    buffer.writeln('');
    buffer.writeln('=== Network Information ===');
    buffer.writeln('Connection Type: $_connectionType');
    buffer.writeln('Status: $_connectionStatus');
    buffer.writeln('');
    if (_testResult.isNotEmpty) {
      buffer.writeln('=== Stream Test Results ===');
      buffer.writeln('URL: ${_urlController.text}');
      buffer.writeln(_testResult);
      buffer.writeln('');
    }
    buffer.writeln('=== End of Report ===');
    return buffer.toString();
  }
  
  /// Export diagnostic report
  void _exportReport() {
    final report = _generateReport();
    Share.share(
      report,
      subject: 'TV Viewer Diagnostic Report',
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Diagnostics'),
        actions: [
          IconButton(
            icon: const Icon(Icons.share),
            tooltip: 'Export Report',
            onPressed: _exportReport,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          await _loadDeviceInfo();
          await _checkNetworkStatus();
        },
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Device Information Section
            _buildSectionCard(
              title: 'Device Information',
              icon: Icons.phone_android,
              children: [
                _buildInfoRow('Model', _deviceModel),
                _buildInfoRow('OS Version', _osVersion),
                _buildInfoRow('Screen Size', _screenSize),
                _buildInfoRow('App Version', _appVersion),
              ],
            ),
            
            const SizedBox(height: 16),
            
            // Network Status Section
            _buildSectionCard(
              title: 'Network Status',
              icon: Icons.wifi,
              children: [
                _buildInfoRow('Connection Type', _connectionType),
                _buildInfoRow('Status', _connectionStatus),
                const SizedBox(height: 8),
                ElevatedButton.icon(
                  onPressed: _checkNetworkStatus,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Refresh Network Status'),
                ),
              ],
            ),
            
            const SizedBox(height: 16),
            
            // Stream URL Tester Section
            _buildSectionCard(
              title: 'Stream URL Tester',
              icon: Icons.link,
              children: [
                TextField(
                  controller: _urlController,
                  decoration: const InputDecoration(
                    labelText: 'Stream URL',
                    hintText: 'Enter stream URL to test',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.link),
                  ),
                  keyboardType: TextInputType.url,
                ),
                const SizedBox(height: 12),
                ElevatedButton.icon(
                  onPressed: _isTesting ? null : _testStreamUrl,
                  icon: _isTesting
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.play_arrow),
                  label: Text(_isTesting ? 'Testing...' : 'Test Stream'),
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(double.infinity, 48),
                  ),
                ),
                if (_testResult.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: _testResult.startsWith('✓')
                          ? Theme.of(context).colorScheme.primaryContainer.withOpacity(0.3)
                          : Theme.of(context).colorScheme.errorContainer.withOpacity(0.3),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: _testResult.startsWith('✓')
                            ? Theme.of(context).colorScheme.primary
                            : Theme.of(context).colorScheme.error,
                        width: 2,
                      ),
                    ),
                    child: SelectableText(
                      _testResult,
                      style: TextStyle(
                        fontFamily: 'monospace',
                        fontSize: 13,
                        height: 1.5,
                        color: Theme.of(context).colorScheme.onSurface,
                      ),
                    ),
                  ),
                ],
              ],
            ),
            
            const SizedBox(height: 24),
            
            // Export Button
            OutlinedButton.icon(
              onPressed: _exportReport,
              icon: const Icon(Icons.file_download),
              label: const Text('Export Full Diagnostic Report'),
              style: OutlinedButton.styleFrom(
                minimumSize: const Size(double.infinity, 48),
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildSectionCard({
    required String title,
    required IconData icon,
    required List<Widget> children,
  }) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(
          color: Theme.of(context).colorScheme.outlineVariant,
          width: 1,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.primaryContainer,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    icon,
                    color: Theme.of(context).colorScheme.onPrimaryContainer,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 12),
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            const Divider(height: 24),
            ...children,
          ],
        ),
      ),
    );
  }
  
  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: MediaQuery.of(context).orientation == Orientation.landscape
                ? 160.0
                : 120.0,
            child: Text(
              label,
              style: TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 13,
                color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
          ),
          Expanded(
            child: SelectableText(
              value,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// Example integration of FMStream into Flutter channel provider
//
// This file demonstrates how to integrate FMStream radio stations
// into the existing ChannelProvider.
//
// Place this code in: lib/providers/channel_provider.dart

import 'package:flutter/foundation.dart';
import '../models/channel.dart';
import '../services/m3u_service.dart';
import '../services/fmstream_service.dart';
import '../utils/logger_service.dart';

class ChannelProviderWithFMStream extends ChangeNotifier {
  // Existing code...
  List<Channel> _channels = [];
  bool _isLoading = false;
  String? _error;
  bool _enableFMStream = true; // Toggle for FMStream source
  
  // Getters
  List<Channel> get channels => _channels;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get enableFMStream => _enableFMStream;
  
  // Toggle FMStream source
  void setEnableFMStream(bool enabled) {
    if (_enableFMStream != enabled) {
      _enableFMStream = enabled;
      notifyListeners();
      
      // Optionally reload channels when toggling
      if (!_isLoading) {
        loadAllChannels();
      }
    }
  }
  
  /// Load channels from all sources (M3U + FMStream)
  Future<void> loadAllChannels() async {
    if (_isLoading) return;
    
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      logger.info('Loading channels from all sources...');
      
      // Step 1: Load M3U channels
      logger.info('Loading M3U channels...');
      final m3uChannels = await M3UService.fetchAllChannels(
        onProgress: (current, total) {
          logger.debug('M3U progress: $current/$total');
          // Could add progress notification here
        },
      );
      
      logger.info('Loaded ${m3uChannels.length} channels from M3U');
      
      // Step 2: Load FMStream radio stations (optional)
      List<Channel> fmstreamChannels = [];
      
      if (_enableFMStream) {
        try {
          logger.info('Loading FMStream radio stations...');
          fmstreamChannels = await FMStreamService.fetchFromFMStream(
            onProgress: (current, total) {
              logger.debug('FMStream progress: $current/$total');
              // Could add progress notification here
            },
          );
          
          logger.info('Loaded ${fmstreamChannels.length} radio stations from FMStream');
        } catch (e) {
          logger.error('Error loading FMStream channels', e);
          // Continue with M3U channels only
        }
      }
      
      // Step 3: Merge and deduplicate
      logger.info('Merging and deduplicating channels...');
      final allChannels = [...m3uChannels, ...fmstreamChannels];
      _channels = M3UService.deduplicateChannels(allChannels);
      
      logger.info('Total unique channels: ${_channels.length}');
      logger.info('Radio channels: ${radioChannels.length}');
      logger.info('TV channels: ${tvChannels.length}');
      
      _error = null;
      
    } catch (e, stackTrace) {
      logger.error('Error loading channels', e, stackTrace);
      _error = 'Failed to load channels: ${e.toString()}';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  /// Get radio channels only
  List<Channel> get radioChannels {
    return _channels.where((ch) => ch.mediaType == 'Radio').toList();
  }
  
  /// Get TV channels only
  List<Channel> get tvChannels {
    return _channels.where((ch) => ch.mediaType == 'TV').toList();
  }
  
  /// Get channels from a specific country
  List<Channel> getChannelsByCountry(String country) {
    return _channels
        .where((ch) => ch.country?.toLowerCase() == country.toLowerCase())
        .toList();
  }
  
  /// Get channels by genre/category
  List<Channel> getChannelsByGenre(String genre) {
    return _channels
        .where((ch) => ch.category?.toLowerCase() == genre.toLowerCase())
        .toList();
  }
  
  /// Search channels by name
  List<Channel> searchChannels(String query) {
    final lowerQuery = query.toLowerCase();
    return _channels
        .where((ch) => ch.name.toLowerCase().contains(lowerQuery))
        .toList();
  }
  
  /// Get high-quality radio stations (bitrate >= 128kbps)
  List<Channel> get highQualityRadio {
    return radioChannels
        .where((ch) => ch.bitrate != null && ch.bitrate! >= 128000)
        .toList();
  }
}

// Example usage in a widget:
/*
class ChannelListScreen extends StatefulWidget {
  @override
  _ChannelListScreenState createState() => _ChannelListScreenState();
}

class _ChannelListScreenState extends State<ChannelListScreen> {
  late ChannelProviderWithFMStream _provider;
  
  @override
  void initState() {
    super.initState();
    _provider = ChannelProviderWithFMStream();
    _provider.loadAllChannels();
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Channels'),
        actions: [
          // Toggle FMStream source
          IconButton(
            icon: Icon(_provider.enableFMStream 
              ? Icons.radio_button_checked 
              : Icons.radio_button_unchecked),
            onPressed: () {
              _provider.setEnableFMStream(!_provider.enableFMStream);
            },
            tooltip: 'Toggle FMStream',
          ),
          
          // Reload channels
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: () => _provider.loadAllChannels(),
          ),
        ],
      ),
      body: _buildBody(),
    );
  }
  
  Widget _buildBody() {
    if (_provider.isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Loading channels...'),
          ],
        ),
      );
    }
    
    if (_provider.error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 48, color: Colors.red),
            SizedBox(height: 16),
            Text(_provider.error!),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => _provider.loadAllChannels(),
              child: Text('Retry'),
            ),
          ],
        ),
      );
    }
    
    final channels = _provider.channels;
    
    if (channels.isEmpty) {
      return Center(
        child: Text('No channels found'),
      );
    }
    
    return ListView(
      children: [
        // Statistics
        _buildStatistics(),
        
        // Channel list
        ...channels.map((channel) => _buildChannelTile(channel)),
      ],
    );
  }
  
  Widget _buildStatistics() {
    final radioCount = _provider.radioChannels.length;
    final tvCount = _provider.tvChannels.length;
    final totalCount = _provider.channels.length;
    
    return Card(
      margin: EdgeInsets.all(8),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Statistics', style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            )),
            SizedBox(height: 8),
            Text('Total: $totalCount channels'),
            Text('TV: $tvCount channels'),
            Text('Radio: $radioCount channels'),
            if (_provider.enableFMStream)
              Text('FMStream: Enabled', style: TextStyle(color: Colors.green)),
          ],
        ),
      ),
    );
  }
  
  Widget _buildChannelTile(Channel channel) {
    return ListTile(
      leading: channel.logo != null
          ? Image.network(
              channel.logo!,
              width: 48,
              height: 48,
              errorBuilder: (_, __, ___) => Icon(
                channel.mediaType == 'Radio' ? Icons.radio : Icons.tv,
              ),
            )
          : Icon(channel.mediaType == 'Radio' ? Icons.radio : Icons.tv),
      title: Text(channel.name),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (channel.country != null)
            Text('${channel.country} - ${channel.category ?? 'Unknown'}'),
          if (channel.bitrate != null)
            Text('${channel.formattedBitrate}'),
        ],
      ),
      trailing: Icon(Icons.play_arrow),
      onTap: () {
        // Play channel
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => PlayerScreen(channel: channel),
          ),
        );
      },
    );
  }
}
*/

// Example: Settings screen to toggle FMStream
/*
class SettingsScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final provider = Provider.of<ChannelProviderWithFMStream>(context);
    
    return Scaffold(
      appBar: AppBar(title: Text('Settings')),
      body: ListView(
        children: [
          SwitchListTile(
            title: Text('Enable FMStream Radio'),
            subtitle: Text('Load radio stations from FMStream.org'),
            value: provider.enableFMStream,
            onChanged: (value) {
              provider.setEnableFMStream(value);
            },
          ),
          
          ListTile(
            title: Text('Radio Channels'),
            subtitle: Text('${provider.radioChannels.length} stations'),
            trailing: Icon(Icons.radio),
          ),
          
          ListTile(
            title: Text('TV Channels'),
            subtitle: Text('${provider.tvChannels.length} channels'),
            trailing: Icon(Icons.tv),
          ),
        ],
      ),
    );
  }
}
*/

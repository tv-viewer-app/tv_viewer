/// Integration Example: Using Dependency Injection with get_it
/// 
/// This example demonstrates how to integrate the dependency injection
/// system into your Flutter application and migrate existing code.

// ignore_for_file: unused_local_variable, unused_element

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:tv_viewer/di/service_locator.dart';
import 'package:tv_viewer/repositories/channel_repository.dart';
import 'package:tv_viewer/repositories/playlist_repository.dart';
import 'package:tv_viewer/models/channel.dart';
import 'package:tv_viewer/utils/logger_service.dart';

// ============================================================================
// EXAMPLE 1: Initialize in main()
// ============================================================================

void exampleMain() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize dependency injection BEFORE runApp
  await setupServiceLocator();
  
  // Logger is now available throughout the app
  final logger = getIt<LoggerService>();
  logger.info('App started with dependency injection');
  
  runApp(const MyApp());
}

// ============================================================================
// EXAMPLE 2: Simple Widget Using Repository
// ============================================================================

class ChannelListScreen extends StatefulWidget {
  const ChannelListScreen({super.key});

  @override
  State<ChannelListScreen> createState() => _ChannelListScreenState();
}

class _ChannelListScreenState extends State<ChannelListScreen> {
  // ✅ Inject dependencies using getIt
  final _channelRepo = getIt<ChannelRepository>();
  final _logger = getIt<LoggerService>();
  
  List<Channel> _channels = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadChannels();
  }

  Future<void> _loadChannels() async {
    setState(() => _isLoading = true);
    
    try {
      // First try cache
      _channels = await _channelRepo.getCachedChannels();
      setState(() {});
      
      if (_channels.isEmpty) {
        // Fetch from remote if no cache
        _logger.info('No cache found, fetching channels...');
        _channels = await _channelRepo.fetchChannels();
        
        // Save to cache
        await _channelRepo.cacheChannels(_channels);
        _logger.info('Fetched and cached ${_channels.length} channels');
      }
    } catch (e, stackTrace) {
      _logger.error('Failed to load channels', e, stackTrace);
      
      // Show error to user
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to load channels')),
        );
      }
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Channels')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
              itemCount: _channels.length,
              itemBuilder: (context, index) {
                final channel = _channels[index];
                return ListTile(
                  title: Text(channel.name),
                  subtitle: Text(channel.category ?? 'Unknown'),
                );
              },
            ),
    );
  }
}

// ============================================================================
// EXAMPLE 3: Provider with Dependency Injection
// ============================================================================

class ChannelProviderWithDI extends ChangeNotifier {
  // ✅ Inject repositories via getIt
  final ChannelRepository _repository;
  final LoggerService _logger;
  
  ChannelProviderWithDI()
      : _repository = getIt<ChannelRepository>(),
        _logger = getIt<LoggerService>();
  
  List<Channel> _channels = [];
  bool _isLoading = false;
  
  List<Channel> get channels => _channels;
  bool get isLoading => _isLoading;
  
  Future<void> loadChannels() async {
    _logger.info('Loading channels via provider...');
    _isLoading = true;
    notifyListeners();
    
    try {
      // Load from cache first
      _channels = await _repository.getCachedChannels();
      
      if (_channels.isEmpty) {
        // Fetch from remote
        _channels = await _repository.fetchChannels(
          onProgress: (current, total) {
            _logger.debug('Fetching channels: $current/$total');
          },
        );
        
        // Cache for next time
        await _repository.cacheChannels(_channels);
      }
      
      _logger.info('Loaded ${_channels.length} channels');
    } catch (e, stackTrace) {
      _logger.error('Failed to load channels', e, stackTrace);
      rethrow;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  Future<void> toggleFavorite(Channel channel) async {
    final isFav = await _repository.isFavorite(channel.url);
    
    if (isFav) {
      await _repository.removeFavorite(channel.url);
      _logger.info('Removed favorite: ${channel.name}');
    } else {
      await _repository.addFavorite(channel.url);
      _logger.info('Added favorite: ${channel.name}');
    }
    
    notifyListeners();
  }
}

// ============================================================================
// EXAMPLE 4: Using Multiple Repositories
// ============================================================================

class PlaylistImportScreen extends StatefulWidget {
  const PlaylistImportScreen({super.key});

  @override
  State<PlaylistImportScreen> createState() => _PlaylistImportScreenState();
}

class _PlaylistImportScreenState extends State<PlaylistImportScreen> {
  // ✅ Inject multiple dependencies
  final _playlistRepo = getIt<PlaylistRepository>();
  final _channelRepo = getIt<ChannelRepository>();
  final _logger = getIt<LoggerService>();
  
  final _urlController = TextEditingController();
  bool _isImporting = false;

  Future<void> _importPlaylist() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) return;
    
    setState(() => _isImporting = true);
    _logger.info('Importing playlist from: $url');
    
    try {
      // Fetch channels from playlist URL
      final channels = await _playlistRepo.fetchFromUrl(url);
      _logger.info('Imported ${channels.length} channels');
      
      // Save to cache
      await _channelRepo.cacheChannels(channels);
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Imported ${channels.length} channels')),
        );
        Navigator.pop(context);
      }
    } catch (e, stackTrace) {
      _logger.error('Failed to import playlist', e, stackTrace);
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Import failed: $e')),
        );
      }
    } finally {
      setState(() => _isImporting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Import Playlist')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _urlController,
              decoration: const InputDecoration(
                labelText: 'Playlist URL',
                hintText: 'https://example.com/playlist.m3u',
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _isImporting ? null : _importPlaylist,
              child: _isImporting
                  ? const CircularProgressIndicator()
                  : const Text('Import'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }
}

// ============================================================================
// EXAMPLE 5: Service Class with Dependency Injection
// ============================================================================

/// Example service that uses repositories via DI
class ChannelValidationService {
  // ✅ Inject dependencies via constructor
  final ChannelRepository _repository;
  final LoggerService _logger;
  
  // Constructor receives dependencies from getIt
  ChannelValidationService()
      : _repository = getIt<ChannelRepository>(),
        _logger = getIt<LoggerService>();
  
  /// Validate all channels and update cache
  Future<ValidationResult> validateAllChannels({
    void Function(int current, int total)? onProgress,
  }) async {
    _logger.info('Starting channel validation...');
    
    final channels = await _repository.getCachedChannels();
    if (channels.isEmpty) {
      _logger.warning('No channels to validate');
      return ValidationResult(working: 0, failed: 0, total: 0);
    }
    
    int working = 0;
    int failed = 0;
    
    for (int i = 0; i < channels.length; i++) {
      final channel = channels[i];
      
      try {
        final isValid = await _repository.validateChannelStream(channel.url);
        
        if (isValid) {
          working++;
        } else {
          failed++;
        }
        
        onProgress?.call(i + 1, channels.length);
        
      } catch (e) {
        _logger.warning('Failed to validate ${channel.name}', e);
        failed++;
      }
    }
    
    _logger.info('Validation complete: $working working, $failed failed');
    
    return ValidationResult(
      working: working,
      failed: failed,
      total: channels.length,
    );
  }
}

class ValidationResult {
  final int working;
  final int failed;
  final int total;
  
  ValidationResult({
    required this.working,
    required this.failed,
    required this.total,
  });
}

// ============================================================================
// EXAMPLE 6: Testing with Dependency Injection
// ============================================================================

/// Mock repository for testing
class MockChannelRepository implements ChannelRepository {
  @override
  Future<List<Channel>> fetchChannels({
    void Function(int current, int total)? onProgress,
  }) async {
    // Return mock data
    return [
      Channel(
        name: 'Test Channel',
        url: 'https://test.com/stream',
        category: 'Test',
        country: 'US',
      ),
    ];
  }

  @override
  Future<List<Channel>> getCachedChannels() async => [];

  @override
  Future<bool> cacheChannels(List<Channel> channels) async => true;

  @override
  Future<bool> validateChannelStream(String url) async => true;

  @override
  Future<Set<String>> getFavorites() async => {};

  @override
  Future<bool> addFavorite(String channelUrl) async => true;

  @override
  Future<bool> removeFavorite(String channelUrl) async => true;

  @override
  Future<bool> isFavorite(String channelUrl) async => false;

  @override
  Future<void> clearCache() async {}
}

/// Example test setup
void exampleTestSetup() async {
  // Reset service locator
  await resetServiceLocator();
  
  // Register mock implementations
  getIt.registerLazySingleton<ChannelRepository>(
    () => MockChannelRepository(),
  );
  
  getIt.registerLazySingleton<LoggerService>(
    () => LoggerService.instance,
  );
  
  // Now tests can use getIt to get mocks
  final repo = getIt<ChannelRepository>();
  final channels = await repo.fetchChannels();
  
  assert(channels.length == 1);
  assert(channels.first.name == 'Test Channel');
}

// ============================================================================
// EXAMPLE 7: Main App Setup
// ============================================================================

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    // ✅ Use provider with DI
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => ChannelProviderWithDI()..loadChannels(),
        ),
      ],
      child: MaterialApp(
        title: 'TV Viewer',
        home: const HomeScreenWithDI(),
      ),
    );
  }
}

class HomeScreenWithDI extends StatelessWidget {
  const HomeScreenWithDI({super.key});

  @override
  Widget build(BuildContext context) {
    // ✅ Access provider
    final channelProvider = Provider.of<ChannelProviderWithDI>(context);
    
    // ✅ Can also access repositories directly if needed
    final logger = getIt<LoggerService>();
    
    return Scaffold(
      appBar: AppBar(title: const Text('TV Viewer')),
      body: channelProvider.isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
              itemCount: channelProvider.channels.length,
              itemBuilder: (context, index) {
                final channel = channelProvider.channels[index];
                return ListTile(
                  title: Text(channel.name),
                  trailing: IconButton(
                    icon: const Icon(Icons.favorite_border),
                    onPressed: () {
                      channelProvider.toggleFavorite(channel);
                      logger.info('Toggled favorite for ${channel.name}');
                    },
                  ),
                );
              },
            ),
    );
  }
}

// ============================================================================
// MIGRATION GUIDE SUMMARY
// ============================================================================

/// STEP 1: Add to main()
/// ```dart
/// void main() async {
///   WidgetsFlutterBinding.ensureInitialized();
///   await setupServiceLocator();  // Add this line
///   runApp(MyApp());
/// }
/// ```
/// 
/// STEP 2: Replace direct instantiation
/// ```dart
/// // Before:
/// final repo = ChannelRepositoryImpl();
/// 
/// // After:
/// final repo = getIt<ChannelRepository>();
/// ```
/// 
/// STEP 3: Use in providers
/// ```dart
/// class MyProvider extends ChangeNotifier {
///   final _repo = getIt<ChannelRepository>();
/// }
/// ```
/// 
/// STEP 4: Use in widgets
/// ```dart
/// class MyWidget extends StatefulWidget {
///   final _logger = getIt<LoggerService>();
/// }
/// ```
/// 
/// BENEFITS:
/// - ✅ Easier testing (swap real with mock implementations)
/// - ✅ Better architecture (loose coupling)
/// - ✅ Centralized configuration
/// - ✅ Type-safe dependency access

/// Dependency Injection Setup
/// 
/// This module provides a centralized dependency injection configuration
/// using the get_it package. It simplifies access to services and repositories
/// throughout the application.
/// 
/// ## Quick Start
/// 
/// ### 1. Initialize in main()
/// ```dart
/// void main() async {
///   WidgetsFlutterBinding.ensureInitialized();
///   await setupServiceLocator();
///   runApp(MyApp());
/// }
/// ```
/// 
/// ### 2. Access dependencies anywhere
/// ```dart
/// // Import the service locator
/// import 'package:tv_viewer/di/service_locator.dart';
/// 
/// // Get a repository
/// final channelRepo = getIt<ChannelRepository>();
/// final channels = await channelRepo.fetchChannels();
/// 
/// // Get the logger
/// final logger = getIt<LoggerService>();
/// logger.info('Operation completed');
/// ```
/// 
/// ### 3. Use in Widgets
/// ```dart
/// class MyWidget extends StatefulWidget {
///   @override
///   _MyWidgetState createState() => _MyWidgetState();
/// }
/// 
/// class _MyWidgetState extends State<MyWidget> {
///   // Inject dependencies
///   final _channelRepo = getIt<ChannelRepository>();
///   final _logger = getIt<LoggerService>();
///   
///   @override
///   void initState() {
///     super.initState();
///     _loadChannels();
///   }
///   
///   Future<void> _loadChannels() async {
///     try {
///       final channels = await _channelRepo.fetchChannels();
///       _logger.info('Loaded ${channels.length} channels');
///       // Update UI...
///     } catch (e) {
///       _logger.error('Failed to load channels', e);
///     }
///   }
/// }
/// ```
/// 
/// ### 4. Use with Provider
/// ```dart
/// class ChannelProvider extends ChangeNotifier {
///   final ChannelRepository _repository;
///   
///   // Constructor injection from get_it
///   ChannelProvider() : _repository = getIt<ChannelRepository>();
///   
///   // Or use getter
///   ChannelRepository get repository => getIt<ChannelRepository>();
///   
///   Future<void> loadChannels() async {
///     final channels = await _repository.fetchChannels();
///     notifyListeners();
///   }
/// }
/// ```
/// 
/// ## Registered Services
/// 
/// The following services are available through get_it:
/// 
/// - **LoggerService**: File-based logging with rotation
///   ```dart
///   final logger = getIt<LoggerService>();
///   logger.info('Message');
///   logger.error('Error', exception, stackTrace);
///   ```
/// 
/// - **ChannelRepository**: Channel data operations
///   ```dart
///   final repo = getIt<ChannelRepository>();
///   final channels = await repo.fetchChannels();
///   await repo.addFavorite(channelUrl);
///   ```
/// 
/// - **PlaylistRepository**: Playlist/M3U operations
///   ```dart
///   final repo = getIt<PlaylistRepository>();
///   final channels = await repo.fetchFromUrl(m3uUrl);
///   final m3u = repo.exportAsM3U(channels);
///   ```
/// 
/// ## Benefits
/// 
/// 1. **Decoupling**: Classes don't need to know how to create their dependencies
/// 2. **Testability**: Easy to swap implementations for testing
/// 3. **Single Responsibility**: Services focus on business logic, not object creation
/// 4. **Centralized Configuration**: All dependencies registered in one place
/// 5. **Type Safety**: Compile-time checking of dependency types
/// 
/// ## Testing
/// 
/// For testing, you can reset and reconfigure dependencies:
/// 
/// ```dart
/// setUp(() async {
///   await resetServiceLocator();
///   
///   // Register mock implementations
///   getIt.registerLazySingleton<ChannelRepository>(
///     () => MockChannelRepository(),
///   );
/// });
/// 
/// tearDown(() async {
///   await resetServiceLocator();
/// });
/// ```
/// 
/// ## Migration Guide
/// 
/// ### Before (Direct instantiation):
/// ```dart
/// class MyWidget extends StatefulWidget {
///   @override
///   _MyWidgetState createState() => _MyWidgetState();
/// }
/// 
/// class _MyWidgetState extends State<MyWidget> {
///   final _repository = ChannelRepositoryImpl(); // ❌ Hard-coded dependency
///   
///   Future<void> loadData() async {
///     final channels = await _repository.fetchChannels();
///   }
/// }
/// ```
/// 
/// ### After (Dependency injection):
/// ```dart
/// import 'package:tv_viewer/di/service_locator.dart';
/// 
/// class MyWidget extends StatefulWidget {
///   @override
///   _MyWidgetState createState() => _MyWidgetState();
/// }
/// 
/// class _MyWidgetState extends State<MyWidget> {
///   final _repository = getIt<ChannelRepository>(); // ✅ Injected dependency
///   
///   Future<void> loadData() async {
///     final channels = await _repository.fetchChannels();
///   }
/// }
/// ```
/// 
/// ## Best Practices
/// 
/// 1. **Register interfaces, not implementations**
///    ```dart
///    // ✅ Good
///    getIt.registerLazySingleton<ChannelRepository>(
///      () => ChannelRepositoryImpl(),
///    );
///    
///    // ❌ Avoid
///    getIt.registerLazySingleton<ChannelRepositoryImpl>(
///      () => ChannelRepositoryImpl(),
///    );
///    ```
/// 
/// 2. **Use lazy singletons for stateless services**
///    ```dart
///    // Services without state can be shared
///    getIt.registerLazySingleton<ChannelRepository>(
///      () => ChannelRepositoryImpl(),
///    );
///    ```
/// 
/// 3. **Use factories for stateful objects**
///    ```dart
///    // New instance each time
///    getIt.registerFactory<MyStatefulService>(
///      () => MyStatefulService(),
///    );
///    ```
/// 
/// 4. **Initialize dependencies early**
///    ```dart
///    void main() async {
///      WidgetsFlutterBinding.ensureInitialized();
///      await setupServiceLocator(); // Initialize before runApp()
///      runApp(MyApp());
///    }
///    ```
/// 
/// 5. **Access dependencies at the point of use**
///    ```dart
///    // ✅ Good - lazy initialization
///    class MyWidget extends StatefulWidget {
///      final _repo = getIt<ChannelRepository>();
///    }
///    
///    // ❌ Avoid - top-level access
///    final globalRepo = getIt<ChannelRepository>(); // May fail if not initialized
///    ```
/// 
/// ## Architecture Notes
/// 
/// The dependency injection setup follows these principles:
/// 
/// - **Service Locator Pattern**: Central registry for all dependencies
/// - **Lazy Initialization**: Services created only when first accessed
/// - **Singleton Lifecycle**: Repositories shared across the application
/// - **Constructor Injection**: Services receive dependencies via constructor
/// - **Interface-based Design**: Register abstractions, not concrete types
/// 
/// ## Related Files
/// 
/// - `lib/di/service_locator.dart` - Main DI configuration
/// - `lib/repositories/` - Repository interfaces and implementations
/// - `lib/services/` - Service implementations
/// - `lib/utils/logger_service.dart` - Logging service
library injection;

export 'service_locator.dart';

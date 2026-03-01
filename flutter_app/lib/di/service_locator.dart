import 'package:get_it/get_it.dart';
import '../repositories/channel_repository.dart';
import '../repositories/playlist_repository.dart';
import '../repositories/impl/channel_repository_impl.dart';
import '../repositories/impl/playlist_repository_impl.dart';
import '../utils/logger_service.dart';
import '../services/analytics_service.dart';
import '../services/crashlytics_service.dart';

/// Global service locator instance
/// 
/// This is the single source of truth for dependency injection throughout
/// the application. Use this to access registered services and repositories.
final getIt = GetIt.instance;

/// Initialize and register all dependencies
/// 
/// This should be called once at application startup, before any widgets
/// are built or services are accessed.
/// 
/// Example:
/// ```dart
/// void main() async {
///   WidgetsFlutterBinding.ensureInitialized();
///   await setupServiceLocator();
///   runApp(MyApp());
/// }
/// ```
Future<void> setupServiceLocator() async {
  // Register Logger Service as a singleton
  // Logger is already initialized in main() before this is called,
  // so we just register the existing instance — no re-initialization.
  getIt.registerLazySingleton<LoggerService>(
    () => LoggerService.instance,
  );

  // Register Analytics Service as a singleton
  getIt.registerLazySingleton<AnalyticsService>(
    () => AnalyticsService.instance,
  );
  
  // Register Crashlytics Service as a singleton
  getIt.registerLazySingleton<CrashlyticsService>(
    () => CrashlyticsService.instance,
  );
  
  // Initialize analytics (Supabase-backed) and crashlytics services.
  // Wrapped in try-catch: app must still work if Supabase env vars aren't set.
  try {
    await getIt<AnalyticsService>().initialize();
  } catch (e) {
    LoggerService.instance.warning(
      'Analytics service initialization failed (non-fatal): $e',
    );
  }

  try {
    await getIt<CrashlyticsService>().initialize();
  } catch (e) {
    LoggerService.instance.warning(
      'Crashlytics service initialization failed (non-fatal): $e',
    );
  }
  
  // Register repositories as singletons
  // Repositories are stateless and can be safely shared across the app
  getIt.registerLazySingleton<ChannelRepository>(
    () => ChannelRepositoryImpl(),
  );
  
  getIt.registerLazySingleton<PlaylistRepository>(
    () => PlaylistRepositoryImpl(),
  );
  
  // Log successful initialization
  LoggerService.instance.info('Service locator initialized successfully');
}

/// Reset the service locator (useful for testing)
/// 
/// Warning: This will unregister all services and clear the container.
/// Only use this in test environments or when completely restarting the app.
Future<void> resetServiceLocator() async {
  await getIt.reset();
}

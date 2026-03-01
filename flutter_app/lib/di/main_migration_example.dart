/// MIGRATION GUIDE: Integrating Dependency Injection into main.dart
/// 
/// This file shows how to update the existing main.dart to use
/// dependency injection with get_it.

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

// ✅ ADD: Import the DI setup
import 'package:tv_viewer/di/injection.dart';

import 'screens/home_screen.dart';
import 'providers/channel_provider.dart';
import 'utils/logger_service.dart';
import 'utils/error_handler.dart';

/// Updated main() with dependency injection
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // ✅ ADD: Setup dependency injection FIRST
  // This registers all services and repositories
  await setupServiceLocator();
  
  // ✅ CHANGE: Get logger from service locator instead of direct access
  // (Optional - LoggerService.instance still works, but getIt is more consistent)
  final logger = getIt<LoggerService>();
  logger.info('TV Viewer app starting with dependency injection...');
  
  // Wrap app in error zone to catch all errors
  runZonedGuarded(() {
    // Catch Flutter framework errors
    FlutterError.onError = (FlutterErrorDetails details) {
      logger.error(
        'Flutter framework error',
        details.exception,
        details.stack,
      );
    };
    
    runApp(const TVViewerApp());
  }, (error, stackTrace) {
    // Catch async errors not caught by Flutter
    logger.error('Uncaught async error', error, stackTrace);
  });
}

class TVViewerApp extends StatelessWidget {
  const TVViewerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      // ChannelProvider can now use getIt internally
      // (see channel_provider_migration_example.dart for details)
      create: (_) => ChannelProvider(),
      child: MaterialApp(
        title: 'TV Viewer',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFF0078D4),
            brightness: Brightness.light,
          ),
          appBarTheme: const AppBarTheme(
            centerTitle: true,
            elevation: 0,
          ),
        ),
        darkTheme: ThemeData(
          useMaterial3: true,
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFF0078D4),
            brightness: Brightness.dark,
          ),
        ),
        themeMode: ThemeMode.system,
        home: const HomeScreen(),
      ),
    );
  }
}

// ============================================================================
// COMPARISON: Before vs After
// ============================================================================

/// BEFORE (Without DI):
/// ```dart
/// void main() async {
///   WidgetsFlutterBinding.ensureInitialized();
///   
///   await LoggerService.instance.initialize(minLogLevel: LogLevel.info);
///   logger.info('TV Viewer app starting...');
///   
///   runApp(const TVViewerApp());
/// }
/// ```
/// 
/// AFTER (With DI):
/// ```dart
/// void main() async {
///   WidgetsFlutterBinding.ensureInitialized();
///   
///   // Setup DI - registers and initializes all services
///   await setupServiceLocator();
///   
///   final logger = getIt<LoggerService>();
///   logger.info('TV Viewer app starting with DI...');
///   
///   runApp(const TVViewerApp());
/// }
/// ```
/// 
/// BENEFITS:
/// - Logger is automatically initialized by setupServiceLocator()
/// - All services registered in one place
/// - Easy to swap implementations for testing
/// - Repositories available throughout the app

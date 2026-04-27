import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'screens/home_screen.dart';
import 'providers/channel_provider.dart';
import 'utils/logger_service.dart';
import 'utils/error_handler.dart';
import 'di/service_locator.dart';
import 'services/analytics_service.dart';
import 'services/crashlytics_service.dart';
import 'services/parental_controls_service.dart';
import 'services/play_integrity_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize logger service first (before DI container)
  await LoggerService.instance.initialize(minLogLevel: LogLevel.info);
  logger.info('TV Viewer app starting...');
  
  // Initialize dependency injection container
  try {
    await setupServiceLocator();
    logger.info('Dependency injection initialized');
  } catch (e, stackTrace) {
    logger.error('DI setup failed (non-fatal, using fallback)', e, stackTrace);
  }
  
  // Initialize parental controls (fail-safe — uses defaults on error)
  try {
    await ParentalControlsService.instance.initialize();
    logger.info('Parental controls initialized');
  } catch (e) {
    logger.warning('Parental controls init failed (non-fatal)', e);
  }
  
  // Initialize analytics (fail-safe — never blocks app startup)
  try {
    await analytics.initialize();
    await analytics.trackAppLaunch();
  } catch (e) {
    logger.warning('Analytics init failed (non-fatal)', e);
  }
  
  // Initialize crashlytics service (fail-safe — uses fallback logger)
  try {
    await CrashlyticsService.instance.initialize();
    logger.info('Crashlytics service initialized');
  } catch (e) {
    logger.warning('Crashlytics init failed (non-fatal)', e);
  }
  
  // Verify Play Integrity (fire-and-forget, never blocks startup)
  PlayIntegrityService.instance.verifyOnStartup();
  
  // Wrap app in error zone to catch all errors
  runZonedGuarded(() {
    // Catch Flutter framework errors
    FlutterError.onError = (FlutterErrorDetails details) {
      logger.error(
        'Flutter framework error',
        details.exception,
        details.stack,
      );
      analytics.trackCrash(details.exception, details.stack);
      crashlytics.recordFlutterError(details);
    };
    
    runApp(const TVViewerApp());
  }, (error, stackTrace) {
    // Catch async errors not caught by Flutter
    logger.error('Uncaught async error', error, stackTrace);
    analytics.trackCrash(error, stackTrace);
    crashlytics.recordError(error, stackTrace, fatal: true);
  });
}

class TVViewerApp extends StatelessWidget {
  const TVViewerApp({super.key});

  static ThemeData _buildLightTheme() {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: const Color(0xFF1565C0),
      brightness: Brightness.light,
    );
    
    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      textTheme: GoogleFonts.interTextTheme().apply(
        fontFamilyFallback: ['Roboto', 'Noto Sans', 'Noto Sans Hebrew', 'sans-serif'],
      ),
      appBarTheme: AppBarTheme(
        centerTitle: true,
        elevation: 0,
        backgroundColor: colorScheme.surface,
        foregroundColor: colorScheme.onSurface,
      ),
      cardTheme: CardTheme(
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
      ),
      chipTheme: ChipThemeData(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          elevation: 2,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
    );
  }

  static ThemeData _buildDarkTheme() {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: const Color(0xFF1565C0),
      brightness: Brightness.dark,
    );
    
    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme).apply(
        fontFamilyFallback: ['Roboto', 'Noto Sans', 'Noto Sans Hebrew', 'sans-serif'],
      ),
      appBarTheme: AppBarTheme(
        centerTitle: true,
        elevation: 0,
        backgroundColor: colorScheme.surface,
        foregroundColor: colorScheme.onSurface,
      ),
      cardTheme: CardTheme(
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
      ),
      chipTheme: ChipThemeData(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          elevation: 2,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => ChannelProvider(),
      child: MaterialApp(
        title: 'TV Viewer',
        debugShowCheckedModeBanner: false,
        theme: _buildLightTheme(),
        darkTheme: _buildDarkTheme(),
        themeMode: ThemeMode.system,
        home: const HomeScreen(),
      ),
    );
  }
}

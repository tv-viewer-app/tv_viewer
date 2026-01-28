import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'screens/home_screen.dart';
import 'providers/channel_provider.dart';
import 'utils/logger_service.dart';
import 'utils/error_handler.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize logger service
  await LoggerService.instance.initialize(minLogLevel: LogLevel.info);
  logger.info('TV Viewer app starting...');
  
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

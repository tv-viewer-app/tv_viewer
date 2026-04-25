# Dependency Injection with get_it

This module implements dependency injection for the TV Viewer app using the [get_it](https://pub.dev/packages/get_it) package.

## Quick Start

### 1. Setup in main()

Add the initialization to your app's main entry point:

```dart
import 'package:tv_viewer/di/injection.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize dependency injection
  await setupServiceLocator();
  
  runApp(MyApp());
}
```

### 2. Access Dependencies

Use `getIt<T>()` to access registered services anywhere in your app:

```dart
import 'package:tv_viewer/di/service_locator.dart';

// In a widget
class MyWidget extends StatefulWidget {
  final _channelRepo = getIt<ChannelRepository>();
  final _logger = getIt<LoggerService>();
  
  // Use them...
}

// In a provider
class MyProvider extends ChangeNotifier {
  final _repository = getIt<ChannelRepository>();
}

// In a service
class MyService {
  final _logger = getIt<LoggerService>();
}
```

## Registered Services

The following services are automatically registered:

| Service | Type | Lifecycle | Description |
|---------|------|-----------|-------------|
| `LoggerService` | Singleton | Lazy | File-based logging service |
| `ChannelRepository` | Singleton | Lazy | Channel data operations |
| `PlaylistRepository` | Singleton | Lazy | M3U playlist operations |

### Usage Examples

#### LoggerService
```dart
final logger = getIt<LoggerService>();

logger.info('Application started');
logger.debug('Debug information');
logger.warning('Warning message', error);
logger.error('Error occurred', exception, stackTrace);
```

#### ChannelRepository
```dart
final repo = getIt<ChannelRepository>();

// Fetch channels
final channels = await repo.fetchChannels(
  onProgress: (current, total) {
    print('Progress: $current/$total');
  },
);

// Cache management
await repo.cacheChannels(channels);
final cached = await repo.getCachedChannels();

// Favorites
await repo.addFavorite(channelUrl);
await repo.removeFavorite(channelUrl);
final isFav = await repo.isFavorite(channelUrl);

// Validation
final isValid = await repo.validateChannelStream(url);
```

#### PlaylistRepository
```dart
final repo = getIt<PlaylistRepository>();

// Fetch from URL
final channels = await repo.fetchFromUrl('https://example.com/playlist.m3u');

// Parse M3U content
final parsed = repo.parseM3U(m3uContent);

// Fetch all default playlists
final all = await repo.fetchAllChannels();

// Export as M3U
final m3u = repo.exportAsM3U(channels);
```

## Architecture

### Service Locator Pattern

The implementation uses the **Service Locator** pattern with lazy singleton registration:

- **Lazy**: Services are created only when first accessed
- **Singleton**: One instance shared across the app
- **Type-safe**: Compile-time type checking

### Benefits

1. **Loose Coupling**: Components don't need to know implementation details
2. **Easy Testing**: Swap real implementations with mocks
3. **Centralized Configuration**: All dependencies registered in one place
4. **Clean Code**: No `new` or constructors scattered throughout
5. **Lifecycle Management**: Automatic singleton management

## Testing

### Setup Mock Services

```dart
import 'package:tv_viewer/di/service_locator.dart';

void main() {
  setUp(() async {
    // Reset service locator
    await resetServiceLocator();
    
    // Register mock implementations
    getIt.registerLazySingleton<ChannelRepository>(
      () => MockChannelRepository(),
    );
    
    getIt.registerLazySingleton<LoggerService>(
      () => MockLoggerService(),
    );
  });
  
  test('example test', () async {
    final repo = getIt<ChannelRepository>();
    final channels = await repo.fetchChannels();
    
    expect(channels, isNotEmpty);
  });
  
  tearDown(() async {
    await resetServiceLocator();
  });
}
```

### Mock Example

```dart
class MockChannelRepository implements ChannelRepository {
  @override
  Future<List<Channel>> fetchChannels({
    void Function(int current, int total)? onProgress,
  }) async {
    return [
      Channel(name: 'Test', url: 'https://test.com'),
    ];
  }
  
  // Implement other methods...
}
```

## Migration Guide

### Before (Direct Instantiation)

```dart
class MyWidget extends StatefulWidget {
  @override
  _MyWidgetState createState() => _MyWidgetState();
}

class _MyWidgetState extends State<MyWidget> {
  final _repository = ChannelRepositoryImpl(); // ❌ Hard-coded
  
  Future<void> loadData() async {
    final channels = await _repository.fetchChannels();
  }
}
```

### After (Dependency Injection)

```dart
import 'package:tv_viewer/di/service_locator.dart';

class MyWidget extends StatefulWidget {
  @override
  _MyWidgetState createState() => _MyWidgetState();
}

class _MyWidgetState extends State<MyWidget> {
  final _repository = getIt<ChannelRepository>(); // ✅ Injected
  
  Future<void> loadData() async {
    final channels = await _repository.fetchChannels();
  }
}
```

### Migrating Providers

```dart
// Before
class ChannelProvider extends ChangeNotifier {
  final _service = M3UService(); // ❌
  final _prefs = SharedPreferences.getInstance(); // ❌
}

// After
class ChannelProvider extends ChangeNotifier {
  final ChannelRepository _repository;
  final LoggerService _logger;
  
  ChannelProvider()
      : _repository = getIt<ChannelRepository>(), // ✅
        _logger = getIt<LoggerService>(); // ✅
}
```

## Best Practices

### ✅ DO: Register Interfaces

```dart
getIt.registerLazySingleton<ChannelRepository>(
  () => ChannelRepositoryImpl(),
);
```

### ❌ DON'T: Register Concrete Classes

```dart
// Avoid this - less flexible
getIt.registerLazySingleton<ChannelRepositoryImpl>(
  () => ChannelRepositoryImpl(),
);
```

### ✅ DO: Use Lazy Singletons for Stateless Services

```dart
getIt.registerLazySingleton<ChannelRepository>(
  () => ChannelRepositoryImpl(),
);
```

### ✅ DO: Use Factories for Stateful Objects

```dart
// If you need a new instance each time
getIt.registerFactory<MyStatefulService>(
  () => MyStatefulService(),
);
```

### ✅ DO: Initialize Early

```dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await setupServiceLocator(); // Before runApp()
  runApp(MyApp());
}
```

### ❌ DON'T: Access at Top Level

```dart
// Avoid - may fail if not initialized
final repo = getIt<ChannelRepository>();

void main() {
  setupServiceLocator();
}
```

### ✅ DO: Access in Methods

```dart
class MyWidget extends StatefulWidget {
  final _repo = getIt<ChannelRepository>(); // OK - lazy
  
  @override
  void initState() {
    super.initState();
    final logger = getIt<LoggerService>(); // OK
  }
}
```

## Troubleshooting

### Error: "GetIt: Object/factory with type X is not registered"

**Solution**: Make sure you called `setupServiceLocator()` in `main()`:

```dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await setupServiceLocator(); // Add this
  runApp(MyApp());
}
```

### Error: "GetIt: You have already registered a type X"

**Solution**: You're trying to register the same type twice. In tests, call `resetServiceLocator()`:

```dart
setUp(() async {
  await resetServiceLocator();
  // Now register your mocks
});
```

## File Structure

```
lib/di/
├── service_locator.dart     # Main DI setup
├── injection.dart           # Public API & documentation
├── integration_example.dart # Usage examples
└── README.md               # This file
```

## See Also

- [get_it package documentation](https://pub.dev/packages/get_it)
- [Integration Examples](./integration_example.dart)
- [Repository Pattern Documentation](../repositories/README.md)
- [Logger Service Documentation](../utils/logger_service.dart)

## Contributing

When adding new services:

1. Create the service interface and implementation
2. Register in `service_locator.dart`:
   ```dart
   getIt.registerLazySingleton<MyService>(
     () => MyServiceImpl(),
   );
   ```
3. Document in this README
4. Add usage examples to `integration_example.dart`
5. Update tests to use the new service

## Issue Reference

This implementation addresses **GitHub Issue #15**: Add dependency injection using get_it.

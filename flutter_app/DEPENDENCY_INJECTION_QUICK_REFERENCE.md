# Dependency Injection Quick Reference

## Setup (One Time)

```dart
// main.dart
import 'package:tv_viewer/di/injection.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await setupServiceLocator();  // ← Add this line
  runApp(MyApp());
}
```

## Usage

```dart
import 'package:tv_viewer/di/service_locator.dart';

// Get any service
final logger = getIt<LoggerService>();
final channelRepo = getIt<ChannelRepository>();
final playlistRepo = getIt<PlaylistRepository>();
```

## Common Patterns

### In Widgets
```dart
class MyWidget extends StatefulWidget {
  final _repo = getIt<ChannelRepository>();
  final _logger = getIt<LoggerService>();
}
```

### In Providers
```dart
class MyProvider extends ChangeNotifier {
  final _repository = getIt<ChannelRepository>();
  final _logger = getIt<LoggerService>();
}
```

### In Services
```dart
class MyService {
  final _logger = getIt<LoggerService>();
}
```

## Available Services

| Service | Type | Usage |
|---------|------|-------|
| `LoggerService` | Logging | `getIt<LoggerService>()` |
| `ChannelRepository` | Channels | `getIt<ChannelRepository>()` |
| `PlaylistRepository` | Playlists | `getIt<PlaylistRepository>()` |

## Testing

```dart
setUp(() async {
  await resetServiceLocator();
  getIt.registerLazySingleton<ChannelRepository>(
    () => MockChannelRepository(),
  );
});
```

## Examples

### Load Channels
```dart
final repo = getIt<ChannelRepository>();
final channels = await repo.fetchChannels();
```

### Log Message
```dart
final logger = getIt<LoggerService>();
logger.info('Application started');
```

### Toggle Favorite
```dart
final repo = getIt<ChannelRepository>();
await repo.addFavorite(channelUrl);
```

## Documentation

- **Full Guide**: `lib/di/README.md`
- **Examples**: `lib/di/integration_example.dart`
- **Migration**: `lib/di/main_migration_example.dart`

## Issue

GitHub Issue #15: Add dependency injection using get_it ✅

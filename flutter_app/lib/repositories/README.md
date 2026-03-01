# Repository Pattern Implementation

This document describes the repository pattern implementation for the TV Viewer Flutter app.

## Overview

The repository pattern has been implemented to improve code organization by separating data access logic from business logic. This provides:

- **Clear separation of concerns**: Data access is isolated from UI and business logic
- **Testability**: Repositories can be easily mocked for unit testing
- **Flexibility**: Easy to swap data sources (API, cache, database) without changing business logic
- **Maintainability**: Changes to data access don't affect other layers

## Architecture

```
┌─────────────────────────────────────────────┐
│            UI Layer (Widgets)               │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│      Business Logic Layer (Providers)       │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│    Repository Layer (Abstract Interfaces)   │
│  ┌──────────────────┐  ┌─────────────────┐ │
│  │ ChannelRepository│  │PlaylistRepository│ │
│  └──────────────────┘  └─────────────────┘ │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  Implementation Layer (Concrete Classes)    │
│  ┌────────────────────┐ ┌────────────────┐ │
│  │ChannelRepositoryImpl│ │PlaylistRepoImpl│ │
│  └────────────────────┘ └────────────────┘ │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  Data Sources (Services, Storage, APIs)     │
│  • M3UService                               │
│  • SharedPreferences                        │
│  • FavoritesService                         │
└─────────────────────────────────────────────┘
```

## Repository Interfaces

### 1. ChannelRepository

**Location**: `lib/repositories/channel_repository.dart`

Abstract interface for channel data operations. Provides methods for:

- **fetchChannels()** - Fetch channels from remote sources
- **getCachedChannels()** - Retrieve channels from local cache
- **cacheChannels()** - Save channels to local cache
- **validateChannelStream()** - Check if a stream URL is accessible
- **getFavorites()** - Get favorite channel URLs
- **addFavorite()** - Add a channel to favorites
- **removeFavorite()** - Remove a channel from favorites
- **isFavorite()** - Check if a channel is favorited
- **clearCache()** - Clear all cached data

### 2. PlaylistRepository

**Location**: `lib/repositories/playlist_repository.dart`

Abstract interface for M3U playlist operations. Provides methods for:

- **fetchFromUrl()** - Fetch and parse M3U playlist from URL
- **parseM3U()** - Parse M3U content into Channel objects
- **fetchAllChannels()** - Fetch from all configured playlist sources
- **deduplicateChannels()** - Remove duplicate channels
- **exportAsM3U()** - Export channels to M3U format

## Repository Implementations

### 1. ChannelRepositoryImpl

**Location**: `lib/repositories/impl/channel_repository_impl.dart`

Default implementation using:
- **M3UService** for remote channel fetching
- **SharedPreferences** for local caching
- **FavoritesService** for favorites persistence

Key features:
- Comprehensive error handling
- Detailed logging for debugging
- Safe fallbacks (returns empty lists on errors)
- JSON serialization for caching

### 2. PlaylistRepositoryImpl

**Location**: `lib/repositories/impl/playlist_repository_impl.dart`

Default implementation wrapping M3UService functionality:
- Fetches from default IPTV repositories
- Parses M3U format with metadata extraction
- Deduplicates channels based on URL
- Exports channels with full metadata

Key features:
- Metadata preservation (logo, country, language)
- Only exports working channels
- Comprehensive error handling
- Progress callback support

## Usage Examples

### Using ChannelRepository

```dart
import 'package:tv_viewer/repositories/channel_repository.dart';
import 'package:tv_viewer/repositories/impl/channel_repository_impl.dart';

// Create repository instance
final ChannelRepository channelRepo = ChannelRepositoryImpl();

// Fetch channels from remote
final channels = await channelRepo.fetchChannels(
  onProgress: (current, total) {
    print('Progress: $current/$total');
  },
);

// Cache channels locally
await channelRepo.cacheChannels(channels);

// Load from cache
final cachedChannels = await channelRepo.getCachedChannels();

// Manage favorites
await channelRepo.addFavorite(channel.url);
final isFav = await channelRepo.isFavorite(channel.url);
await channelRepo.removeFavorite(channel.url);

// Validate stream
final isValid = await channelRepo.validateChannelStream(channel.url);
```

### Using PlaylistRepository

```dart
import 'package:tv_viewer/repositories/playlist_repository.dart';
import 'package:tv_viewer/repositories/impl/playlist_repository_impl.dart';

// Create repository instance
final PlaylistRepository playlistRepo = PlaylistRepositoryImpl();

// Fetch from specific URL
final channels = await playlistRepo.fetchFromUrl('https://example.com/playlist.m3u');

// Parse M3U content
final m3uContent = '...'; // M3U text content
final parsedChannels = playlistRepo.parseM3U(m3uContent);

// Fetch from all sources
final allChannels = await playlistRepo.fetchAllChannels(
  onProgress: (current, total) {
    print('Fetching playlist $current of $total');
  },
);

// Deduplicate
final uniqueChannels = playlistRepo.deduplicateChannels(allChannels);

// Export to M3U
final m3uExport = playlistRepo.exportAsM3U(channels);
```

## Migration Guide

To migrate existing code to use repositories:

### Before (Direct Service Calls)
```dart
// In Provider
final channels = await M3UService.fetchAllChannels();
final prefs = await SharedPreferences.getInstance();
await prefs.setString('channels_cache', jsonEncode(channels));
```

### After (Repository Pattern)
```dart
// In Provider
final channels = await channelRepo.fetchChannels();
await channelRepo.cacheChannels(channels);
```

### Benefits of Migration
- Less coupling to specific implementations
- Easier to test (can mock repositories)
- Cleaner, more maintainable code
- Better error handling
- Consistent logging

## Testing

Test stubs have been created for both repository implementations:

- `test/repositories/impl/channel_repository_impl_test.dart`
- `test/repositories/impl/playlist_repository_impl_test.dart`

Each test file includes TODO markers for implementing comprehensive unit tests covering:
- Success scenarios
- Error handling
- Edge cases
- Logging verification

### Running Tests

```bash
# Run all repository tests
flutter test test/repositories/

# Run specific test file
flutter test test/repositories/impl/channel_repository_impl_test.dart
```

## Future Enhancements

Potential improvements for the repository pattern:

1. **Dependency Injection**: Use a DI framework (get_it, provider) to inject repositories
2. **Multiple Implementations**: Create alternative implementations (e.g., SQLite, Remote API)
3. **Repository Factory**: Factory pattern for creating repository instances
4. **Caching Strategy**: Implement cache expiration and refresh logic
5. **Offline Support**: Enhanced offline-first capabilities
6. **Batch Operations**: Support for bulk channel operations
7. **Stream Support**: Use Dart Streams for real-time updates

## Related Files

### Created Files
- `lib/repositories/channel_repository.dart` - ChannelRepository interface
- `lib/repositories/playlist_repository.dart` - PlaylistRepository interface
- `lib/repositories/impl/channel_repository_impl.dart` - ChannelRepository implementation
- `lib/repositories/impl/playlist_repository_impl.dart` - PlaylistRepository implementation
- `test/repositories/impl/channel_repository_impl_test.dart` - Test stubs
- `test/repositories/impl/playlist_repository_impl_test.dart` - Test stubs

### Existing Files (Not Modified)
- `lib/services/m3u_service.dart` - Still used by repository implementations
- `lib/services/favorites_service.dart` - Still used by repository implementations
- `lib/providers/channel_provider.dart` - Can now be refactored to use repositories

## Best Practices

When using repositories:

1. **Always use interfaces**: Depend on abstractions, not concrete implementations
2. **Handle errors gracefully**: Repositories should catch and log errors appropriately
3. **Use async/await**: All data operations should be asynchronous
4. **Log important events**: Use logger service for debugging
5. **Keep repositories focused**: Each repository should have a single responsibility
6. **Test thoroughly**: Mock repositories in unit tests, test implementations separately

## Notes

- This is a **refactoring task** - existing functionality is preserved
- Repositories wrap existing services (M3UService, FavoritesService)
- No breaking changes to existing code (services still work as before)
- Providers can be gradually migrated to use repositories
- The pattern provides foundation for future architectural improvements

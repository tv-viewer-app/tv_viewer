# TV Viewer App - Critical Refactoring Examples

**Concrete code examples for key improvements**

---

## 1. Convert Static M3UService to Injectable Instance

### ❌ Current Implementation (Static - Untestable)

```dart
// lib/services/m3u_service.dart
class M3UService {
  static const List<String> defaultRepositories = [...];
  
  static Future<List<Channel>> fetchFromUrl(String url) async {
    final response = await http.get(Uri.parse(url));
    // ...
  }
  
  static Future<bool> checkStream(String url) async {
    final response = await http.head(Uri.parse(url));
    // ...
  }
}

// Usage in provider
final channels = await M3UService.fetchAllChannels();  // ❌ Can't mock!
```

**Problems:**
- Cannot mock for testing
- Hard dependency on http package
- Cannot swap implementations
- Violates Dependency Inversion Principle

### ✅ Refactored Implementation (Injectable - Testable)

```dart
// lib/data/datasources/channel_remote_datasource.dart
import 'package:http/http.dart' as http;
import '../../models/channel.dart';
import '../../core/errors/exceptions.dart';

abstract class ChannelRemoteDataSource {
  Future<List<Channel>> fetchChannels(List<String> repositoryUrls);
  Future<bool> validateStream(String url);
}

class ChannelRemoteDataSourceImpl implements ChannelRemoteDataSource {
  final http.Client client;
  
  const ChannelRemoteDataSourceImpl({required this.client});
  
  @override
  Future<List<Channel>> fetchChannels(List<String> repositoryUrls) async {
    final allChannels = <Channel>[];
    final seenUrls = <String>{};
    
    for (final url in repositoryUrls) {
      try {
        final response = await client.get(
          Uri.parse(url),
          headers: {'User-Agent': 'TV Viewer/1.5.0'},
        ).timeout(const Duration(seconds: 30));
        
        if (response.statusCode == 200) {
          final channels = _parseM3U(response.body);
          for (final channel in channels) {
            if (!seenUrls.contains(channel.url)) {
              seenUrls.add(channel.url);
              allChannels.add(channel);
            }
          }
        } else {
          throw ServerException(
            'Repository returned ${response.statusCode}',
            statusCode: response.statusCode,
          );
        }
      } on SocketException {
        throw const NetworkException('No internet connection');
      } on TimeoutException {
        throw const NetworkException('Request timed out');
      }
    }
    
    return allChannels;
  }
  
  @override
  Future<bool> validateStream(String url) async {
    try {
      final response = await client.head(
        Uri.parse(url),
        headers: {'User-Agent': 'TV Viewer/1.5.0'},
      ).timeout(const Duration(seconds: 5));
      
      return [200, 206, 301, 302].contains(response.statusCode);
    } catch (e) {
      return false;
    }
  }
  
  List<Channel> _parseM3U(String content) {
    final channels = <Channel>[];
    final lines = content.split('\n');
    String? currentInfo;
    
    for (final line in lines) {
      final trimmed = line.trim();
      
      if (trimmed.startsWith('#EXTINF:')) {
        currentInfo = trimmed;
      } else if (trimmed.isNotEmpty && 
                 !trimmed.startsWith('#') && 
                 currentInfo != null) {
        if (_isValidStreamUrl(trimmed)) {
          channels.add(Channel.fromM3ULine(currentInfo, trimmed));
        }
        currentInfo = null;
      }
    }
    
    return channels;
  }
  
  bool _isValidStreamUrl(String url) {
    return url.startsWith('http://') || 
           url.startsWith('https://') ||
           url.startsWith('rtmp://') || 
           url.startsWith('rtsp://');
  }
}
```

### ✅ Unit Test Example

```dart
// test/data/datasources/channel_remote_datasource_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:http/http.dart' as http;

class MockHttpClient extends Mock implements http.Client {}

void main() {
  late ChannelRemoteDataSourceImpl dataSource;
  late MockHttpClient mockClient;
  
  setUp(() {
    mockClient = MockHttpClient();
    dataSource = ChannelRemoteDataSourceImpl(client: mockClient);
  });
  
  group('fetchChannels', () {
    const testUrl = 'https://example.com/playlist.m3u';
    final testM3UContent = '''
#EXTM3U
#EXTINF:-1 group-title="Sports",ESPN
http://example.com/espn.m3u8
#EXTINF:-1 group-title="News",CNN
http://example.com/cnn.m3u8
    ''';
    
    test('should return channels on successful fetch', () async {
      // Arrange
      when(() => mockClient.get(
        any(),
        headers: any(named: 'headers'),
      )).thenAnswer((_) async => http.Response(testM3UContent, 200));
      
      // Act
      final result = await dataSource.fetchChannels([testUrl]);
      
      // Assert
      expect(result, isA<List<Channel>>());
      expect(result.length, 2);
      expect(result[0].name, 'ESPN');
      expect(result[1].name, 'CNN');
      verify(() => mockClient.get(
        Uri.parse(testUrl),
        headers: {'User-Agent': 'TV Viewer/1.5.0'},
      )).called(1);
    });
    
    test('should throw ServerException on non-200 response', () async {
      // Arrange
      when(() => mockClient.get(any(), headers: any(named: 'headers')))
        .thenAnswer((_) async => http.Response('Not Found', 404));
      
      // Act & Assert
      expect(
        () => dataSource.fetchChannels([testUrl]),
        throwsA(isA<ServerException>()),
      );
    });
    
    test('should throw NetworkException on SocketException', () async {
      // Arrange
      when(() => mockClient.get(any(), headers: any(named: 'headers')))
        .thenThrow(const SocketException('No internet'));
      
      // Act & Assert
      expect(
        () => dataSource.fetchChannels([testUrl]),
        throwsA(isA<NetworkException>()),
      );
    });
  });
}
```

---

## 2. Implement Repository Pattern

### ✅ Repository Interface (Domain Layer)

```dart
// lib/domain/repositories/channel_repository.dart
import 'package:dartz/dartz.dart';  // For Either type
import '../entities/channel.dart';
import '../../core/errors/failures.dart';

abstract class ChannelRepository {
  /// Fetch channels from remote or cache
  /// Returns Either<Failure, List<Channel>>
  Future<Either<Failure, List<Channel>>> getChannels();
  
  /// Validate a specific channel stream
  Future<Either<Failure, bool>> validateChannel(String url);
  
  /// Validate multiple channels
  Future<Either<Failure, List<Channel>>> validateChannels(
    List<Channel> channels,
    void Function(int current, int total)? onProgress,
  );
  
  /// Cache channels locally
  Future<Either<Failure, void>> cacheChannels(List<Channel> channels);
  
  /// Get only cached channels
  Future<Either<Failure, List<Channel>>> getCachedChannels();
}
```

### ✅ Repository Implementation (Data Layer)

```dart
// lib/data/repositories/channel_repository_impl.dart
import 'package:dartz/dartz.dart';
import '../../domain/repositories/channel_repository.dart';
import '../../domain/entities/channel.dart';
import '../../core/errors/failures.dart';
import '../../core/errors/exceptions.dart';
import '../datasources/channel_remote_datasource.dart';
import '../datasources/channel_local_datasource.dart';

class ChannelRepositoryImpl implements ChannelRepository {
  final ChannelRemoteDataSource remoteDataSource;
  final ChannelLocalDataSource localDataSource;
  final List<String> repositoryUrls;
  
  const ChannelRepositoryImpl({
    required this.remoteDataSource,
    required this.localDataSource,
    required this.repositoryUrls,
  });
  
  @override
  Future<Either<Failure, List<Channel>>> getChannels() async {
    try {
      // Try to fetch from remote
      final channels = await remoteDataSource.fetchChannels(repositoryUrls);
      
      // Cache the results
      await localDataSource.cacheChannels(channels);
      
      return Right(channels);
    } on NetworkException catch (e) {
      // Network failed, try cache
      try {
        final cachedChannels = await localDataSource.getCachedChannels();
        if (cachedChannels.isNotEmpty) {
          return Right(cachedChannels);
        }
        return Left(NetworkFailure(e.message));
      } on CacheException {
        return Left(NetworkFailure(e.message));
      }
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    } on ParseException catch (e) {
      return Left(ParseFailure(e.message));
    } catch (e) {
      return Left(const UnknownFailure('An unexpected error occurred'));
    }
  }
  
  @override
  Future<Either<Failure, bool>> validateChannel(String url) async {
    try {
      final isValid = await remoteDataSource.validateStream(url);
      return Right(isValid);
    } on NetworkException catch (e) {
      return Left(NetworkFailure(e.message));
    } catch (e) {
      return Left(const UnknownFailure('Validation failed'));
    }
  }
  
  @override
  Future<Either<Failure, List<Channel>>> validateChannels(
    List<Channel> channels,
    void Function(int current, int total)? onProgress,
  ) async {
    try {
      final validatedChannels = <Channel>[];
      int current = 0;
      
      // Validate in batches of 5
      const batchSize = 5;
      for (int i = 0; i < channels.length; i += batchSize) {
        final batch = channels.skip(i).take(batchSize).toList();
        
        final results = await Future.wait(
          batch.map((channel) async {
            final isWorking = await remoteDataSource.validateStream(channel.url);
            return channel.copyWith(
              isWorking: isWorking,
              lastChecked: DateTime.now(),
            );
          }),
        );
        
        validatedChannels.addAll(results);
        current += batch.length;
        onProgress?.call(current, channels.length);
        
        // Small delay to prevent overwhelming
        await Future.delayed(const Duration(milliseconds: 50));
      }
      
      // Cache updated channels
      await localDataSource.cacheChannels(validatedChannels);
      
      return Right(validatedChannels);
    } catch (e) {
      return Left(const UnknownFailure('Validation process failed'));
    }
  }
  
  @override
  Future<Either<Failure, void>> cacheChannels(List<Channel> channels) async {
    try {
      await localDataSource.cacheChannels(channels);
      return const Right(null);
    } on CacheException catch (e) {
      return Left(CacheFailure(e.message));
    }
  }
  
  @override
  Future<Either<Failure, List<Channel>>> getCachedChannels() async {
    try {
      final channels = await localDataSource.getCachedChannels();
      return Right(channels);
    } on CacheException catch (e) {
      return Left(CacheFailure(e.message));
    }
  }
}
```

### ✅ Repository Test

```dart
// test/data/repositories/channel_repository_impl_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:dartz/dartz.dart';

class MockRemoteDataSource extends Mock implements ChannelRemoteDataSource {}
class MockLocalDataSource extends Mock implements ChannelLocalDataSource {}

void main() {
  late ChannelRepositoryImpl repository;
  late MockRemoteDataSource mockRemoteDataSource;
  late MockLocalDataSource mockLocalDataSource;
  
  setUp(() {
    mockRemoteDataSource = MockRemoteDataSource();
    mockLocalDataSource = MockLocalDataSource();
    repository = ChannelRepositoryImpl(
      remoteDataSource: mockRemoteDataSource,
      localDataSource: mockLocalDataSource,
      repositoryUrls: ['https://example.com/playlist.m3u'],
    );
  });
  
  group('getChannels', () {
    final testChannels = [
      Channel(name: 'Test Channel', url: 'http://test.com'),
    ];
    
    test('should return channels from remote and cache them', () async {
      // Arrange
      when(() => mockRemoteDataSource.fetchChannels(any()))
        .thenAnswer((_) async => testChannels);
      when(() => mockLocalDataSource.cacheChannels(any()))
        .thenAnswer((_) async => Future.value());
      
      // Act
      final result = await repository.getChannels();
      
      // Assert
      expect(result, Right(testChannels));
      verify(() => mockRemoteDataSource.fetchChannels(any())).called(1);
      verify(() => mockLocalDataSource.cacheChannels(testChannels)).called(1);
    });
    
    test('should return cached channels when network fails', () async {
      // Arrange
      when(() => mockRemoteDataSource.fetchChannels(any()))
        .thenThrow(const NetworkException('No internet'));
      when(() => mockLocalDataSource.getCachedChannels())
        .thenAnswer((_) async => testChannels);
      
      // Act
      final result = await repository.getChannels();
      
      // Assert
      expect(result, Right(testChannels));
      verify(() => mockRemoteDataSource.fetchChannels(any())).called(1);
      verify(() => mockLocalDataSource.getCachedChannels()).called(1);
    });
    
    test('should return NetworkFailure when both remote and cache fail', () async {
      // Arrange
      when(() => mockRemoteDataSource.fetchChannels(any()))
        .thenThrow(const NetworkException('No internet'));
      when(() => mockLocalDataSource.getCachedChannels())
        .thenThrow(const CacheException('No cache'));
      
      // Act
      final result = await repository.getChannels();
      
      // Assert
      expect(result.isLeft(), true);
      result.fold(
        (failure) => expect(failure, isA<NetworkFailure>()),
        (_) => fail('Should have returned failure'),
      );
    });
  });
}
```

---

## 3. Add Use Cases (Business Logic Layer)

### ✅ Fetch Channels Use Case

```dart
// lib/domain/usecases/fetch_channels.dart
import 'package:dartz/dartz.dart';
import '../repositories/channel_repository.dart';
import '../entities/channel.dart';
import '../../core/errors/failures.dart';

class FetchChannels {
  final ChannelRepository repository;
  
  const FetchChannels(this.repository);
  
  Future<Either<Failure, List<Channel>>> call() async {
    return await repository.getChannels();
  }
}
```

### ✅ Filter Channels Use Case

```dart
// lib/domain/usecases/filter_channels.dart
import '../entities/channel.dart';

class FilterChannelsParams {
  final List<Channel> channels;
  final String? category;
  final String? country;
  final String? mediaType;
  final String? searchQuery;
  
  const FilterChannelsParams({
    required this.channels,
    this.category,
    this.country,
    this.mediaType,
    this.searchQuery,
  });
}

class FilterChannels {
  List<Channel> call(FilterChannelsParams params) {
    return params.channels.where((channel) {
      // Category filter
      if (params.category != null && params.category != 'All') {
        if ((channel.category ?? 'Other') != params.category) {
          return false;
        }
      }
      
      // Country filter
      if (params.country != null && params.country != 'All') {
        if ((channel.country ?? 'Unknown') != params.country) {
          return false;
        }
      }
      
      // Media type filter
      if (params.mediaType != null && params.mediaType != 'All') {
        if (channel.mediaType != params.mediaType) {
          return false;
        }
      }
      
      // Search filter
      if (params.searchQuery != null && params.searchQuery!.isNotEmpty) {
        final query = params.searchQuery!.toLowerCase();
        return channel.name.toLowerCase().contains(query) ||
               (channel.category?.toLowerCase().contains(query) ?? false) ||
               (channel.country?.toLowerCase().contains(query) ?? false);
      }
      
      return true;
    }).toList();
  }
}
```

### ✅ Validate Channels Use Case

```dart
// lib/domain/usecases/validate_channels.dart
import 'package:dartz/dartz.dart';
import '../repositories/channel_repository.dart';
import '../entities/channel.dart';
import '../../core/errors/failures.dart';

class ValidateChannelsParams {
  final List<Channel> channels;
  final void Function(int current, int total)? onProgress;
  
  const ValidateChannelsParams({
    required this.channels,
    this.onProgress,
  });
}

class ValidateChannels {
  final ChannelRepository repository;
  
  const ValidateChannels(this.repository);
  
  Future<Either<Failure, List<Channel>>> call(
    ValidateChannelsParams params,
  ) async {
    return await repository.validateChannels(
      params.channels,
      params.onProgress,
    );
  }
}
```

---

## 4. Refactor Provider to Use Use Cases

### ✅ Simplified Provider

```dart
// lib/presentation/providers/channel_provider.dart
import 'dart:async';
import 'package:flutter/foundation.dart';
import '../../domain/entities/channel.dart';
import '../../domain/usecases/fetch_channels.dart';
import '../../domain/usecases/filter_channels.dart';
import '../../domain/usecases/validate_channels.dart';
import '../../core/errors/failures.dart';

class ChannelProvider extends ChangeNotifier {
  final FetchChannels fetchChannelsUseCase;
  final FilterChannels filterChannelsUseCase;
  final ValidateChannels validateChannelsUseCase;
  
  ChannelProvider({
    required this.fetchChannelsUseCase,
    required this.filterChannelsUseCase,
    required this.validateChannelsUseCase,
  });
  
  // State
  List<Channel> _allChannels = [];
  List<Channel> _filteredChannels = [];
  Set<String> _categories = {};
  Set<String> _countries = {};
  
  String _selectedCategory = 'All';
  String _selectedCountry = 'All';
  String _selectedMediaType = 'All';
  String _searchQuery = '';
  
  bool _isLoading = false;
  bool _isValidating = false;
  Failure? _failure;
  
  int _validationProgress = 0;
  int _validationTotal = 0;
  int _workingCount = 0;
  int _failedCount = 0;
  
  Timer? _searchDebounce;
  
  // Getters
  List<Channel> get channels => _filteredChannels;
  List<String> get categories => ['All', ..._categories.toList()..sort()];
  List<String> get countries => ['All', ..._countries.toList()..sort()];
  List<String> get mediaTypes => ['All', 'TV', 'Radio'];
  
  String get selectedCategory => _selectedCategory;
  String get selectedCountry => _selectedCountry;
  String get selectedMediaType => _selectedMediaType;
  String get searchQuery => _searchQuery;
  
  bool get isLoading => _isLoading;
  bool get isValidating => _isValidating;
  bool get hasError => _failure != null;
  Failure? get failure => _failure;
  
  int get validationProgress => _validationProgress;
  int get validationTotal => _validationTotal;
  int get workingCount => _workingCount;
  int get failedCount => _failedCount;
  
  /// Load channels
  Future<void> loadChannels() async {
    _isLoading = true;
    _failure = null;
    notifyListeners();
    
    final result = await fetchChannelsUseCase();
    
    result.fold(
      (failure) {
        _failure = failure;
        _isLoading = false;
        notifyListeners();
      },
      (channels) {
        _allChannels = channels;
        _updateMetadata();
        _applyFilters();
        _isLoading = false;
        notifyListeners();
      },
    );
  }
  
  /// Validate channels
  Future<void> validateChannels() async {
    if (_isValidating) return;
    
    _isValidating = true;
    _validationProgress = 0;
    _validationTotal = _allChannels.length;
    _workingCount = 0;
    _failedCount = 0;
    notifyListeners();
    
    final result = await validateChannelsUseCase(
      ValidateChannelsParams(
        channels: _allChannels,
        onProgress: (current, total) {
          _validationProgress = current;
          
          // Count working/failed
          _workingCount = _allChannels
              .where((c) => c.lastChecked != null && c.isWorking)
              .length;
          _failedCount = _allChannels
              .where((c) => c.lastChecked != null && !c.isWorking)
              .length;
          
          notifyListeners();
        },
      ),
    );
    
    result.fold(
      (failure) {
        _failure = failure;
      },
      (validatedChannels) {
        _allChannels = validatedChannels;
        _applyFilters();
      },
    );
    
    _isValidating = false;
    notifyListeners();
  }
  
  /// Set category filter
  void setCategory(String category) {
    _selectedCategory = category;
    _applyFilters();
    notifyListeners();
  }
  
  /// Set country filter
  void setCountry(String country) {
    _selectedCountry = country;
    _applyFilters();
    notifyListeners();
  }
  
  /// Set media type filter
  void setMediaType(String mediaType) {
    _selectedMediaType = mediaType;
    _applyFilters();
    notifyListeners();
  }
  
  /// Set search query (with debouncing)
  void setSearchQuery(String query) {
    _searchQuery = query;
    
    _searchDebounce?.cancel();
    _searchDebounce = Timer(const Duration(milliseconds: 300), () {
      _applyFilters();
      notifyListeners();
    });
  }
  
  /// Clear error
  void clearError() {
    _failure = null;
    notifyListeners();
  }
  
  void _updateMetadata() {
    _categories = _allChannels
        .map((c) => c.category ?? 'Other')
        .where((c) => c.isNotEmpty)
        .toSet();
    
    _countries = _allChannels
        .map((c) => c.country ?? 'Unknown')
        .where((c) => c.isNotEmpty && c != 'Unknown')
        .toSet();
  }
  
  void _applyFilters() {
    _filteredChannels = filterChannelsUseCase(
      FilterChannelsParams(
        channels: _allChannels,
        category: _selectedCategory,
        country: _selectedCountry,
        mediaType: _selectedMediaType,
        searchQuery: _searchQuery,
      ),
    );
  }
  
  @override
  void dispose() {
    _searchDebounce?.cancel();
    super.dispose();
  }
}
```

**Benefits:**
- ✅ Provider only manages UI state
- ✅ Business logic in use cases
- ✅ Easy to test (inject mock use cases)
- ✅ Clear separation of concerns
- ✅ ~100 lines shorter than before

---

## 5. Dependency Injection Setup

### ✅ Injection Container

```dart
// lib/core/di/injection_container.dart
import 'package:get_it/get_it.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../../data/datasources/channel_remote_datasource.dart';
import '../../data/datasources/channel_local_datasource.dart';
import '../../data/repositories/channel_repository_impl.dart';
import '../../domain/repositories/channel_repository.dart';
import '../../domain/usecases/fetch_channels.dart';
import '../../domain/usecases/filter_channels.dart';
import '../../domain/usecases/validate_channels.dart';
import '../../presentation/providers/channel_provider.dart';
import '../constants/app_constants.dart';

final sl = GetIt.instance;

Future<void> initDependencies() async {
  // External dependencies
  sl.registerLazySingleton<http.Client>(() => http.Client());
  
  final sharedPreferences = await SharedPreferences.getInstance();
  sl.registerLazySingleton<SharedPreferences>(() => sharedPreferences);
  
  // Data sources
  sl.registerLazySingleton<ChannelRemoteDataSource>(
    () => ChannelRemoteDataSourceImpl(client: sl()),
  );
  
  sl.registerLazySingleton<ChannelLocalDataSource>(
    () => ChannelLocalDataSourceImpl(sharedPreferences: sl()),
  );
  
  // Repository
  sl.registerLazySingleton<ChannelRepository>(
    () => ChannelRepositoryImpl(
      remoteDataSource: sl(),
      localDataSource: sl(),
      repositoryUrls: AppConstants.defaultRepositories,
    ),
  );
  
  // Use cases
  sl.registerLazySingleton(() => FetchChannels(sl()));
  sl.registerLazySingleton(() => FilterChannels());
  sl.registerLazySingleton(() => ValidateChannels(sl()));
  
  // Providers
  sl.registerFactory(
    () => ChannelProvider(
      fetchChannelsUseCase: sl(),
      filterChannelsUseCase: sl(),
      validateChannelsUseCase: sl(),
    ),
  );
}
```

### ✅ Update main.dart

```dart
// lib/main.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/di/injection_container.dart' as di;
import 'presentation/screens/home_screen.dart';
import 'presentation/providers/channel_provider.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize dependencies
  await di.initDependencies();
  
  runApp(const TVViewerApp());
}

class TVViewerApp extends StatelessWidget {
  const TVViewerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => di.sl<ChannelProvider>(),  // ✅ Inject from DI container
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
```

---

## 6. Make Channel Immutable with copyWith

### ❌ Current (Mutable)

```dart
class Channel {
  final String name;
  final String url;
  bool isWorking;  // ❌ Mutable - can cause bugs
  DateTime? lastChecked;  // ❌ Mutable
  
  // ... rest
}

// Usage (dangerous):
channel.isWorking = false;  // Direct mutation
```

### ✅ Refactored (Immutable)

```dart
// lib/domain/entities/channel.dart
class Channel {
  final String name;
  final String url;
  final String? category;
  final String? logo;
  final String? country;
  final String? language;
  final String mediaType;
  final bool isWorking;  // ✅ Immutable
  final DateTime? lastChecked;  // ✅ Immutable
  final String? resolution;
  final int? bitrate;
  
  const Channel({
    required this.name,
    required this.url,
    this.category,
    this.logo,
    this.country,
    this.language,
    this.mediaType = 'TV',
    this.isWorking = true,
    this.lastChecked,
    this.resolution,
    this.bitrate,
  });
  
  /// Create a copy with modified fields
  Channel copyWith({
    String? name,
    String? url,
    String? category,
    String? logo,
    String? country,
    String? language,
    String? mediaType,
    bool? isWorking,
    DateTime? lastChecked,
    String? resolution,
    int? bitrate,
  }) {
    return Channel(
      name: name ?? this.name,
      url: url ?? this.url,
      category: category ?? this.category,
      logo: logo ?? this.logo,
      country: country ?? this.country,
      language: language ?? this.language,
      mediaType: mediaType ?? this.mediaType,
      isWorking: isWorking ?? this.isWorking,
      lastChecked: lastChecked ?? this.lastChecked,
      resolution: resolution ?? this.resolution,
      bitrate: bitrate ?? this.bitrate,
    );
  }
  
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Channel &&
          runtimeType == other.runtimeType &&
          url == other.url;
  
  @override
  int get hashCode => url.hashCode;
  
  // ... rest of methods
}

// Usage (safe):
final updatedChannel = channel.copyWith(
  isWorking: false,
  lastChecked: DateTime.now(),
);
```

---

## Summary

These refactorings transform the app from:
- ❌ Untestable static methods → ✅ Injectable, mockable dependencies
- ❌ God-object provider → ✅ Focused use cases
- ❌ Direct service calls → ✅ Repository abstraction
- ❌ Mutable state → ✅ Immutable entities
- ❌ No DI → ✅ Centralized dependency management

**Result:** Professional, maintainable, testable architecture ready for production.

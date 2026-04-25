/// MIGRATION GUIDE: Updating ChannelProvider to Use Dependency Injection
/// 
/// This file demonstrates how to refactor the existing ChannelProvider
/// to use dependency injection instead of direct service access.

import 'package:flutter/foundation.dart';
import 'package:tv_viewer/di/service_locator.dart';
import 'package:tv_viewer/models/channel.dart';
import 'package:tv_viewer/repositories/channel_repository.dart';
import 'package:tv_viewer/utils/logger_service.dart';

/// Updated ChannelProvider using dependency injection
/// 
/// Key changes:
/// 1. Inject ChannelRepository instead of using M3UService directly
/// 2. Inject LoggerService from getIt
/// 3. Use repository methods instead of service methods
class ChannelProviderWithDI extends ChangeNotifier {
  // ✅ CHANGE: Inject dependencies via getIt
  final ChannelRepository _repository;
  final LoggerService _logger;
  
  // Constructor injection from service locator
  ChannelProviderWithDI()
      : _repository = getIt<ChannelRepository>(),
        _logger = getIt<LoggerService>();

  List<Channel> _channels = [];
  List<Channel> _filteredChannels = [];
  Set<String> _categories = {};
  Set<String> _countries = {};
  Set<String> _favoriteUrls = {};
  String _selectedCategory = 'All';
  String _selectedCountry = 'All';
  String _searchQuery = '';
  bool _isLoading = false;

  // Getters
  List<Channel> get channels => _filteredChannels;
  List<String> get categories => ['All', 'Favorites', ..._categories.toList()..sort()];
  List<String> get countries => ['All', ..._countries.toList()..sort()];
  String get selectedCategory => _selectedCategory;
  String get selectedCountry => _selectedCountry;
  String get searchQuery => _searchQuery;
  bool get isLoading => _isLoading;
  int get totalChannels => _channels.length;
  int get favoritesCount => _favoriteUrls.length;

  /// Load channels from cache or fetch new
  Future<void> loadChannels() async {
    _logger.info('Loading channels...');
    _isLoading = true;
    notifyListeners();

    // ✅ CHANGE: Load favorites using repository
    await _loadFavorites();

    // ✅ CHANGE: Try cache using repository
    final cached = await _repository.getCachedChannels();
    
    if (cached.isNotEmpty) {
      _logger.info('Loaded ${cached.length} channels from cache');
      _channels = cached;
      _updateCategories();
      _applyFilters();
      _isLoading = false;
      notifyListeners();

      // Fetch updates in background
      _fetchChannelsInBackground();
    } else {
      _logger.info('No cached channels found, fetching fresh data');
      await fetchChannels();
    }
  }

  /// Fetch channels from repositories
  Future<void> fetchChannels() async {
    _logger.info('Fetching channels from repositories...');
    _isLoading = true;
    notifyListeners();

    try {
      // ✅ CHANGE: Use repository instead of M3UService
      final channels = await _repository.fetchChannels(
        onProgress: (current, total) {
          _logger.debug('Fetching: $current/$total');
        },
      );

      _logger.info('Successfully fetched ${channels.length} channels');
      _channels = channels;
      _updateCategories();
      _applyFilters();
      
      // ✅ CHANGE: Cache using repository
      await _repository.cacheChannels(_channels);
    } catch (e, stackTrace) {
      _logger.error('Error fetching channels', e, stackTrace);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Background fetch
  void _fetchChannelsInBackground() async {
    _logger.debug('Starting background channel fetch...');
    try {
      // ✅ CHANGE: Use repository
      final channels = await _repository.fetchChannels();
      
      if (channels.length > _channels.length) {
        _logger.info('Background fetch found ${channels.length - _channels.length} new channels');
        _channels = channels;
        _updateCategories();
        _applyFilters();
        await _repository.cacheChannels(_channels);
        notifyListeners();
      }
    } catch (e, stackTrace) {
      _logger.error('Background fetch error', e, stackTrace);
    }
  }

  /// Check if a channel is favorited
  bool isFavorite(Channel channel) {
    return _favoriteUrls.contains(channel.url);
  }

  /// Toggle favorite status for a channel
  Future<void> toggleFavorite(Channel channel) async {
    // ✅ CHANGE: Use repository for favorites
    final currentlyFavorite = await _repository.isFavorite(channel.url);
    
    if (currentlyFavorite) {
      final success = await _repository.removeFavorite(channel.url);
      if (success) {
        _favoriteUrls.remove(channel.url);
        _logger.info('Removed favorite: ${channel.name}');
      }
    } else {
      final success = await _repository.addFavorite(channel.url);
      if (success) {
        _favoriteUrls.add(channel.url);
        _logger.info('Added favorite: ${channel.name}');
      }
    }
    
    // If currently viewing favorites, reapply filters
    if (_selectedCategory == 'Favorites') {
      _applyFilters();
    }
    
    notifyListeners();
  }

  /// Load favorites from persistent storage
  Future<void> _loadFavorites() async {
    // ✅ CHANGE: Use repository
    _favoriteUrls = await _repository.getFavorites();
    _logger.debug('Loaded ${_favoriteUrls.length} favorites');
  }

  /// Validate a specific channel
  Future<bool> validateChannel(Channel channel) async {
    // ✅ CHANGE: Use repository
    return await _repository.validateChannelStream(channel.url);
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

  /// Set search query
  void setSearchQuery(String query) {
    _searchQuery = query;
    _applyFilters();
    notifyListeners();
  }

  /// Clear all filters
  void clearFilters() {
    _selectedCategory = 'All';
    _selectedCountry = 'All';
    _searchQuery = '';
    _applyFilters();
    notifyListeners();
  }

  /// Check if any filters are active
  bool get hasActiveFilters {
    return _selectedCategory != 'All' ||
        _selectedCountry != 'All' ||
        _searchQuery.isNotEmpty;
  }

  /// Export channels as M3U (working channels only)
  String exportAsM3U() {
    final buffer = StringBuffer();
    buffer.writeln('#EXTM3U');

    for (final channel in workingChannels) {
      buffer.writeln(
          '#EXTINF:-1 group-title="${channel.category ?? 'Other'}",${channel.name}');
      buffer.writeln(channel.url);
    }

    return buffer.toString();
  }

  /// Get working channels only
  List<Channel> get workingChannels =>
      _filteredChannels.where((c) => c.isWorking).toList();

  /// Get all favorite channels
  List<Channel> get favoriteChannels =>
      _channels.where((c) => _favoriteUrls.contains(c.url)).toList();

  // Private helper methods
  void _updateCategories() {
    _categories = _channels
        .map((c) => c.category ?? 'Other')
        .where((c) => c.isNotEmpty)
        .toSet();
    _countries = _channels
        .map((c) => c.country ?? 'Unknown')
        .where((c) => c.isNotEmpty && c != 'Unknown')
        .toSet();
  }

  void _applyFilters() {
    _filteredChannels = _channels.where((channel) {
      // Favorites filter
      if (_selectedCategory == 'Favorites') {
        if (!_favoriteUrls.contains(channel.url)) return false;
      }
      // Category filter
      else if (_selectedCategory != 'All') {
        if ((channel.category ?? 'Other') != _selectedCategory) return false;
      }
      
      // Country filter
      if (_selectedCountry != 'All') {
        if ((channel.country ?? 'Unknown') != _selectedCountry) return false;
      }

      // Search filter
      if (_searchQuery.isNotEmpty) {
        final query = _searchQuery.toLowerCase();
        if (!channel.name.toLowerCase().contains(query)) return false;
      }

      return true;
    }).toList();
  }
}

// ============================================================================
// COMPARISON SUMMARY
// ============================================================================

/// KEY CHANGES:
/// 
/// 1. INJECT DEPENDENCIES:
///    Before: Using static services directly (M3UService, FavoritesService)
///    After:  Inject ChannelRepository and LoggerService via getIt
/// 
/// 2. USE REPOSITORY METHODS:
///    Before: M3UService.fetchAllChannels()
///    After:  _repository.fetchChannels()
/// 
/// 3. USE REPOSITORY FOR FAVORITES:
///    Before: FavoritesService.addFavorite()
///    After:  _repository.addFavorite()
/// 
/// 4. USE REPOSITORY FOR CACHE:
///    Before: SharedPreferences directly
///    After:  _repository.getCachedChannels() / cacheChannels()
/// 
/// 5. CONSISTENT LOGGING:
///    Before: logger.info() (global instance)
///    After:  _logger.info() (injected instance)
/// 
/// BENEFITS:
/// - ✅ Easier to test (mock the repository)
/// - ✅ Loose coupling (provider doesn't know about M3U, SharedPreferences, etc.)
/// - ✅ Single responsibility (provider manages state, repository manages data)
/// - ✅ Consistent pattern across the app
/// - ✅ Easy to swap implementations
/// 
/// MIGRATION STEPS:
/// 1. Update constructor to inject dependencies
/// 2. Replace M3UService calls with repository.fetchChannels()
/// 3. Replace FavoritesService calls with repository favorites methods
/// 4. Replace SharedPreferences with repository cache methods
/// 5. Update any direct service calls to use injected instances
/// 6. Test thoroughly!

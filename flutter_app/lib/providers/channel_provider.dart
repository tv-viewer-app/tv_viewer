import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/channel.dart';
import '../services/m3u_service.dart';
import '../services/favorites_service.dart';
import '../utils/logger_service.dart';

/// Provider for managing channel state
class ChannelProvider extends ChangeNotifier {
  List<Channel> _channels = [];
  List<Channel> _filteredChannels = [];
  Set<String> _categories = {};
  Set<String> _countries = {};
  Set<String> _languages = {}; // BL-017: Language filter
  Set<String> _favoriteUrls = {}; // Track favorite channel URLs
  String _selectedCategory = 'All';
  String _selectedCountry = 'All';
  String _selectedLanguage = 'All'; // BL-017: Language filter
  String _selectedMediaType = 'All'; // 'All', 'TV', or 'Radio'
  String _searchQuery = '';
  bool _isLoading = false;
  bool _isScanning = false;
  int _scanProgress = 0;
  int _scanTotal = 0;
  int _workingCount = 0;
  int _failedCount = 0;

  // Getters
  List<Channel> get channels => _filteredChannels;
  List<String> get categories => ['All', 'Favorites', ..._categories.toList()..sort()];
  List<String> get countries => ['All', ..._countries.toList()..sort()];
  List<String> get languages => ['All', ..._languages.toList()..sort()]; // BL-017
  List<String> get mediaTypes => ['All', 'TV', 'Radio'];
  String get selectedCategory => _selectedCategory;
  String get selectedCountry => _selectedCountry;
  String get selectedLanguage => _selectedLanguage; // BL-017
  String get selectedMediaType => _selectedMediaType;
  String get searchQuery => _searchQuery;
  bool get isLoading => _isLoading;
  bool get isScanning => _isScanning;
  int get scanProgress => _scanProgress;
  int get scanTotal => _scanTotal;
  int get workingCount => _workingCount;
  int get failedCount => _failedCount;
  int get totalChannels => _channels.length;
  int get favoritesCount => _favoriteUrls.length;


  /// Load channels from cache or fetch new
  Future<void> loadChannels() async {
    logger.info('Loading channels...');
    _isLoading = true;
    notifyListeners();

    // Load favorites first
    await _loadFavorites();

    // Try to load from cache first
    final cached = await _loadFromCache();
    if (cached.isNotEmpty) {
      logger.info('Loaded ${cached.length} channels from cache');
      _channels = cached;
      _updateCategories();
      _applyFilters();
      _isLoading = false;
      notifyListeners();

      // Fetch updates in background
      _fetchChannelsInBackground();
    } else {
      logger.info('No cached channels found, fetching fresh data');
      // No cache, fetch fresh
      await fetchChannels();
    }
  }

  /// Fetch channels from repositories
  Future<void> fetchChannels() async {
    logger.info('Fetching channels from repositories...');
    _isLoading = true;
    notifyListeners();

    try {
      final channels = await M3UService.fetchAllChannels(
        onProgress: (current, total) {
          // Could add progress indicator here
        },
      );

      logger.info('Successfully fetched ${channels.length} channels');
      _channels = channels;
      _updateCategories();
      _applyFilters();
      await _saveToCache();
    } catch (e, stackTrace) {
      logger.error('Error fetching channels', e, stackTrace);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void _fetchChannelsInBackground() async {
    logger.debug('Starting background channel fetch...');
    try {
      final channels = await M3UService.fetchAllChannels();
      if (channels.length > _channels.length) {
        logger.info('Background fetch found ${channels.length - _channels.length} new channels');
        _channels = channels;
        _updateCategories();
        _applyFilters();
        await _saveToCache();
        notifyListeners();
      } else {
        logger.debug('Background fetch completed, no new channels');
      }
    } catch (e, stackTrace) {
      logger.error('Background fetch error', e, stackTrace);
    }
  }

  /// Validate channels (check if streams are working)
  Future<void> validateChannels() async {
    if (_isScanning) return;

    logger.info('Starting channel validation for ${_channels.length} channels');
    _isScanning = true;
    _scanProgress = 0;
    _scanTotal = _channels.length;
    _workingCount = 0;
    _failedCount = 0;
    notifyListeners();

    // Validate in batches of 5 for performance
    const batchSize = 5;
    for (int i = 0; i < _channels.length; i += batchSize) {
      if (!_isScanning) break; // Allow cancellation

      final batch = _channels.skip(i).take(batchSize).toList();
      
      // Collect results from batch before updating state (BL-031: immutable)
      final updatedChannels = <Channel>[];
      int batchWorking = 0;
      int batchFailed = 0;
      
      await Future.wait(
        batch.map((channel) async {
          final isWorking = await M3UService.checkStream(channel.url);
          final updated = channel.copyWith(
            isWorking: isWorking,
            lastChecked: DateTime.now(),
          );
          updatedChannels.add(updated);

          if (isWorking) {
            batchWorking++;
          } else {
            batchFailed++;
          }
        }),
      );
      
      // Update channels list with new instances (BL-031: immutable pattern)
      for (var updated in updatedChannels) {
        final index = _channels.indexWhere((c) => c.url == updated.url);
        if (index != -1) {
          _channels[index] = updated;
        }
      }
      
      // Update state once after batch completes
      _workingCount += batchWorking;
      _failedCount += batchFailed;
      _scanProgress += batch.length;
      notifyListeners();

      // Small delay to prevent overwhelming
      await Future.delayed(const Duration(milliseconds: 50));
    }

    _isScanning = false;
    logger.info('Channel validation completed: $_workingCount working, $_failedCount failed');
    await _saveToCache();
    notifyListeners();
  }

  /// Stop validation
  void stopValidation() {
    _isScanning = false;
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
  
  /// BL-017: Set language filter
  void setLanguage(String language) {
    _selectedLanguage = language;
    _applyFilters();
    notifyListeners();
  }
  
  /// Set media type filter (TV/Radio)
  void setMediaType(String mediaType) {
    _selectedMediaType = mediaType;
    _applyFilters();
    notifyListeners();
  }

  /// Set search query
  void setSearchQuery(String query) {
    _searchQuery = query;
    _applyFilters();
    notifyListeners();
  }

  /// Clear all filters (BL-008)
  void clearFilters() {
    _selectedCategory = 'All';
    _selectedCountry = 'All';
    _selectedLanguage = 'All';
    _selectedMediaType = 'All';
    _searchQuery = '';
    _applyFilters();
    notifyListeners();
  }

  /// Check if any filters are active (BL-008)
  bool get hasActiveFilters {
    return _selectedCategory != 'All' ||
        _selectedCountry != 'All' ||
        _selectedLanguage != 'All' ||
        _selectedMediaType != 'All' ||
        _searchQuery.isNotEmpty;
  }

  void _updateCategories() {
    _categories = _channels
        .map((c) => c.category ?? 'Other')
        .where((c) => c.isNotEmpty)
        .toSet();
    _countries = _channels
        .map((c) => c.country ?? 'Unknown')
        .where((c) => c.isNotEmpty && c != 'Unknown')
        .toSet();
    // BL-017: Extract languages
    _languages = _channels
        .map((c) => c.language ?? 'Unknown')
        .where((c) => c.isNotEmpty && c != 'Unknown')
        .toSet();
  }

  void _applyFilters() {
    _filteredChannels = _channels.where((channel) {
      // Favorites filter (special category)
      if (_selectedCategory == 'Favorites') {
        if (!_favoriteUrls.contains(channel.url)) {
          return false;
        }
      }
      // Category filter
      else if (_selectedCategory != 'All') {
        if ((channel.category ?? 'Other') != _selectedCategory) {
          return false;
        }
      }
      
      // Country filter
      if (_selectedCountry != 'All') {
        if ((channel.country ?? 'Unknown') != _selectedCountry) {
          return false;
        }
      }
      
      // BL-017: Language filter
      if (_selectedLanguage != 'All') {
        if ((channel.language ?? 'Unknown') != _selectedLanguage) {
          return false;
        }
      }
      
      // Media type filter
      if (_selectedMediaType != 'All') {
        if (channel.mediaType != _selectedMediaType) {
          return false;
        }
      }

      // Search filter
      if (_searchQuery.isNotEmpty) {
        final query = _searchQuery.toLowerCase();
        if (!channel.name.toLowerCase().contains(query)) {
          return false;
        }
      }

      return true;
    }).toList();
  }

  Future<List<Channel>> _loadFromCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final json = prefs.getString('channels_cache');
      if (json != null) {
        final List<dynamic> data = jsonDecode(json);
        return data.map((e) => Channel.fromJson(e)).toList();
      }
    } catch (e, stackTrace) {
      logger.error('Error loading cache', e, stackTrace);
    }
    return [];
  }

  Future<void> _saveToCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final json = jsonEncode(_channels.map((c) => c.toJson()).toList());
      await prefs.setString('channels_cache', json);
      logger.debug('Saved ${_channels.length} channels to cache');
    } catch (e, stackTrace) {
      logger.error('Error saving cache', e, stackTrace);
    }
  }

  /// Get working channels only
  List<Channel> get workingChannels =>
      _filteredChannels.where((c) => c.isWorking).toList();

  /// Export channels as M3U
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

  // ========== Favorites Management ==========

  /// Check if a channel is favorited
  bool isFavorite(Channel channel) {
    return _favoriteUrls.contains(channel.url);
  }

  /// Toggle favorite status for a channel
  Future<void> toggleFavorite(Channel channel) async {
    if (_favoriteUrls.contains(channel.url)) {
      _favoriteUrls.remove(channel.url);
      await FavoritesService.removeFavorite(channel.url);
    } else {
      _favoriteUrls.add(channel.url);
      await FavoritesService.addFavorite(channel.url);
    }
    
    // If currently viewing favorites, reapply filters
    if (_selectedCategory == 'Favorites') {
      _applyFilters();
    }
    
    notifyListeners();
  }

  /// Load favorites from persistent storage
  Future<void> _loadFavorites() async {
    _favoriteUrls = await FavoritesService.loadFavorites();
  }

  /// Get all favorite channels
  List<Channel> get favoriteChannels =>
      _channels.where((c) => _favoriteUrls.contains(c.url)).toList();
}

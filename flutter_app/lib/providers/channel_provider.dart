import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/channel.dart';
import '../services/m3u_service.dart';

/// Provider for managing channel state
class ChannelProvider extends ChangeNotifier {
  List<Channel> _channels = [];
  List<Channel> _filteredChannels = [];
  Set<String> _categories = {};
  Set<String> _countries = {};
  String _selectedCategory = 'All';
  String _selectedCountry = 'All';
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
  List<String> get categories => ['All', ..._categories.toList()..sort()];
  List<String> get countries => ['All', ..._countries.toList()..sort()];
  List<String> get mediaTypes => ['All', 'TV', 'Radio'];
  String get selectedCategory => _selectedCategory;
  String get selectedCountry => _selectedCountry;
  String get selectedMediaType => _selectedMediaType;
  String get searchQuery => _searchQuery;
  bool get isLoading => _isLoading;
  bool get isScanning => _isScanning;
  int get scanProgress => _scanProgress;
  int get scanTotal => _scanTotal;
  int get workingCount => _workingCount;
  int get failedCount => _failedCount;
  int get totalChannels => _channels.length;

  /// Load channels from cache or fetch new
  Future<void> loadChannels() async {
    _isLoading = true;
    notifyListeners();

    // Try to load from cache first
    final cached = await _loadFromCache();
    if (cached.isNotEmpty) {
      _channels = cached;
      _updateCategories();
      _applyFilters();
      _isLoading = false;
      notifyListeners();

      // Fetch updates in background
      _fetchChannelsInBackground();
    } else {
      // No cache, fetch fresh
      await fetchChannels();
    }
  }

  /// Fetch channels from repositories
  Future<void> fetchChannels() async {
    _isLoading = true;
    notifyListeners();

    try {
      final channels = await M3UService.fetchAllChannels(
        onProgress: (current, total) {
          // Could add progress indicator here
        },
      );

      _channels = channels;
      _updateCategories();
      _applyFilters();
      await _saveToCache();
    } catch (e) {
      debugPrint('Error fetching channels: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void _fetchChannelsInBackground() async {
    try {
      final channels = await M3UService.fetchAllChannels();
      if (channels.length > _channels.length) {
        _channels = channels;
        _updateCategories();
        _applyFilters();
        await _saveToCache();
        notifyListeners();
      }
    } catch (e) {
      debugPrint('Background fetch error: $e');
    }
  }

  /// Validate channels (check if streams are working)
  Future<void> validateChannels() async {
    if (_isScanning) return;

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
      
      // Collect results from batch before updating state
      int batchWorking = 0;
      int batchFailed = 0;
      
      await Future.wait(
        batch.map((channel) async {
          final isWorking = await M3UService.checkStream(channel.url);
          channel.isWorking = isWorking;
          channel.lastChecked = DateTime.now();

          if (isWorking) {
            batchWorking++;
          } else {
            batchFailed++;
          }
        }),
      );
      
      // Update state once after batch completes (fixes race condition)
      _workingCount += batchWorking;
      _failedCount += batchFailed;
      _scanProgress += batch.length;
      notifyListeners();

      // Small delay to prevent overwhelming
      await Future.delayed(const Duration(milliseconds: 50));
    }

    _isScanning = false;
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
      // Category filter
      if (_selectedCategory != 'All') {
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
    } catch (e) {
      debugPrint('Error loading cache: $e');
    }
    return [];
  }

  Future<void> _saveToCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final json = jsonEncode(_channels.map((c) => c.toJson()).toList());
      await prefs.setString('channels_cache', json);
    } catch (e) {
      debugPrint('Error saving cache: $e');
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
}

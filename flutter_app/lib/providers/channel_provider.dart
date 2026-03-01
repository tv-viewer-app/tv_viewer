import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/channel.dart';
import '../services/m3u_service.dart';
import '../services/favorites_service.dart';
import '../services/shared_db_service.dart';
import '../utils/logger_service.dart';

/// Provider for managing channel state
class ChannelProvider extends ChangeNotifier {
  // ISO/common language code → display name mapping
  static const _langNormalize = {
    'heb': 'Hebrew', 'he': 'Hebrew', 'hebrew': 'Hebrew',
    'eng': 'English', 'en': 'English', 'english': 'English',
    'ara': 'Arabic', 'ar': 'Arabic', 'arabic': 'Arabic',
    'spa': 'Spanish', 'es': 'Spanish', 'spanish': 'Spanish',
    'fra': 'French', 'fr': 'French', 'french': 'French',
    'deu': 'German', 'de': 'German', 'german': 'German',
    'ita': 'Italian', 'it': 'Italian', 'italian': 'Italian',
    'por': 'Portuguese', 'pt': 'Portuguese', 'portuguese': 'Portuguese',
    'rus': 'Russian', 'ru': 'Russian', 'russian': 'Russian',
    'tur': 'Turkish', 'tr': 'Turkish', 'turkish': 'Turkish',
    'pol': 'Polish', 'pl': 'Polish', 'polish': 'Polish',
    'zho': 'Chinese', 'zh': 'Chinese', 'chinese': 'Chinese',
    'jpn': 'Japanese', 'ja': 'Japanese', 'japanese': 'Japanese',
    'kor': 'Korean', 'ko': 'Korean', 'korean': 'Korean',
    'hin': 'Hindi', 'hi': 'Hindi', 'hindi': 'Hindi',
    'nld': 'Dutch', 'nl': 'Dutch', 'dutch': 'Dutch',
    'ell': 'Greek', 'el': 'Greek', 'greek': 'Greek',
    'tha': 'Thai', 'th': 'Thai', 'thai': 'Thai',
    'vie': 'Vietnamese', 'vi': 'Vietnamese', 'vietnamese': 'Vietnamese',
    'ind': 'Indonesian', 'id': 'Indonesian', 'indonesian': 'Indonesian',
    'msa': 'Malay', 'ms': 'Malay', 'malay': 'Malay',
    'fil': 'Filipino', 'tl': 'Filipino', 'filipino': 'Filipino',
    'fas': 'Persian', 'fa': 'Persian', 'persian': 'Persian', 'farsi': 'Persian',
    'urd': 'Urdu', 'ur': 'Urdu', 'urdu': 'Urdu',
    'swe': 'Swedish', 'sv': 'Swedish', 'swedish': 'Swedish',
    'nor': 'Norwegian', 'no': 'Norwegian', 'norwegian': 'Norwegian',
    'dan': 'Danish', 'da': 'Danish', 'danish': 'Danish',
    'fin': 'Finnish', 'fi': 'Finnish', 'finnish': 'Finnish',
    'ron': 'Romanian', 'ro': 'Romanian', 'romanian': 'Romanian',
    'hun': 'Hungarian', 'hu': 'Hungarian', 'hungarian': 'Hungarian',
    'ces': 'Czech', 'cs': 'Czech', 'czech': 'Czech',
    'slk': 'Slovak', 'sk': 'Slovak', 'slovak': 'Slovak',
    'bul': 'Bulgarian', 'bg': 'Bulgarian', 'bulgarian': 'Bulgarian',
    'ukr': 'Ukrainian', 'uk': 'Ukrainian', 'ukrainian': 'Ukrainian',
    'srp': 'Serbian', 'sr': 'Serbian', 'serbian': 'Serbian',
    'hrv': 'Croatian', 'hr': 'Croatian', 'croatian': 'Croatian',
    'cat': 'Catalan', 'ca': 'Catalan', 'catalan': 'Catalan',
    'tam': 'Tamil', 'ta': 'Tamil', 'tamil': 'Tamil',
    'tel': 'Telugu', 'te': 'Telugu', 'telugu': 'Telugu',
    'ben': 'Bengali', 'bn': 'Bengali', 'bengali': 'Bengali', 'bangla': 'Bengali',
    'pan': 'Punjabi', 'pa': 'Punjabi', 'punjabi': 'Punjabi',
    'guj': 'Gujarati', 'gu': 'Gujarati', 'gujarati': 'Gujarati',
    'mar': 'Marathi', 'mr': 'Marathi', 'marathi': 'Marathi',
    'mal': 'Malayalam', 'ml': 'Malayalam', 'malayalam': 'Malayalam',
    'kan': 'Kannada', 'kn': 'Kannada', 'kannada': 'Kannada',
    'pus': 'Pashto', 'ps': 'Pashto', 'pashto': 'Pashto',
    'kur': 'Kurdish', 'ku': 'Kurdish', 'kurdish': 'Kurdish',
    'som': 'Somali', 'so': 'Somali', 'somali': 'Somali',
    'amh': 'Amharic', 'am': 'Amharic', 'amharic': 'Amharic',
  };

  static String _normalizeLanguage(String raw) {
    final key = raw.toLowerCase().trim();
    if (key.contains(';')) return _normalizeLanguage(raw.split(';').first);
    return _langNormalize[key] ?? (raw[0].toUpperCase() + raw.substring(1).toLowerCase());
  }

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
  String _selectedStatus = 'All'; // 'All', 'Working', 'Failed', 'Unchecked'
  String _searchQuery = '';
  bool _isLoading = false;
  bool _isScanning = false;
  bool _isOffline = false; // #41: Offline state tracking
  bool _showFavoritesOnly = false; // Dedicated favorites toggle
  String _errorMessage = ''; // #41: User-facing error message
  int _scanProgress = 0;
  int _scanTotal = 0;
  int _workingCount = 0;
  int _failedCount = 0;

  // Getters
  List<Channel> get channels => _filteredChannels;
  List<String> get categories => ['All', ..._categories.toList()..sort()];
  List<String> get countries => ['All', ..._countries.toList()..sort()];
  List<String> get languages => ['All', ..._languages.toList()..sort()]; // BL-017
  List<String> get mediaTypes => ['All', 'TV', 'Radio'];
  List<String> get statusOptions => ['All', 'Working', 'Failed', 'Unchecked'];
  String get selectedCategory => _selectedCategory;
  String get selectedCountry => _selectedCountry;
  String get selectedLanguage => _selectedLanguage; // BL-017
  String get selectedMediaType => _selectedMediaType;
  String get selectedStatus => _selectedStatus;
  String get searchQuery => _searchQuery;
  bool get isLoading => _isLoading;
  bool get isScanning => _isScanning;
  bool get isOffline => _isOffline; // #41
  bool get showFavoritesOnly => _showFavoritesOnly;
  String get errorMessage => _errorMessage; // #41
  int get scanProgress => _scanProgress;
  int get scanTotal => _scanTotal;
  int get workingCount => _workingCount;
  int get failedCount => _failedCount;
  int get totalChannels => _channels.length;
  int get favoritesCount => _favoriteUrls.length;


  /// Check network connectivity (#41)
  Future<bool> _hasConnectivity() async {
    try {
      final result = await Connectivity().checkConnectivity();
      final online = !result.contains(ConnectivityResult.none);
      if (_isOffline != !online) {
        _isOffline = !online;
        notifyListeners();
      }
      return online;
    } catch (e) {
      logger.error('Connectivity check failed', e);
      return true; // Assume online if check fails
    }
  }

  /// Clear error message
  void clearError() {
    _errorMessage = '';
    notifyListeners();
  }

  /// Load channels from cache or fetch new
  Future<void> loadChannels() async {
    logger.info('Loading channels...');
    _isLoading = true;
    _errorMessage = '';
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

      // #41: Check connectivity before background fetch
      if (await _hasConnectivity()) {
        _fetchChannelsInBackground();
      } else {
        _errorMessage = 'Offline — showing cached channels';
        logger.info('Offline: using ${cached.length} cached channels');
        notifyListeners();
      }
    } else {
      // #41: No cache — check connectivity before fetching
      if (await _hasConnectivity()) {
        logger.info('No cached channels found, fetching fresh data');
        await fetchChannels();
      } else {
        _isOffline = true;
        _isLoading = false;
        _errorMessage = 'No internet connection. Connect to WiFi or mobile data and retry.';
        logger.warning('Offline with no cache — cannot load channels');
        notifyListeners();
      }
    }
  }

  /// Fetch channels from repositories
  Future<void> fetchChannels() async {
    logger.info('Fetching channels from repositories...');
    _isLoading = true;
    _errorMessage = '';
    notifyListeners();

    // #41: Check connectivity before network operations
    if (!await _hasConnectivity()) {
      _isLoading = false;
      _errorMessage = 'No internet connection. Please check your network and try again.';
      notifyListeners();
      return;
    }

    try {
      final channels = await M3UService.fetchAllChannels(
        onProgress: (current, total) {
          // Could add progress indicator here
        },
      );

      logger.info('Successfully fetched ${channels.length} channels');
      _channels = channels;
      _isOffline = false;
      _errorMessage = '';
      _updateCategories();
      _applyFilters();
      await _saveToCache();
    } catch (e, stackTrace) {
      logger.error('Error fetching channels', e, stackTrace);
      _errorMessage = 'Failed to load channels. Using cached data if available.';
      // #41: Fall back to cache on fetch failure
      if (_channels.isEmpty) {
        final cached = await _loadFromCache();
        if (cached.isNotEmpty) {
          _channels = cached;
          _updateCategories();
          _applyFilters();
          _errorMessage = 'Network error — showing cached channels';
        } else {
          _errorMessage = 'Could not load channels. Check your connection and retry.';
        }
      }
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void _fetchChannelsInBackground() async {
    logger.debug('Starting background channel fetch...');
    // #41: Skip background fetch if offline
    if (!await _hasConnectivity()) {
      logger.debug('Skipping background fetch — offline');
      return;
    }
    try {
      final channels = await M3UService.fetchAllChannels();
      if (channels.length > _channels.length) {
        logger.info('Background fetch found ${channels.length - _channels.length} new channels');
        _channels = channels;
        _isOffline = false;
        _errorMessage = '';
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

    // #41: Check connectivity before validation
    if (!await _hasConnectivity()) {
      _errorMessage = 'Cannot validate channels while offline';
      notifyListeners();
      return;
    }

    logger.info('Starting channel validation for ${_channels.length} channels');
    _isScanning = true;
    _scanProgress = 0;
    _scanTotal = _channels.length;
    _workingCount = 0;
    _failedCount = 0;
    notifyListeners();

    // --- SharedDb: Fetch cached results to skip recently-validated channels ---
    final sharedDb = SharedDbService();
    final Set<String> skippedUrls = {};
    try {
      if (SharedDbService.isConfigured) {
        final sharedDbCache = await sharedDb.fetchRecentResults();
        if (sharedDbCache.isNotEmpty) {
          for (int j = 0; j < _channels.length; j++) {
            if (sharedDb.shouldSkipValidation(_channels[j].url, sharedDbCache)) {
              _channels[j] = _channels[j].copyWith(
                isWorking: true,
                lastChecked: DateTime.now(),
              );
              skippedUrls.add(_channels[j].url);
              _workingCount++;
              _scanProgress++;
            }
          }
          if (skippedUrls.isNotEmpty) {
            logger.info(
              'SharedDb: Skipped ${skippedUrls.length}/${_channels.length} channels '
              'with cached working status',
            );
            notifyListeners();
          }
        }
      }
    } catch (e) {
      logger.warning('SharedDb: Failed to fetch cached results: $e');
      // Reset counters on failure — all channels will be validated normally
      _workingCount = 0;
      _failedCount = 0;
      _scanProgress = 0;
      skippedUrls.clear();
    }
    // Channels that still need validation (excludes SharedDb-cached working channels)
    final channelsToValidate = skippedUrls.isNotEmpty
        ? _channels.where((c) => !skippedUrls.contains(c.url)).toList()
        : _channels;
    // --- End SharedDb fetch ---

    // Validate in batches of 5 for performance
    const batchSize = 5;
    for (int i = 0; i < channelsToValidate.length; i += batchSize) {
      if (!_isScanning) break; // Allow cancellation

      final batch = channelsToValidate.skip(i).take(batchSize).toList();
      
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

    // --- SharedDb: Upload results for channels that were actually validated ---
    try {
      if (SharedDbService.isConfigured) {
        final uploadResults = _channels
            .where((c) => c.url.startsWith('http') && !skippedUrls.contains(c.url))
            .map((c) => ChannelResult(
                  url: c.url,
                  isWorking: c.isWorking,
                  lastChecked: c.lastChecked ?? DateTime.now(),
                ))
            .toList();
        if (uploadResults.isNotEmpty) {
          await sharedDb.uploadResults(uploadResults);
        }
      }
    } catch (e) {
      logger.warning('SharedDb: Failed to upload results: $e');
    }
    // --- End SharedDb upload ---

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

  /// Set channel status filter (Working/Failed/Unchecked)
  void setStatus(String status) {
    _selectedStatus = status;
    _applyFilters();
    notifyListeners();
  }

  /// Toggle favorites-only filter
  void toggleFavoritesFilter() {
    _showFavoritesOnly = !_showFavoritesOnly;
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
    _selectedStatus = 'All';
    _showFavoritesOnly = false;
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
        _selectedStatus != 'All' ||
        _showFavoritesOnly ||
        _searchQuery.isNotEmpty;
  }

  /// Known content categories — anything else in group-title is likely a country name
  static const _knownCategories = {
    'Animation', 'Auto', 'Business', 'Classic', 'Comedy', 'Cooking',
    'Culture', 'Documentary', 'Education', 'Entertainment', 'Family',
    'General', 'Kids', 'Legislative', 'Lifestyle', 'Movies', 'Music',
    'News', 'Outdoor', 'Radio', 'Relax', 'Religious', 'Science',
    'Series', 'Shop', 'Sports', 'Travel', 'Weather', 'Xxx', 'Other',
    'Undefined', 'Fiction', 'Food', 'Health', 'History', 'Nature',
    'Technology', 'Gaming', 'Drama', 'Crime', 'Reality', 'Talk',
  };

  void _updateCategories() {
    // Separate real content categories from country names in group-title
    final rawCategories = _channels
        .map((c) => c.category ?? 'Other')
        .where((c) => c.isNotEmpty)
        .toSet();

    // Only include known content categories; filter out country names
    _categories = rawCategories.where((cat) {
      return _knownCategories.contains(cat) ||
          // Keep it if it's NOT a recognized country in our countries set
          // (short names < 4 chars are likely codes, keep them)
          cat.length <= 3;
    }).toSet();

    // If very few categories matched, fall back to all (some playlists use custom names)
    if (_categories.length < 3 && rawCategories.length > 3) {
      _categories = rawCategories;
    }

    _countries = _channels
        .map((c) => c.country ?? 'Unknown')
        .where((c) => c.isNotEmpty && c != 'Unknown')
        .toSet();
    // BL-017: Extract languages with normalization
    _languages = _channels
        .map((c) => c.language ?? 'Unknown')
        .where((c) => c.isNotEmpty && c != 'Unknown')
        .map(_normalizeLanguage)
        .toSet();
  }

  void _applyFilters() {
    _filteredChannels = _channels.where((channel) {
      // Favorites toggle (dedicated button)
      if (_showFavoritesOnly) {
        if (!_favoriteUrls.contains(channel.url)) {
          return false;
        }
      }

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
      
      // BL-017: Language filter (with normalization)
      if (_selectedLanguage != 'All') {
        final rawLang = channel.language ?? 'Unknown';
        final normalizedLang = _normalizeLanguage(rawLang);
        if (normalizedLang != _selectedLanguage) {
          return false;
        }
      }
      
      // Media type filter
      if (_selectedMediaType != 'All') {
        if (channel.mediaType != _selectedMediaType) {
          return false;
        }
      }

      // Channel status filter
      if (_selectedStatus == 'Working') {
        if (!(channel.isWorking && channel.lastChecked != null)) {
          return false;
        }
      } else if (_selectedStatus == 'Failed') {
        if (channel.isWorking || channel.lastChecked == null) {
          return false;
        }
      } else if (_selectedStatus == 'Unchecked') {
        if (channel.lastChecked != null) {
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

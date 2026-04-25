import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:package_info_plus/package_info_plus.dart';
import '../providers/channel_provider.dart';
import '../models/channel.dart';
import '../services/feedback_service.dart';
import '../services/onboarding_service.dart';
import '../services/analytics_service.dart';
import '../services/parental_controls_service.dart';
import '../services/watch_history_service.dart';
import '../widgets/channel_tile.dart';
import '../widgets/contribute_channel_dialog.dart';
import '../widgets/filter_dropdown.dart';
import '../widgets/pin_dialog.dart';
import '../widgets/scan_progress_bar.dart';
import '../widgets/onboarding_tooltip.dart';
import '../widgets/consent_dialog.dart';
import 'diagnostics_screen.dart';
import 'help_screen.dart';
import 'map_screen.dart';
import 'parental_settings_screen.dart';
import 'player_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _searchController = TextEditingController();
  
  // Keys for onboarding tooltips
  final GlobalKey _scanButtonKey = GlobalKey();
  final GlobalKey _filterAreaKey = GlobalKey();
  
  bool _hasShownOnboarding = false;
  int _currentTooltipIndex = 0;
  List<String> _tooltipsToShow = [];
  
  // Watch history
  List<Map<String, dynamic>> _recentChannels = [];

  // Tablet embedded player state
  Channel? _tabletSelectedChannel;
  int? _tabletSelectedIndex;

  @override
  void initState() {
    super.initState();
    // Load channels on startup
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _showConsentIfNeeded();
      context.read<ChannelProvider>().loadChannels();
      _loadRecentHistory();
      _checkRatingPrompt(); // BL-032: Check if we should show rating prompt
      _checkAndShowOnboarding();
    });
  }
  
  /// Show first-launch consent dialog if not yet shown.
  Future<void> _showConsentIfNeeded() async {
    if (!mounted) return;
    final needsConsent = await ConsentDialog.needsConsent();
    if (needsConsent && mounted) {
      final accepted = await ConsentDialog.show(context);
      if (!accepted && mounted) {
        // User declined — exit app
        Navigator.of(context).maybePop();
      }
    }
  }

  /// BL-032: Check and show rating prompt if needed
  Future<void> _checkRatingPrompt() async {
    final shouldShow = await FeedbackService.shouldShowRatingPrompt();
    if (shouldShow && mounted) {
      // Delay to avoid showing immediately on app launch
      Future.delayed(const Duration(seconds: 2), () {
        if (mounted) {
          FeedbackService.showRatingPrompt(context);
        }
      });
    }
  }
  
  /// Load recent watch history for the "Recently Played" section
  Future<void> _loadRecentHistory() async {
    final recent = await WatchHistoryService.getRecent(limit: 5);
    if (mounted) {
      setState(() {
        _recentChannels = recent;
      });
    }
  }
  
  Future<void> _checkAndShowOnboarding() async {
    if (_hasShownOnboarding) return;
    
    _tooltipsToShow = await OnboardingService.getTooltipsToShow();
    if (_tooltipsToShow.isNotEmpty && mounted) {
      _hasShownOnboarding = true;
      // Delay to ensure widgets are rendered
      await Future.delayed(const Duration(milliseconds: 800));
      if (mounted) {
        _showNextTooltip();
      }
    }
  }

  void _showNextTooltip() {
    if (_currentTooltipIndex >= _tooltipsToShow.length) {
      // All tooltips shown, mark onboarding as complete
      OnboardingService.completeOnboarding();
      return;
    }

    final tooltipId = _tooltipsToShow[_currentTooltipIndex];
    GlobalKey? targetKey;
    String message = '';
    ArrowPosition position = ArrowPosition.bottom;

    switch (tooltipId) {
      case 'scan_button':
        targetKey = _scanButtonKey;
        message = 'Tap to check which channels are working';
        position = ArrowPosition.top;
        break;
      case 'filter_area':
        targetKey = _filterAreaKey;
        message = 'Filter by category, country, or type';
        position = ArrowPosition.top;
        break;
      case 'favorite_button':
        // This will be shown on first channel tile (future enhancement)
        _currentTooltipIndex++;
        OnboardingService.markTooltipAsShown(tooltipId);
        _showNextTooltip();
        return;
    }

    if (targetKey != null && mounted) {
      OnboardingOverlay.show(
        context,
        message: message,
        targetKey: targetKey,
        arrowPosition: position,
        onDismiss: () {
          OnboardingService.markTooltipAsShown(tooltipId);
          _currentTooltipIndex++;
          Future.delayed(const Duration(milliseconds: 300), () {
            if (mounted) {
              _showNextTooltip();
            }
          });
        },
      );
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    OnboardingOverlay.dismiss();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final isTablet = screenWidth > 600;
    final isLandscape = MediaQuery.of(context).orientation == Orientation.landscape;
    return Scaffold(
      appBar: AppBar(
        title: const Text('📺 TV Viewer'),
        actions: [
          // Add Channel button
          IconButton(
            icon: const Icon(Icons.add_circle_outline),
            tooltip: 'Contribute Channel',
            onPressed: () => ContributeChannelDialog.show(context),
          ),
          // World Map button
          IconButton(
            icon: const Icon(Icons.map),
            tooltip: 'World Map',
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const MapScreen()),
            ),
          ),
          Consumer<ChannelProvider>(
            builder: (context, provider, _) {
              if (provider.isScanning) {
                return IconButton(
                  key: _scanButtonKey,
                  icon: const Icon(Icons.stop),
                  tooltip: 'Stop Scan',
                  onPressed: () => provider.stopValidation(),
                );
              }
              return IconButton(
                key: _scanButtonKey,
                icon: const Icon(Icons.refresh),
                tooltip: 'Scan Channels',
                onPressed: () => provider.validateChannels(),
              );
            },
          ),
          PopupMenuButton<String>(
            onSelected: (value) {
              if (value == 'help') {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const HelpScreen(),
                  ),
                );
              } else if (value == 'diagnostics') {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const DiagnosticsScreen(),
                  ),
                );
              } else if (value == 'parental') {
                _openParentalSettings();
              } else if (value == 'feedback') {
                FeedbackService.showFeedbackDialog(context);
              } else if (value == 'rate') {
                FeedbackService.openAppStore();
              } else if (value == 'about') {
                _showAboutDialog();
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'help',
                child: Row(
                  children: [
                    Icon(Icons.help_outline),
                    SizedBox(width: 8),
                    Text('Help & Support'),
                  ],
                ),
              ),
              const PopupMenuDivider(),
              const PopupMenuItem(
                value: 'parental',
                child: Row(
                  children: [
                    Icon(Icons.lock),
                    SizedBox(width: 8),
                    Text('Parental Controls'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'diagnostics',
                child: Row(
                  children: [
                    Icon(Icons.bug_report),
                    SizedBox(width: 8),
                    Text('Diagnostics'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'feedback',
                child: Row(
                  children: [
                    Icon(Icons.feedback),
                    SizedBox(width: 8),
                    Text('Send Feedback'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'rate',
                child: Row(
                  children: [
                    Icon(Icons.star),
                    SizedBox(width: 8),
                    Text('Rate App'),
                  ],
                ),
              ),
              const PopupMenuDivider(),
              const PopupMenuItem(
                value: 'about',
                child: Row(
                  children: [
                    Icon(Icons.info),
                    SizedBox(width: 8),
                    Text('About'),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: isTablet && isLandscape
          ? _buildTabletLandscapeBody()
          : isTablet && !isLandscape
              ? _buildTabletPortraitBody()
              : isLandscape
                  ? _buildLandscapeBody()
                  : _buildPortraitBody(),
    );
  }

  /// Builds the scan progress bar widget.
  Widget _buildScanProgress() {
    return Consumer<ChannelProvider>(
      builder: (context, provider, _) {
        if (provider.isScanning) {
          return ScanProgressBar(
            progress: provider.scanProgress,
            total: provider.scanTotal,
            workingCount: provider.workingCount,
            failedCount: provider.failedCount,
          );
        }
        return const SizedBox.shrink();
      },
    );
  }

  /// Builds the error / offline banner widget.
  Widget _buildErrorBanner() {
    return Consumer<ChannelProvider>(
      builder: (context, provider, _) {
        if (provider.errorMessage.isEmpty) {
          return const SizedBox.shrink();
        }
        return MaterialBanner(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          content: Text(provider.errorMessage),
          leading: Icon(
            provider.isOffline ? Icons.wifi_off : Icons.error_outline,
            color: provider.isOffline ? Colors.orange : Colors.red,
          ),
          backgroundColor: provider.isOffline
              ? Colors.orange.withOpacity(0.1)
              : Colors.red.withOpacity(0.1),
          actions: [
            TextButton(
              onPressed: () {
                provider.clearError();
                provider.fetchChannels();
              },
              child: const Text('RETRY'),
            ),
            TextButton(
              onPressed: () => provider.clearError(),
              child: const Text('DISMISS'),
            ),
          ],
        );
      },
    );
  }

  /// Builds the search bar widget.
  Widget _buildSearchBar({double padding = 12.0}) {
    return Padding(
      padding: EdgeInsets.all(padding),
      child: SearchBar(
        controller: _searchController,
        hintText: 'Search channels...',
        leading: const Padding(
          padding: EdgeInsets.only(left: 8),
          child: Icon(Icons.search),
        ),
        trailing: [
          if (_searchController.text.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.clear),
              onPressed: () {
                _searchController.clear();
                context.read<ChannelProvider>().setSearchQuery('');
              },
            ),
        ],
        elevation: MaterialStateProperty.all(0),
        padding: MaterialStateProperty.all(
          const EdgeInsets.symmetric(horizontal: 16),
        ),
        shape: MaterialStateProperty.all(
          RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(28),
          ),
        ),
        onChanged: (value) {
          context.read<ChannelProvider>().setSearchQuery(value);
        },
      ),
    );
  }

  /// Builds the stats bar showing channel counts.
  Widget _buildStatsBar() {
    return Consumer<ChannelProvider>(
      builder: (context, provider, _) {
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '${provider.channels.length} channels',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              Row(
                children: [
                  Icon(Icons.favorite, size: 14, color: Colors.red.shade300),
                  const SizedBox(width: 4),
                  Text(
                    '${provider.favoritesCount}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.red.shade300,
                        ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    '${provider.workingCount} working',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.green,
                        ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  /// Builds the channel list/grid content (loading, empty, or populated).
  Widget _buildChannelList({bool useGridView = false}) {
    return Consumer<ChannelProvider>(
      builder: (context, provider, _) {
        if (provider.isLoading) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                SizedBox(
                  width: 64,
                  height: 64,
                  child: CircularProgressIndicator(
                    strokeWidth: 6,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                ),
                const SizedBox(height: 24),
                Text(
                  'Loading channels...',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface.withOpacity(0.7),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Please wait',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface.withOpacity(0.5),
                  ),
                ),
              ],
            ),
          );
        }

        if (provider.channels.isEmpty) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(32.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.tv_off,
                    size: 96,
                    color: Theme.of(context).colorScheme.primary.withOpacity(0.3),
                  ),
                  const SizedBox(height: 24),
                  Text(
                    'No channels found',
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Try adjusting your filters or refresh to load channels',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 32),
                  FilledButton.icon(
                    onPressed: () => provider.fetchChannels(),
                    icon: const Icon(Icons.refresh),
                    label: const Text('Refresh Channels'),
                    style: FilledButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 32,
                        vertical: 16,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        }

        if (useGridView) {
          return GridView.builder(
            padding: const EdgeInsets.all(8),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              childAspectRatio: 3.5,
              crossAxisSpacing: 8,
              mainAxisSpacing: 4,
            ),
            itemCount: provider.channels.length,
            itemBuilder: (context, index) {
              final channel = provider.channels[index];
              return Card(
                margin: EdgeInsets.zero,
                child: ChannelTile(
                  channel: channel,
                  onTap: () => _playChannel(channel, index),
                ),
              );
            },
          );
        }

        return ListView.builder(
          itemCount: provider.channels.length,
          itemBuilder: (context, index) {
            final channel = provider.channels[index];
            return ChannelTile(
              channel: channel,
              onTap: () => _playChannel(channel, index),
            );
          },
        );
      },
    );
  }

  /// Landscape layout: side-by-side with filter sidebar (left) and channel list (right).
  Widget _buildLandscapeBody() {
    return Column(
      children: [
        _buildScanProgress(),
        _buildErrorBanner(),
        Expanded(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Left sidebar: filters panel (fixed width, scrollable)
              SizedBox(
                width: 300,
                child: Container(
                  decoration: BoxDecoration(
                    border: Border(
                      right: BorderSide(
                        color: Theme.of(context).dividerColor,
                        width: 1,
                      ),
                    ),
                  ),
                  child: Consumer<ChannelProvider>(
                    builder: (context, provider, _) {
                      return SingleChildScrollView(
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            // Search bar
                            _buildSearchBar(padding: 8.0),
                            // Vertical filter dropdowns
                            Padding(
                              key: _filterAreaKey,
                              padding: const EdgeInsets.symmetric(horizontal: 8.0),
                              child: Column(
                                children: [
                                  FilterDropdown(
                                    value: provider.selectedMediaType,
                                    items: provider.mediaTypes,
                                    hint: 'Type',
                                    icon: Icons.live_tv,
                                    onChanged: (value) => provider.setMediaType(value!),
                                  ),
                                  const SizedBox(height: 6),
                                  FilterDropdown(
                                    value: provider.selectedStatus,
                                    items: provider.statusOptions,
                                    hint: 'Status',
                                    icon: Icons.check_circle_outline,
                                    onChanged: (value) => provider.setStatus(value!),
                                  ),
                                  const SizedBox(height: 6),
                                  FilterDropdown(
                                    value: provider.selectedCategory,
                                    items: provider.categories,
                                    hint: 'Category',
                                    icon: Icons.category,
                                    onChanged: (value) => provider.setCategory(value!),
                                  ),
                                  const SizedBox(height: 6),
                                  FilterDropdown(
                                    value: provider.selectedCountry,
                                    items: provider.countries,
                                    hint: 'Country',
                                    icon: Icons.flag,
                                    onChanged: (value) => provider.setCountry(value!),
                                  ),
                                  const SizedBox(height: 6),
                                  FilterDropdown(
                                    value: provider.selectedLanguage,
                                    items: provider.languages,
                                    hint: 'Language',
                                    icon: Icons.language,
                                    onChanged: (value) => provider.setLanguage(value!),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 6),
                            // Favorites chip
                            Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 8.0),
                              child: FilterChip(
                                label: Text(
                                  '★ Favorites (${provider.favoritesCount})',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: provider.showFavoritesOnly
                                        ? Colors.amber.shade900
                                        : null,
                                  ),
                                ),
                                selected: provider.showFavoritesOnly,
                                selectedColor: Colors.amber.shade100,
                                avatar: Icon(
                                  provider.showFavoritesOnly
                                      ? Icons.star
                                      : Icons.star_border,
                                  size: 18,
                                  color: provider.showFavoritesOnly
                                      ? Colors.amber.shade700
                                      : null,
                                ),
                                onSelected: (_) => provider.toggleFavoritesFilter(),
                              ),
                            ),
                            // Clear filters
                            if (provider.hasActiveFilters)
                              Padding(
                                padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
                                child: OutlinedButton.icon(
                                  onPressed: () {
                                    _searchController.clear();
                                    provider.clearFilters();
                                  },
                                  icon: const Icon(Icons.clear_all, size: 18),
                                  label: const Text('Clear Filters'),
                                  style: OutlinedButton.styleFrom(
                                    minimumSize: const Size(double.infinity, 36),
                                  ),
                                ),
                              ),
                            const Divider(height: 8),
                            // Stats
                            _buildStatsBar(),
                            // Recently played (compact)
                            if (_recentChannels.isNotEmpty) ...[
                              const Divider(height: 8),
                              Padding(
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
                                child: Row(
                                  children: [
                                    Icon(Icons.history, size: 14,
                                        color: Theme.of(context).colorScheme.primary),
                                    const SizedBox(width: 4),
                                    Text(
                                      'Recently Played',
                                      style: Theme.of(context).textTheme.labelSmall?.copyWith(
                                            fontWeight: FontWeight.bold,
                                          ),
                                    ),
                                  ],
                                ),
                              ),
                              Padding(
                                padding: const EdgeInsets.symmetric(horizontal: 8.0),
                                child: Wrap(
                                  spacing: 4,
                                  runSpacing: 4,
                                  children: _recentChannels.take(5).map((entry) {
                                    final name = entry['name'] as String? ?? '';
                                    final url = entry['url'] as String? ?? '';
                                    final country = entry['country'] as String? ?? '';
                                    final category = entry['category'] as String? ?? '';
                                    return ActionChip(
                                      avatar: const Icon(Icons.play_circle_fill, size: 14),
                                      label: Text(
                                        name,
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        style: const TextStyle(fontSize: 11),
                                      ),
                                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                      visualDensity: VisualDensity.compact,
                                      onPressed: () {
                                        final channel = Channel(
                                          name: name,
                                          url: url,
                                          country: country.isNotEmpty ? country : null,
                                          category: category.isNotEmpty ? category : null,
                                          logo: entry['logo'] as String?,
                                        );
                                        _playChannel(channel);
                                      },
                                    );
                                  }).toList(),
                                ),
                              ),
                            ],
                          ],
                        ),
                      );
                    },
                  ),
                ),
              ),
              // Right panel: channel list
              Expanded(
                child: _buildChannelList(),
              ),
            ],
          ),
        ),
      ],
    );
  }

  /// Portrait layout: vertical stack with search, filters, and channel list.
  Widget _buildPortraitBody() {
    return Column(
      children: [
        _buildScanProgress(),
        _buildErrorBanner(),
        _buildSearchBar(),
        Consumer<ChannelProvider>(
          builder: (context, provider, _) {
            return _buildFilters(provider, false);
          },
        ),
        // Clear Filters Button (BL-008)
        Consumer<ChannelProvider>(
          builder: (context, provider, _) {
            if (provider.hasActiveFilters) {
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
                child: OutlinedButton.icon(
                  onPressed: () {
                    _searchController.clear();
                    provider.clearFilters();
                  },
                  icon: const Icon(Icons.clear_all, size: 18),
                  label: const Text('Clear Filters'),
                  style: OutlinedButton.styleFrom(
                    minimumSize: const Size(double.infinity, 36),
                  ),
                ),
              );
            }
            return const SizedBox.shrink();
          },
        ),
        _buildStatsBar(),
        // Recently Played Section
        if (_recentChannels.isNotEmpty)
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                child: Row(
                  children: [
                    Icon(Icons.history, size: 16,
                        color: Theme.of(context).colorScheme.primary),
                    const SizedBox(width: 6),
                    Text(
                      'Recently Played',
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                  ],
                ),
              ),
              SizedBox(
                height: 52,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  itemCount: _recentChannels.length,
                  separatorBuilder: (_, __) => const SizedBox(width: 8),
                  itemBuilder: (context, index) {
                    final entry = _recentChannels[index];
                    final name = entry['name'] as String? ?? '';
                    final url = entry['url'] as String? ?? '';
                    final country = entry['country'] as String? ?? '';
                    final category = entry['category'] as String? ?? '';
                    return ActionChip(
                      avatar: const Icon(Icons.play_circle_fill, size: 18),
                      label: Text(
                        name,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      tooltip: [name, country, category]
                          .where((s) => s.isNotEmpty)
                          .join(' • '),
                      onPressed: () {
                        final channel = Channel(
                          name: name,
                          url: url,
                          country: country.isNotEmpty ? country : null,
                          category: category.isNotEmpty ? category : null,
                          logo: entry['logo'] as String?,
                        );
                        _playChannel(channel);
                      },
                    );
                  },
                ),
              ),
              const Divider(height: 1),
            ],
          ),
        // Channel List
        Expanded(
          child: _buildChannelList(),
        ),
      ],
    );
  }

  /// Tablet landscape layout: channel list (flex: 2) + embedded player panel (flex: 3).
  Widget _buildTabletLandscapeBody() {
    return Column(
      children: [
        _buildScanProgress(),
        _buildErrorBanner(),
        Expanded(
          child: Row(
            children: [
              // Left: channel list panel
              Expanded(
                flex: 2,
                child: Column(
                  children: [
                    _buildSearchBar(padding: 8.0),
                    Consumer<ChannelProvider>(
                      builder: (context, provider, _) {
                        return _buildFilters(provider, true);
                      },
                    ),
                    _buildStatsBar(),
                    Expanded(
                      child: Consumer<ChannelProvider>(
                        builder: (context, provider, _) {
                          if (provider.isLoading) {
                            return const Center(
                              child: CircularProgressIndicator(),
                            );
                          }
                          if (provider.channels.isEmpty) {
                            return Center(
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.tv_off, size: 48,
                                      color: Theme.of(context).colorScheme.primary.withOpacity(0.3)),
                                  const SizedBox(height: 12),
                                  const Text('No channels found'),
                                ],
                              ),
                            );
                          }
                          return ListView.builder(
                            itemCount: provider.channels.length,
                            itemBuilder: (context, index) {
                              final channel = provider.channels[index];
                              final isSelected = _tabletSelectedChannel?.url == channel.url;
                              return Container(
                                color: isSelected
                                    ? Theme.of(context).colorScheme.primaryContainer.withOpacity(0.3)
                                    : null,
                                child: ChannelTile(
                                  channel: channel,
                                  compact: true,
                                  onTap: () {
                                    setState(() {
                                      _tabletSelectedChannel = channel;
                                      _tabletSelectedIndex = index;
                                    });
                                  },
                                ),
                              );
                            },
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ),
              // Divider between panels
              VerticalDivider(
                width: 1,
                color: Theme.of(context).dividerColor,
              ),
              // Right: embedded player panel
              Expanded(
                flex: 3,
                child: _tabletSelectedChannel != null
                    ? PlayerScreen(
                        key: ValueKey(_tabletSelectedChannel!.url),
                        channel: _tabletSelectedChannel!,
                        channelList: context.read<ChannelProvider>().channels,
                        channelIndex: _tabletSelectedIndex,
                      )
                    : Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.play_circle_outline,
                              size: 80,
                              color: Theme.of(context).colorScheme.primary.withOpacity(0.3),
                            ),
                            const SizedBox(height: 16),
                            Text(
                              'Select a channel to play',
                              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                color: Theme.of(context).colorScheme.onSurface.withOpacity(0.5),
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Tap any channel from the list',
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: Theme.of(context).colorScheme.onSurface.withOpacity(0.3),
                              ),
                            ),
                          ],
                        ),
                      ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  /// Tablet portrait layout: 2-column grid with larger channel tiles.
  Widget _buildTabletPortraitBody() {
    return Column(
      children: [
        _buildScanProgress(),
        _buildErrorBanner(),
        _buildSearchBar(),
        Consumer<ChannelProvider>(
          builder: (context, provider, _) {
            return _buildFilters(provider, false);
          },
        ),
        // Clear Filters Button
        Consumer<ChannelProvider>(
          builder: (context, provider, _) {
            if (provider.hasActiveFilters) {
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
                child: OutlinedButton.icon(
                  onPressed: () {
                    _searchController.clear();
                    provider.clearFilters();
                  },
                  icon: const Icon(Icons.clear_all, size: 18),
                  label: const Text('Clear Filters'),
                  style: OutlinedButton.styleFrom(
                    minimumSize: const Size(double.infinity, 36),
                  ),
                ),
              );
            }
            return const SizedBox.shrink();
          },
        ),
        _buildStatsBar(),
        // Recently Played Section
        if (_recentChannels.isNotEmpty)
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                child: Row(
                  children: [
                    Icon(Icons.history, size: 16,
                        color: Theme.of(context).colorScheme.primary),
                    const SizedBox(width: 6),
                    Text(
                      'Recently Played',
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                  ],
                ),
              ),
              SizedBox(
                height: 52,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  itemCount: _recentChannels.length,
                  separatorBuilder: (_, __) => const SizedBox(width: 8),
                  itemBuilder: (context, index) {
                    final entry = _recentChannels[index];
                    final name = entry['name'] as String? ?? '';
                    final url = entry['url'] as String? ?? '';
                    final country = entry['country'] as String? ?? '';
                    final category = entry['category'] as String? ?? '';
                    return ActionChip(
                      avatar: const Icon(Icons.play_circle_fill, size: 18),
                      label: Text(
                        name,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      tooltip: [name, country, category]
                          .where((s) => s.isNotEmpty)
                          .join(' • '),
                      onPressed: () {
                        final channel = Channel(
                          name: name,
                          url: url,
                          country: country.isNotEmpty ? country : null,
                          category: category.isNotEmpty ? category : null,
                          logo: entry['logo'] as String?,
                        );
                        _playChannel(channel);
                      },
                    );
                  },
                ),
              ),
              const Divider(height: 1),
            ],
          ),
        // Channel Grid (2 columns for tablet portrait)
        Expanded(
          child: _buildChannelList(useGridView: true),
        ),
      ],
    );
  }

  /// Builds the filter dropdowns layout for portrait mode.
  Widget _buildFilters(ChannelProvider provider, bool isLandscape) {
    // Portrait: original two-row layout
    return Padding(
      key: _filterAreaKey,
      padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
      child: Column(
        children: [
          // First row: Type, Status, Category, Country
          Row(
            children: [
              // Media Type Filter (TV/Radio)
              Expanded(
                child: FilterDropdown(
                  value: provider.selectedMediaType,
                  items: provider.mediaTypes,
                  hint: 'Type',
                  icon: Icons.live_tv,
                  onChanged: (value) => provider.setMediaType(value!),
                ),
              ),
              const SizedBox(width: 8),
              // Channel Status Filter (Working/Failed/Unchecked)
              Expanded(
                child: FilterDropdown(
                  value: provider.selectedStatus,
                  items: provider.statusOptions,
                  hint: 'Status',
                  icon: Icons.check_circle_outline,
                  onChanged: (value) => provider.setStatus(value!),
                ),
              ),
              const SizedBox(width: 8),
              // Category Dropdown
              Expanded(
                flex: 2,
                child: FilterDropdown(
                  value: provider.selectedCategory,
                  items: provider.categories,
                  hint: 'Category',
                  icon: Icons.category,
                  onChanged: (value) => provider.setCategory(value!),
                ),
              ),
              const SizedBox(width: 8),
              // Country Dropdown
              Expanded(
                flex: 2,
                child: FilterDropdown(
                  value: provider.selectedCountry,
                  items: provider.countries,
                  hint: 'Country',
                  icon: Icons.flag,
                  onChanged: (value) => provider.setCountry(value!),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          // Second row: Language filter (BL-017) + Favorites toggle
          Row(
            children: [
              Expanded(
                child: FilterDropdown(
                  value: provider.selectedLanguage,
                  items: provider.languages,
                  hint: 'Language',
                  icon: Icons.language,
                  onChanged: (value) => provider.setLanguage(value!),
                ),
              ),
              const SizedBox(width: 8),
              // Favorites toggle button
              FilterChip(
                label: Text(
                  '★ Favorites (${provider.favoritesCount})',
                  style: TextStyle(
                    fontSize: 12,
                    color: provider.showFavoritesOnly
                        ? Colors.amber.shade900
                        : null,
                  ),
                ),
                selected: provider.showFavoritesOnly,
                selectedColor: Colors.amber.shade100,
                avatar: Icon(
                  provider.showFavoritesOnly
                      ? Icons.star
                      : Icons.star_border,
                  size: 18,
                  color: provider.showFavoritesOnly
                      ? Colors.amber.shade700
                      : null,
                ),
                onSelected: (_) => provider.toggleFavoritesFilter(),
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _playChannel(Channel channel, [int? index]) {
    final parentalService = ParentalControlsService.instance;

    // Check if channel is blocked by parental controls
    if (parentalService.isChannelBlocked(category: channel.category)) {
      _showParentalPinForChannel(channel, index);
      return;
    }

    _navigateToPlayer(channel, index);
  }

  /// Show PIN dialog to unlock a blocked channel.
  Future<void> _showParentalPinForChannel(Channel channel, [int? index]) async {
    final verified = await PinDialog.show(
      context,
      title: 'Content Blocked',
      subtitle: 'This channel is restricted by parental controls.\nEnter PIN to watch.',
      onSubmit: (pin) async {
        return ParentalControlsService.instance.verifyPin(pin);
      },
    );
    if (verified && mounted) {
      _navigateToPlayer(channel, index);
    }
  }

  void _navigateToPlayer(Channel channel, [int? index]) {
    // Track channel play telemetry (no names/URLs)
    AnalyticsService.instance.trackChannelPlay(
      channel.url,
      country: channel.country ?? '',
      category: channel.category ?? '',
    );
    // Boost scan priority for this channel's country
    if (channel.country != null && channel.country!.isNotEmpty) {
      final provider = Provider.of<ChannelProvider>(context, listen: false);
      provider.boostCountry(channel.country!);
    }
    final provider = Provider.of<ChannelProvider>(context, listen: false);
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => PlayerScreen(
          channel: channel,
          channelList: provider.channels,
          channelIndex: index,
        ),
      ),
    ).then((_) {
      // Refresh recently played after returning from player
      _loadRecentHistory();
    });
  }

  /// Open parental controls settings.
  /// If parental controls are already set up, require PIN to access settings.
  Future<void> _openParentalSettings() async {
    final parentalService = ParentalControlsService.instance;

    if (parentalService.hasPin && parentalService.enabled) {
      final verified = await PinDialog.show(
        context,
        title: 'Enter PIN',
        subtitle: 'Enter your PIN to access parental control settings',
        onSubmit: (pin) async => parentalService.verifyPin(pin),
      );
      if (!verified || !mounted) return;
    }

    if (!mounted) return;
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => const ParentalSettingsScreen(),
      ),
    );
  }

  void _showAboutDialog() async {
    String version = '2.3.2';
    try {
      final packageInfo = await PackageInfo.fromPlatform();
      version = packageInfo.version;
    } catch (_) {}
    if (!mounted) return;
    showAboutDialog(
      context: context,
      applicationName: 'TV Viewer',
      applicationVersion: version,
      applicationIcon: const Icon(Icons.tv, size: 48),
      children: [
        const Text(
          'A free IPTV streaming app that discovers and validates '
          'publicly available TV streams from open repositories.',
        ),
        const SizedBox(height: 16),
        const Text(
          'Built with Flutter for Android.',
          style: TextStyle(fontStyle: FontStyle.italic),
        ),
      ],
    );
  }
}

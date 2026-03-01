import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/channel_provider.dart';
import '../models/channel.dart';
import '../services/feedback_service.dart';
import '../services/onboarding_service.dart';
import '../widgets/channel_tile.dart';
import '../widgets/filter_dropdown.dart';
import '../widgets/scan_progress_bar.dart';
import '../widgets/onboarding_tooltip.dart';
import 'diagnostics_screen.dart';
import 'help_screen.dart';
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

  @override
  void initState() {
    super.initState();
    // Load channels on startup
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ChannelProvider>().loadChannels();
      _checkRatingPrompt(); // BL-032: Check if we should show rating prompt
      _checkAndShowOnboarding();
    });
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
        position = ArrowPosition.bottom;
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
    return Scaffold(
      appBar: AppBar(
        title: const Text('📺 TV Viewer'),
        actions: [
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
      body: Column(
        children: [
          // Scan Progress
          Consumer<ChannelProvider>(
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
          ),

          // #41: Offline / error banner
          Consumer<ChannelProvider>(
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
          ),

          // Search Bar
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search channels...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchController.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _searchController.clear();
                          context.read<ChannelProvider>().setSearchQuery('');
                        },
                      )
                    : null,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                filled: true,
              ),
              onChanged: (value) {
                context.read<ChannelProvider>().setSearchQuery(value);
              },
            ),
          ),

          // Filter Row with Dropdowns (BL-017: Added Language filter)
          Consumer<ChannelProvider>(
            builder: (context, provider, _) {
              return Padding(
                key: _filterAreaKey,
                padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
                child: Column(
                  children: [
                    // First row: Type, Category, Country
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

          // Stats Bar
          Consumer<ChannelProvider>(
            builder: (context, provider, _) {
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '${provider.channels.length} channels',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    Row(
                      children: [
                        Icon(
                          Icons.favorite,
                          size: 14,
                          color: Colors.red.shade300,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '${provider.favoritesCount}',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: Colors.red.shade300,
                              ),
                        ),
                        const SizedBox(width: 16),
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
          ),

          // Channel List
          Expanded(
            child: Consumer<ChannelProvider>(
              builder: (context, provider, _) {
                if (provider.isLoading) {
                  return const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        CircularProgressIndicator(),
                        SizedBox(height: 16),
                        Text('Loading channels...'),
                      ],
                    ),
                  );
                }

                if (provider.channels.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.tv_off, size: 64, color: Colors.grey),
                        const SizedBox(height: 16),
                        const Text('No channels found'),
                        const SizedBox(height: 16),
                        ElevatedButton.icon(
                          onPressed: () => provider.fetchChannels(),
                          icon: const Icon(Icons.refresh),
                          label: const Text('Refresh'),
                        ),
                      ],
                    ),
                  );
                }

                return ListView.builder(
                  itemCount: provider.channels.length,
                  itemBuilder: (context, index) {
                    final channel = provider.channels[index];
                    return ChannelTile(
                      channel: channel,
                      onTap: () => _playChannel(channel),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  void _playChannel(Channel channel) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => PlayerScreen(channel: channel),
      ),
    );
  }

  void _showAboutDialog() {
    showAboutDialog(
      context: context,
      applicationName: 'TV Viewer',
      applicationVersion: '2.0.1',
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

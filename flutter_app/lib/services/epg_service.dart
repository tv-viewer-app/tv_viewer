import 'dart:async';
import 'dart:math';
import '../models/channel.dart';
import '../models/epg_info.dart';
import '../utils/logger_service.dart';

/// Simulated Electronic Program Guide (EPG) service.
///
/// Generates category-aware program schedules for channels and caches
/// them in memory. Auto-refreshes every 60 minutes so time-slot data
/// stays current.
class EpgService {
  // ── Singleton ──────────────────────────────────────────────────────
  static final EpgService _instance = EpgService._();
  factory EpgService() => _instance;
  EpgService._();

  // ── State ──────────────────────────────────────────────────────────
  final Map<String, ChannelEpg> _cache = {};
  Timer? _refreshTimer;
  bool _isLoading = false;
  DateTime? _lastFetchTime;
  final Random _random = Random();

  // ── Public getters ─────────────────────────────────────────────────
  bool get isLoading => _isLoading;
  bool get hasData => _cache.isNotEmpty;
  int get cachedChannelCount => _cache.length;

  // ── Category → program templates ──────────────────────────────────
  static const _programTemplates = <String, List<_ProgramTemplate>>{
    'News': [
      _ProgramTemplate('Morning News Briefing', 'Top stories and headlines from around the world', 30),
      _ProgramTemplate('Breaking News Update', 'Live coverage of developing stories', 60),
      _ProgramTemplate('News at Noon', 'Midday news roundup with expert analysis', 30),
      _ProgramTemplate('World Report', 'International news and global events', 45),
      _ProgramTemplate('Evening News Hour', 'Comprehensive evening news coverage', 60),
      _ProgramTemplate('Late News Wrap', 'Summary of the day\'s top stories', 30),
      _ProgramTemplate('Political Roundtable', 'In-depth political discussion and debate', 60),
      _ProgramTemplate('Business & Markets', 'Financial news and market analysis', 30),
      _ProgramTemplate('Investigative Report', 'In-depth journalism and special reports', 45),
      _ProgramTemplate('News Tonight', 'Final news bulletin of the day', 30),
    ],
    'Sports': [
      _ProgramTemplate('Live Sports Coverage', 'Live game broadcast', 120),
      _ProgramTemplate('Sports Center', 'Scores, highlights, and analysis', 60),
      _ProgramTemplate('Sports Highlights', 'Best moments from today\'s games', 30),
      _ProgramTemplate('Pre-Game Show', 'Expert predictions and team analysis', 30),
      _ProgramTemplate('Post-Game Analysis', 'Recap and player interviews', 45),
      _ProgramTemplate('Sports Talk', 'Fan call-in and debate show', 60),
      _ProgramTemplate('Classic Matches', 'Replays of legendary games', 90),
      _ProgramTemplate('Fitness & Training', 'Athlete training and workout tips', 30),
    ],
    'Entertainment': [
      _ProgramTemplate('Evening Show', 'Popular entertainment variety show', 60),
      _ProgramTemplate('Late Night Programming', 'Comedy and celebrity interviews', 60),
      _ProgramTemplate('Reality Hour', 'Unscripted entertainment and competition', 60),
      _ProgramTemplate('Comedy Special', 'Stand-up comedy and sketch show', 45),
      _ProgramTemplate('Celebrity Talk Show', 'Interviews with stars', 60),
      _ProgramTemplate('Game Show', 'Interactive quiz and competition show', 30),
      _ProgramTemplate('Variety Night', 'Musical performances and entertainment', 90),
      _ProgramTemplate('Weekend Special', 'Special weekend programming', 60),
    ],
    'Movies': [
      _ProgramTemplate('Feature Film', 'Blockbuster movie presentation', 120),
      _ProgramTemplate('Classic Cinema', 'Timeless classic movie', 110),
      _ProgramTemplate('Movie Premiere', 'First-run film broadcast', 130),
      _ProgramTemplate('Film Festival Pick', 'Award-winning cinema selection', 100),
      _ProgramTemplate('Action Movie Night', 'High-octane action film', 120),
      _ProgramTemplate('Indie Spotlight', 'Independent film showcase', 95),
    ],
    'Documentary': [
      _ProgramTemplate('Nature Documentary', 'Exploring the natural world', 60),
      _ProgramTemplate('History Revealed', 'Historical events and discoveries', 45),
      _ProgramTemplate('Science Frontiers', 'Cutting-edge science and technology', 60),
      _ProgramTemplate('True Crime Files', 'Real crime investigations', 45),
      _ProgramTemplate('Planet Earth', 'Wildlife and natural wonders', 60),
      _ProgramTemplate('Human Stories', 'Extraordinary personal journeys', 50),
    ],
    'Kids': [
      _ProgramTemplate('Morning Cartoons', 'Animated fun for kids', 30),
      _ProgramTemplate('Kids Adventure', 'Exciting animated adventures', 25),
      _ProgramTemplate('Learning Time', 'Educational programming for children', 30),
      _ProgramTemplate('Story Hour', 'Animated stories and fairy tales', 30),
      _ProgramTemplate('Fun & Games', 'Interactive kids\' game show', 30),
      _ProgramTemplate('Superhero Hour', 'Action-packed animated heroes', 25),
      _ProgramTemplate('Bedtime Stories', 'Calming stories for little ones', 20),
    ],
    'Music': [
      _ProgramTemplate('Music Program', 'Popular music and performances', 60),
      _ProgramTemplate('Top Hits Countdown', 'This week\'s biggest hits', 60),
      _ProgramTemplate('Live Concert', 'Live music performance', 90),
      _ProgramTemplate('Classic Albums', 'Deep dive into legendary albums', 60),
      _ProgramTemplate('Music Videos', 'Latest music video playlist', 30),
      _ProgramTemplate('Artist Spotlight', 'In-depth look at featured artist', 45),
      _ProgramTemplate('Jazz & Blues Hour', 'Smooth jazz and blues selections', 60),
    ],
    'Radio': [
      _ProgramTemplate('Music Program', 'Curated music selection', 60),
      _ProgramTemplate('Talk Show', 'Engaging conversation and discussion', 60),
      _ProgramTemplate('Morning Drive', 'Wake-up show with music and news', 120),
      _ProgramTemplate('Afternoon Mix', 'Afternoon music blend', 60),
      _ProgramTemplate('Evening Lounge', 'Relaxing evening listening', 60),
      _ProgramTemplate('Night Owl Sessions', 'Late night deep cuts', 120),
      _ProgramTemplate('News on the Hour', 'Brief news update', 15),
      _ProgramTemplate('Weekend Vibes', 'Laid-back weekend programming', 90),
    ],
    'Religious': [
      _ProgramTemplate('Morning Prayer', 'Daily spiritual reflection', 30),
      _ProgramTemplate('Scripture Reading', 'Sacred text study and reading', 30),
      _ProgramTemplate('Sermon of the Day', 'Featured spiritual message', 60),
      _ProgramTemplate('Faith & Community', 'Community stories of faith', 45),
      _ProgramTemplate('Evening Devotion', 'End-of-day spiritual reflection', 30),
      _ProgramTemplate('Religious Music', 'Sacred and devotional music', 60),
    ],
    'Education': [
      _ProgramTemplate('Learning Hour', 'Educational programming', 60),
      _ProgramTemplate('Science Explained', 'Making science accessible', 45),
      _ProgramTemplate('Language Lessons', 'Foreign language instruction', 30),
      _ProgramTemplate('History Class', 'Engaging history lectures', 45),
      _ProgramTemplate('TechTalk', 'Technology and digital literacy', 30),
      _ProgramTemplate('Math Made Easy', 'Mathematics tutorials', 30),
    ],
  };

  /// Default templates for categories without specific programs.
  static const _defaultTemplates = [
    _ProgramTemplate('Live Broadcast', 'Currently airing program', 60),
    _ProgramTemplate('Scheduled Program', 'Regular programming', 45),
    _ProgramTemplate('Featured Show', 'Featured content', 60),
    _ProgramTemplate('Special Presentation', 'Special programming', 90),
    _ProgramTemplate('Regular Programming', 'Standard broadcast', 30),
    _ProgramTemplate('Primetime Show', 'Primetime entertainment', 60),
    _ProgramTemplate('Afternoon Program', 'Afternoon broadcast', 45),
    _ProgramTemplate('Late Night Show', 'Late night content', 60),
  ];

  // ── Public API ─────────────────────────────────────────────────────

  /// Generate EPG data for a list of channels.
  ///
  /// Runs asynchronously (off the main thread via [Future.delayed]) so it
  /// never blocks channel loading.  Results are stored in [_cache] and
  /// the auto-refresh timer is (re)started.
  Future<void> fetchEpg(List<Channel> channels) async {
    if (_isLoading) return;
    _isLoading = true;

    try {
      logger.info('EPG: Generating schedule data for ${channels.length} channels');

      // Yield to the event loop so the caller can continue immediately.
      await Future.delayed(Duration.zero);

      for (final channel in channels) {
        final key = _normalizeKey(channel.name);
        // Skip if we already have current data for this channel.
        if (_cache.containsKey(key) && _isCacheFresh(key)) continue;

        final epg = _generateSchedule(channel);
        _cache[key] = epg;
      }

      _lastFetchTime = DateTime.now();
      _startAutoRefresh();

      logger.info('EPG: Generated data for ${_cache.length} channels');
    } catch (e, st) {
      logger.error('EPG: Failed to generate schedule data', e, st);
    } finally {
      _isLoading = false;
    }
  }

  /// Retrieve the full [ChannelEpg] for a channel, if available.
  ChannelEpg? getEpgForChannel(String channelName) {
    final key = _normalizeKey(channelName);
    return _cache[key];
  }

  /// Convenience: current program for [channelName], or `null`.
  EpgInfo? getCurrentProgram(String channelName) {
    return getEpgForChannel(channelName)?.currentProgram;
  }

  /// Convenience: next program for [channelName], or `null`.
  EpgInfo? getNextProgram(String channelName) {
    return getEpgForChannel(channelName)?.nextProgram;
  }

  /// Whether we have any EPG data for [channelName].
  bool hasEpgData(String channelName) {
    final key = _normalizeKey(channelName);
    return _cache.containsKey(key) && _cache[key]!.programs.isNotEmpty;
  }

  /// Force-clear the cache (useful for testing or settings changes).
  void clearCache() {
    _cache.clear();
    _lastFetchTime = null;
    _refreshTimer?.cancel();
    _refreshTimer = null;
    logger.info('EPG: Cache cleared');
  }

  /// Shut down timers.
  void dispose() {
    _refreshTimer?.cancel();
    _refreshTimer = null;
  }

  // ── Private helpers ────────────────────────────────────────────────

  /// Normalise a channel name so look-ups are case-/whitespace-insensitive.
  String _normalizeKey(String name) {
    return name.toLowerCase().trim().replaceAll(RegExp(r'\s+'), ' ');
  }

  /// Returns `true` when the cache entry for [key] was generated within
  /// the current hour-block (i.e. programs still cover "now").
  bool _isCacheFresh(String key) {
    final epg = _cache[key];
    if (epg == null || epg.programs.isEmpty) return false;

    // If there is still a currently-airing program the data is fine.
    if (epg.currentProgram != null) return true;

    // Otherwise the schedule has gone stale.
    return false;
  }

  /// Start (or restart) the 60-minute auto-refresh timer.
  void _startAutoRefresh() {
    _refreshTimer?.cancel();
    _refreshTimer = Timer(const Duration(minutes: 60), () {
      logger.info('EPG: Auto-refresh triggered');
      // Re-generate for all cached channels.
      final staleKeys = _cache.keys.toList();
      for (final key in staleKeys) {
        final old = _cache[key];
        if (old == null) continue; // guard against concurrent clearCache()
        _cache[key] = _generateScheduleFromMeta(
          channelId: old.channelId,
          channelName: old.channelName,
          category: old.programs.isNotEmpty ? old.programs.first.category : null,
        );
      }
      _lastFetchTime = DateTime.now();
      _startAutoRefresh(); // reschedule
    });
  }

  /// Build an 8-hour schedule for [channel] centered on "now".
  ChannelEpg _generateSchedule(Channel channel) {
    final category = channel.category ?? (channel.mediaType == 'Radio' ? 'Radio' : 'General');
    return _generateScheduleFromMeta(
      channelId: channel.url.hashCode.toRadixString(16),
      channelName: channel.name,
      category: category,
    );
  }

  /// Core schedule generator — deterministic-ish per channel name so the
  /// same channel always gets the same "feel" within an hour-block.
  ChannelEpg _generateScheduleFromMeta({
    required String channelId,
    required String channelName,
    String? category,
  }) {
    final templates = _pickTemplates(category);
    final programs = <EpgInfo>[];

    // Seed a deterministic random per channel+hour so successive calls
    // in the same hour yield identical schedules.
    final hourSeed = channelName.hashCode ^ (DateTime.now().hour * 31);
    final rng = Random(hourSeed);

    // Start 2 hours before now, generate up to ~6 hours into the future.
    final now = DateTime.now();
    var cursor = DateTime(now.year, now.month, now.day, now.hour - 2);

    // Generate a rolling window of programs.
    while (cursor.isBefore(now.add(const Duration(hours: 6)))) {
      final template = templates[rng.nextInt(templates.length)];

      // Vary duration ±10 min around the template's preferred length.
      final variance = rng.nextInt(21) - 10; // -10 .. +10
      final durationMin = (template.durationMinutes + variance).clamp(15, 180);

      final start = cursor;
      final end = cursor.add(Duration(minutes: durationMin));

      programs.add(EpgInfo(
        programTitle: template.title,
        description: template.description,
        startTime: start,
        endTime: end,
        category: category,
      ));

      cursor = end;
    }

    return ChannelEpg(
      channelId: channelId,
      channelName: channelName,
      programs: programs,
    );
  }

  /// Pick the template list that best matches [category].
  List<_ProgramTemplate> _pickTemplates(String? category) {
    if (category == null) return _defaultTemplates;

    final lower = category.toLowerCase();

    // Direct hit.
    for (final entry in _programTemplates.entries) {
      if (entry.key.toLowerCase() == lower) return entry.value;
    }

    // Fuzzy match — check if the category *contains* a known key or
    // vice-versa (e.g. "Sports & Fitness" → Sports).
    for (final entry in _programTemplates.entries) {
      final k = entry.key.toLowerCase();
      if (lower.contains(k) || k.contains(lower)) return entry.value;
    }

    return _defaultTemplates;
  }
}

/// Internal program template (compile-time constant).
class _ProgramTemplate {
  final String title;
  final String description;
  final int durationMinutes;

  const _ProgramTemplate(this.title, this.description, this.durationMinutes);
}

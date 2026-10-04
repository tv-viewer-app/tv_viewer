import '../models/channel.dart';
import '../models/epg_info.dart';
import '../utils/logger_service.dart';

/// Program-guide facade.
///
/// TV Viewer does not invent schedule data. Until a verified XMLTV or
/// broadcaster-provided source is configured, every lookup returns no data and
/// the UI clearly reports that the schedule is unavailable.
class EpgService {
  static final EpgService _instance = EpgService._();
  factory EpgService() => _instance;
  EpgService._();

  bool get isLoading => false;
  bool get hasData => false;
  int get cachedChannelCount => 0;

  Future<void> fetchEpg(List<Channel> channels) async {
    logger.debug(
      'EPG: no verified schedule source configured for ${channels.length} channels',
    );
  }

  ChannelEpg? getEpgForChannel(String channelName) => null;

  EpgInfo? getCurrentProgram(String channelName) => null;

  EpgInfo? getNextProgram(String channelName) => null;

  bool hasEpgData(String channelName) => false;

  void clearCache() {}

  void dispose() {}
}

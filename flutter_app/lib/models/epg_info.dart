/// Electronic Program Guide (EPG) model
/// Represents schedule information for a channel
class EpgInfo {
  final String programTitle;
  final String? description;
  final DateTime startTime;
  final DateTime endTime;
  final String? category;
  
  EpgInfo({
    required this.programTitle,
    this.description,
    required this.startTime,
    required this.endTime,
    this.category,
  });
  
  /// Calculate program progress (0.0 to 1.0)
  double get progress {
    final now = DateTime.now();
    if (now.isBefore(startTime)) return 0.0;
    if (now.isAfter(endTime)) return 1.0;
    
    final totalDuration = endTime.difference(startTime).inSeconds;
    final elapsed = now.difference(startTime).inSeconds;
    
    return elapsed / totalDuration;
  }
  
  /// Check if program is currently airing
  bool get isCurrentlyAiring {
    final now = DateTime.now();
    return now.isAfter(startTime) && now.isBefore(endTime);
  }
  
  /// Get remaining time in minutes
  int get remainingMinutes {
    if (!isCurrentlyAiring) return 0;
    return endTime.difference(DateTime.now()).inMinutes;
  }
  
  /// Format time range (e.g., "14:00 - 15:30")
  String get timeRange {
    final startStr = _formatTime(startTime);
    final endStr = _formatTime(endTime);
    return '$startStr - $endStr';
  }
  
  /// Format duration (e.g., "90 min")
  String get duration {
    final minutes = endTime.difference(startTime).inMinutes;
    if (minutes < 60) {
      return '$minutes min';
    } else {
      final hours = minutes ~/ 60;
      final mins = minutes % 60;
      return mins > 0 ? '${hours}h ${mins}min' : '${hours}h';
    }
  }
  
  String _formatTime(DateTime time) {
    return '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';
  }
  
  factory EpgInfo.fromJson(Map<String, dynamic> json) {
    return EpgInfo(
      programTitle: json['programTitle'] ?? json['title'] ?? 'Unknown Program',
      description: json['description'],
      startTime: DateTime.parse(json['startTime']),
      endTime: DateTime.parse(json['endTime']),
      category: json['category'],
    );
  }
  
  Map<String, dynamic> toJson() => {
        'programTitle': programTitle,
        'description': description,
        'startTime': startTime.toIso8601String(),
        'endTime': endTime.toIso8601String(),
        'category': category,
      };
  
  /// Create a placeholder for when EPG data is not available
  factory EpgInfo.placeholder({
    required bool isNow,
  }) {
    final now = DateTime.now();
    final startTime = isNow ? now.subtract(const Duration(minutes: 30)) : now.add(const Duration(hours: 1));
    final endTime = startTime.add(const Duration(hours: 1));
    
    return EpgInfo(
      programTitle: isNow ? 'Live Broadcast' : 'Scheduled Program',
      description: 'EPG data not available for this channel',
      startTime: startTime,
      endTime: endTime,
    );
  }
}

/// EPG schedule for a channel
class ChannelEpg {
  final String channelId;
  final String channelName;
  final List<EpgInfo> programs;
  
  ChannelEpg({
    required this.channelId,
    required this.channelName,
    required this.programs,
  });
  
  /// Get currently airing program
  EpgInfo? get currentProgram {
    final now = DateTime.now();
    try {
      return programs.firstWhere(
        (p) => now.isAfter(p.startTime) && now.isBefore(p.endTime),
      );
    } catch (e) {
      return null;
    }
  }
  
  /// Get next scheduled program
  EpgInfo? get nextProgram {
    final now = DateTime.now();
    final futurePrograms = programs.where((p) => p.startTime.isAfter(now)).toList();
    if (futurePrograms.isEmpty) return null;
    
    futurePrograms.sort((a, b) => a.startTime.compareTo(b.startTime));
    return futurePrograms.first;
  }
  
  /// Get current and next program with placeholders
  Map<String, EpgInfo> getCurrentAndNext() {
    return {
      'now': currentProgram ?? EpgInfo.placeholder(isNow: true),
      'next': nextProgram ?? EpgInfo.placeholder(isNow: false),
    };
  }
  
  factory ChannelEpg.fromJson(Map<String, dynamic> json) {
    return ChannelEpg(
      channelId: json['channelId'] ?? '',
      channelName: json['channelName'] ?? 'Unknown',
      programs: (json['programs'] as List<dynamic>?)
              ?.map((p) => EpgInfo.fromJson(p as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
  
  Map<String, dynamic> toJson() => {
        'channelId': channelId,
        'channelName': channelName,
        'programs': programs.map((p) => p.toJson()).toList(),
      };
  
  /// Create empty EPG with placeholders
  factory ChannelEpg.placeholder({
    required String channelId,
    required String channelName,
  }) {
    return ChannelEpg(
      channelId: channelId,
      channelName: channelName,
      programs: [],
    );
  }
}

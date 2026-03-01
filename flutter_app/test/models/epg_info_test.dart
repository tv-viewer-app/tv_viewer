import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_app/models/epg_info.dart';

void main() {
  group('EpgInfo', () {
    test('creates EPG info with all fields', () {
      final startTime = DateTime(2024, 1, 15, 14, 0);
      final endTime = DateTime(2024, 1, 15, 15, 30);
      
      final epg = EpgInfo(
        programTitle: 'News Hour',
        description: 'Daily news and weather',
        startTime: startTime,
        endTime: endTime,
        category: 'News',
      );
      
      expect(epg.programTitle, 'News Hour');
      expect(epg.description, 'Daily news and weather');
      expect(epg.startTime, startTime);
      expect(epg.endTime, endTime);
      expect(epg.category, 'News');
    });
    
    test('calculates duration correctly', () {
      final startTime = DateTime(2024, 1, 15, 14, 0);
      final endTime = DateTime(2024, 1, 15, 15, 30);
      
      final epg = EpgInfo(
        programTitle: 'Movie',
        startTime: startTime,
        endTime: endTime,
      );
      
      expect(epg.duration, '1h 30min');
    });
    
    test('formats duration for full hours', () {
      final startTime = DateTime(2024, 1, 15, 14, 0);
      final endTime = DateTime(2024, 1, 15, 16, 0);
      
      final epg = EpgInfo(
        programTitle: 'Movie',
        startTime: startTime,
        endTime: endTime,
      );
      
      expect(epg.duration, '2h');
    });
    
    test('formats duration for minutes only', () {
      final startTime = DateTime(2024, 1, 15, 14, 0);
      final endTime = DateTime(2024, 1, 15, 14, 45);
      
      final epg = EpgInfo(
        programTitle: 'Short Show',
        startTime: startTime,
        endTime: endTime,
      );
      
      expect(epg.duration, '45 min');
    });
    
    test('formats time range correctly', () {
      final startTime = DateTime(2024, 1, 15, 14, 0);
      final endTime = DateTime(2024, 1, 15, 15, 30);
      
      final epg = EpgInfo(
        programTitle: 'News',
        startTime: startTime,
        endTime: endTime,
      );
      
      expect(epg.timeRange, '14:00 - 15:30');
    });
    
    test('formats time with leading zeros', () {
      final startTime = DateTime(2024, 1, 15, 9, 5);
      final endTime = DateTime(2024, 1, 15, 10, 30);
      
      final epg = EpgInfo(
        programTitle: 'Morning Show',
        startTime: startTime,
        endTime: endTime,
      );
      
      expect(epg.timeRange, '09:05 - 10:30');
    });
    
    test('creates placeholder for current program', () {
      final epg = EpgInfo.placeholder(isNow: true);
      
      expect(epg.programTitle, 'Live Broadcast');
      expect(epg.description, 'EPG data not available for this channel');
      expect(epg.startTime.isBefore(DateTime.now()), true);
      expect(epg.endTime.isAfter(DateTime.now()), true);
    });
    
    test('creates placeholder for next program', () {
      final epg = EpgInfo.placeholder(isNow: false);
      
      expect(epg.programTitle, 'Scheduled Program');
      expect(epg.description, 'EPG data not available for this channel');
      expect(epg.startTime.isAfter(DateTime.now()), true);
      expect(epg.endTime.isAfter(DateTime.now()), true);
    });
    
    test('serializes to JSON correctly', () {
      final startTime = DateTime(2024, 1, 15, 14, 0);
      final endTime = DateTime(2024, 1, 15, 15, 30);
      
      final epg = EpgInfo(
        programTitle: 'News Hour',
        description: 'Daily news',
        startTime: startTime,
        endTime: endTime,
        category: 'News',
      );
      
      final json = epg.toJson();
      
      expect(json['programTitle'], 'News Hour');
      expect(json['description'], 'Daily news');
      expect(json['startTime'], startTime.toIso8601String());
      expect(json['endTime'], endTime.toIso8601String());
      expect(json['category'], 'News');
    });
    
    test('deserializes from JSON correctly', () {
      final startTime = DateTime(2024, 1, 15, 14, 0);
      final endTime = DateTime(2024, 1, 15, 15, 30);
      
      final json = {
        'programTitle': 'News Hour',
        'description': 'Daily news',
        'startTime': startTime.toIso8601String(),
        'endTime': endTime.toIso8601String(),
        'category': 'News',
      };
      
      final epg = EpgInfo.fromJson(json);
      
      expect(epg.programTitle, 'News Hour');
      expect(epg.description, 'Daily news');
      expect(epg.startTime, startTime);
      expect(epg.endTime, endTime);
      expect(epg.category, 'News');
    });
    
    test('deserializes from JSON with alternative title field', () {
      final startTime = DateTime(2024, 1, 15, 14, 0);
      final endTime = DateTime(2024, 1, 15, 15, 30);
      
      final json = {
        'title': 'News Hour',
        'startTime': startTime.toIso8601String(),
        'endTime': endTime.toIso8601String(),
      };
      
      final epg = EpgInfo.fromJson(json);
      
      expect(epg.programTitle, 'News Hour');
    });
    
    test('handles missing optional fields in JSON', () {
      final startTime = DateTime(2024, 1, 15, 14, 0);
      final endTime = DateTime(2024, 1, 15, 15, 30);
      
      final json = {
        'startTime': startTime.toIso8601String(),
        'endTime': endTime.toIso8601String(),
      };
      
      final epg = EpgInfo.fromJson(json);
      
      expect(epg.programTitle, 'Unknown Program');
      expect(epg.description, null);
      expect(epg.category, null);
    });
  });
  
  group('ChannelEpg', () {
    test('creates channel EPG with programs', () {
      final programs = [
        EpgInfo(
          programTitle: 'Show 1',
          startTime: DateTime(2024, 1, 15, 14, 0),
          endTime: DateTime(2024, 1, 15, 15, 0),
        ),
        EpgInfo(
          programTitle: 'Show 2',
          startTime: DateTime(2024, 1, 15, 15, 0),
          endTime: DateTime(2024, 1, 15, 16, 0),
        ),
      ];
      
      final channelEpg = ChannelEpg(
        channelId: 'cnn',
        channelName: 'CNN',
        programs: programs,
      );
      
      expect(channelEpg.channelId, 'cnn');
      expect(channelEpg.channelName, 'CNN');
      expect(channelEpg.programs.length, 2);
    });
    
    test('finds current program correctly', () {
      final now = DateTime.now();
      final programs = [
        EpgInfo(
          programTitle: 'Past Show',
          startTime: now.subtract(const Duration(hours: 2)),
          endTime: now.subtract(const Duration(hours: 1)),
        ),
        EpgInfo(
          programTitle: 'Current Show',
          startTime: now.subtract(const Duration(minutes: 30)),
          endTime: now.add(const Duration(minutes: 30)),
        ),
        EpgInfo(
          programTitle: 'Future Show',
          startTime: now.add(const Duration(hours: 1)),
          endTime: now.add(const Duration(hours: 2)),
        ),
      ];
      
      final channelEpg = ChannelEpg(
        channelId: 'cnn',
        channelName: 'CNN',
        programs: programs,
      );
      
      expect(channelEpg.currentProgram?.programTitle, 'Current Show');
    });
    
    test('finds next program correctly', () {
      final now = DateTime.now();
      final programs = [
        EpgInfo(
          programTitle: 'Current Show',
          startTime: now.subtract(const Duration(minutes: 30)),
          endTime: now.add(const Duration(minutes: 30)),
        ),
        EpgInfo(
          programTitle: 'Next Show',
          startTime: now.add(const Duration(hours: 1)),
          endTime: now.add(const Duration(hours: 2)),
        ),
        EpgInfo(
          programTitle: 'Later Show',
          startTime: now.add(const Duration(hours: 3)),
          endTime: now.add(const Duration(hours: 4)),
        ),
      ];
      
      final channelEpg = ChannelEpg(
        channelId: 'cnn',
        channelName: 'CNN',
        programs: programs,
      );
      
      expect(channelEpg.nextProgram?.programTitle, 'Next Show');
    });
    
    test('returns null when no current program', () {
      final now = DateTime.now();
      final programs = [
        EpgInfo(
          programTitle: 'Past Show',
          startTime: now.subtract(const Duration(hours: 2)),
          endTime: now.subtract(const Duration(hours: 1)),
        ),
        EpgInfo(
          programTitle: 'Future Show',
          startTime: now.add(const Duration(hours: 1)),
          endTime: now.add(const Duration(hours: 2)),
        ),
      ];
      
      final channelEpg = ChannelEpg(
        channelId: 'cnn',
        channelName: 'CNN',
        programs: programs,
      );
      
      expect(channelEpg.currentProgram, null);
    });
    
    test('returns null when no next program', () {
      final now = DateTime.now();
      final programs = [
        EpgInfo(
          programTitle: 'Past Show',
          startTime: now.subtract(const Duration(hours: 2)),
          endTime: now.subtract(const Duration(hours: 1)),
        ),
        EpgInfo(
          programTitle: 'Current Show',
          startTime: now.subtract(const Duration(minutes: 30)),
          endTime: now.add(const Duration(minutes: 30)),
        ),
      ];
      
      final channelEpg = ChannelEpg(
        channelId: 'cnn',
        channelName: 'CNN',
        programs: programs,
      );
      
      expect(channelEpg.nextProgram, null);
    });
    
    test('getCurrentAndNext returns placeholders when no programs', () {
      final channelEpg = ChannelEpg(
        channelId: 'cnn',
        channelName: 'CNN',
        programs: [],
      );
      
      final result = channelEpg.getCurrentAndNext();
      
      expect(result['now']?.programTitle, 'Live Broadcast');
      expect(result['next']?.programTitle, 'Scheduled Program');
    });
    
    test('getCurrentAndNext returns actual programs when available', () {
      final now = DateTime.now();
      final programs = [
        EpgInfo(
          programTitle: 'Current Show',
          startTime: now.subtract(const Duration(minutes: 30)),
          endTime: now.add(const Duration(minutes: 30)),
        ),
        EpgInfo(
          programTitle: 'Next Show',
          startTime: now.add(const Duration(hours: 1)),
          endTime: now.add(const Duration(hours: 2)),
        ),
      ];
      
      final channelEpg = ChannelEpg(
        channelId: 'cnn',
        channelName: 'CNN',
        programs: programs,
      );
      
      final result = channelEpg.getCurrentAndNext();
      
      expect(result['now']?.programTitle, 'Current Show');
      expect(result['next']?.programTitle, 'Next Show');
    });
    
    test('creates placeholder channel EPG', () {
      final channelEpg = ChannelEpg.placeholder(
        channelId: 'cnn',
        channelName: 'CNN',
      );
      
      expect(channelEpg.channelId, 'cnn');
      expect(channelEpg.channelName, 'CNN');
      expect(channelEpg.programs.isEmpty, true);
    });
    
    test('serializes to JSON correctly', () {
      final programs = [
        EpgInfo(
          programTitle: 'Show 1',
          startTime: DateTime(2024, 1, 15, 14, 0),
          endTime: DateTime(2024, 1, 15, 15, 0),
        ),
      ];
      
      final channelEpg = ChannelEpg(
        channelId: 'cnn',
        channelName: 'CNN',
        programs: programs,
      );
      
      final json = channelEpg.toJson();
      
      expect(json['channelId'], 'cnn');
      expect(json['channelName'], 'CNN');
      expect(json['programs'], isA<List>());
      expect(json['programs'].length, 1);
    });
    
    test('deserializes from JSON correctly', () {
      final json = {
        'channelId': 'cnn',
        'channelName': 'CNN',
        'programs': [
          {
            'programTitle': 'Show 1',
            'startTime': DateTime(2024, 1, 15, 14, 0).toIso8601String(),
            'endTime': DateTime(2024, 1, 15, 15, 0).toIso8601String(),
          },
        ],
      };
      
      final channelEpg = ChannelEpg.fromJson(json);
      
      expect(channelEpg.channelId, 'cnn');
      expect(channelEpg.channelName, 'CNN');
      expect(channelEpg.programs.length, 1);
      expect(channelEpg.programs.first.programTitle, 'Show 1');
    });
    
    test('handles missing programs in JSON', () {
      final json = {
        'channelId': 'cnn',
        'channelName': 'CNN',
      };
      
      final channelEpg = ChannelEpg.fromJson(json);
      
      expect(channelEpg.channelId, 'cnn');
      expect(channelEpg.channelName, 'CNN');
      expect(channelEpg.programs.isEmpty, true);
    });
    
    test('handles missing channel info in JSON', () {
      final json = <String, dynamic>{};
      
      final channelEpg = ChannelEpg.fromJson(json);
      
      expect(channelEpg.channelId, '');
      expect(channelEpg.channelName, 'Unknown');
      expect(channelEpg.programs.isEmpty, true);
    });
  });
}

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_app/models/epg_info.dart';
import 'package:flutter_app/widgets/epg_display.dart';

void main() {
  group('EpgDisplay', () {
    testWidgets('displays placeholder EPG info', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: EpgDisplay.placeholder(),
          ),
        ),
      );
      
      // Should show "SCHEDULE" header
      expect(find.text('SCHEDULE'), findsOneWidget);
      
      // Should show "NOW PLAYING" label
      expect(find.text('NOW PLAYING'), findsOneWidget);
      
      // Should show "NEXT" label
      expect(find.text('NEXT'), findsOneWidget);
      
      // Should show placeholder titles
      expect(find.text('Live Broadcast'), findsOneWidget);
      expect(find.text('Scheduled Program'), findsOneWidget);
    });
    
    testWidgets('displays actual EPG data', (WidgetTester tester) async {
      final now = DateTime.now();
      final nowProgram = EpgInfo(
        programTitle: 'News Hour',
        description: 'Breaking news and analysis',
        startTime: now.subtract(const Duration(minutes: 30)),
        endTime: now.add(const Duration(minutes: 30)),
        category: 'News',
      );
      
      final nextProgram = EpgInfo(
        programTitle: 'Sports Tonight',
        description: 'Latest sports updates',
        startTime: now.add(const Duration(hours: 1)),
        endTime: now.add(const Duration(hours: 2)),
        category: 'Sports',
      );
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: EpgDisplay(
              nowPlaying: nowProgram,
              nextProgram: nextProgram,
              isDataAvailable: true,
            ),
          ),
        ),
      );
      
      // Should show program titles
      expect(find.text('News Hour'), findsOneWidget);
      expect(find.text('Sports Tonight'), findsOneWidget);
      
      // Should show descriptions
      expect(find.text('Breaking news and analysis'), findsOneWidget);
      expect(find.text('Latest sports updates'), findsOneWidget);
      
      // Should show categories
      expect(find.text('News'), findsOneWidget);
      expect(find.text('Sports'), findsOneWidget);
    });
    
    testWidgets('creates from ChannelEpg', (WidgetTester tester) async {
      final now = DateTime.now();
      final channelEpg = ChannelEpg(
        channelId: 'cnn',
        channelName: 'CNN',
        programs: [
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
        ],
      );
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: EpgDisplay.fromChannelEpg(channelEpg),
          ),
        ),
      );
      
      expect(find.text('Current Show'), findsOneWidget);
      expect(find.text('Next Show'), findsOneWidget);
    });
    
    testWidgets('shows info icon when EPG data not available', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: EpgDisplay.placeholder(),
          ),
        ),
      );
      
      // Should show info icon for unavailable data
      expect(find.byIcon(Icons.info_outline), findsOneWidget);
    });
    
    testWidgets('shows schedule icon', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: EpgDisplay.placeholder(),
          ),
        ),
      );
      
      // Should show schedule icon
      expect(find.byIcon(Icons.schedule), findsOneWidget);
    });
  });
  
  group('CompactEpgDisplay', () {
    testWidgets('displays compact placeholder info', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: CompactEpgDisplay.placeholder(),
          ),
        ),
      );
      
      // Should show "NOW:" prefix
      expect(find.textContaining('NOW:'), findsOneWidget);
      
      // Should show placeholder title
      expect(find.textContaining('Live Broadcast'), findsOneWidget);
    });
    
    testWidgets('displays compact actual data', (WidgetTester tester) async {
      final now = DateTime.now();
      final nowProgram = EpgInfo(
        programTitle: 'News Hour',
        startTime: now.subtract(const Duration(minutes: 30)),
        endTime: now.add(const Duration(minutes: 30)),
      );
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CompactEpgDisplay(
              nowPlaying: nowProgram,
              isDataAvailable: true,
            ),
          ),
        ),
      );
      
      // Should show program title
      expect(find.textContaining('News Hour'), findsOneWidget);
    });
    
    testWidgets('creates from ChannelEpg', (WidgetTester tester) async {
      final now = DateTime.now();
      final channelEpg = ChannelEpg(
        channelId: 'cnn',
        channelName: 'CNN',
        programs: [
          EpgInfo(
            programTitle: 'Current Show',
            startTime: now.subtract(const Duration(minutes: 30)),
            endTime: now.add(const Duration(minutes: 30)),
          ),
        ],
      );
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CompactEpgDisplay.fromChannelEpg(channelEpg),
          ),
        ),
      );
      
      expect(find.textContaining('Current Show'), findsOneWidget);
    });
  });
}

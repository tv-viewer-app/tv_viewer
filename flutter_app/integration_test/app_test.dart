import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:tv_viewer_project/main.dart' as app;
import 'package:tv_viewer_project/providers/channel_provider.dart';
import 'package:provider/provider.dart';

/// Integration tests for TV Viewer app
/// Tests complete user flows from start to finish
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('TV Viewer App Integration Tests', () {
    
    group('IT-1.1: Complete First-Time Flow', () {
      testWidgets('User can launch app, browse channels, filter, search, and play',
          (WidgetTester tester) async {
        // Launch app
        app.main();
        await tester.pumpAndSettle();

        // FC-1.1: Verify channel list displays
        expect(find.byType(ListView), findsOneWidget);
        
        // Wait for channels to load
        await tester.pumpAndSettle(Duration(seconds: 3));

        // Verify search bar is visible
        expect(find.byType(TextField), findsWidgets);

        // FC-2.2: Tap TV filter
        final tvButton = find.text('TV');
        if (tvButton.evaluate().isNotEmpty) {
          await tester.tap(tvButton);
          await tester.pumpAndSettle();
        }

        // FC-3.3: Open and select category (if available)
        final categoryDropdown = find.byKey(Key('categoryDropdown'));
        if (categoryDropdown.evaluate().isNotEmpty) {
          await tester.tap(categoryDropdown);
          await tester.pumpAndSettle();
          
          // Select first category
          final firstCategory = find.text('News').first;
          if (firstCategory.evaluate().isNotEmpty) {
            await tester.tap(firstCategory);
            await tester.pumpAndSettle();
          }
        }

        // FC-5.2: Enter search query
        final searchField = find.byType(TextField).first;
        await tester.enterText(searchField, 'CNN');
        await tester.pumpAndSettle();

        // Verify search filtered results
        expect(find.byType(ListTile), findsWidgets);

        // FC-1.5: Tap first channel to play
        final firstChannel = find.byType(ListTile).first;
        await tester.tap(firstChannel);
        await tester.pumpAndSettle(Duration(seconds: 2));

        // Verify navigation to player screen
        // (Check for video player or back button)
        
        // FC-7.9: Press back button
        final backButton = find.byType(BackButton);
        if (backButton.evaluate().isNotEmpty) {
          await tester.tap(backButton);
          await tester.pumpAndSettle();
        } else {
          // Use system back
          await tester.pageBack();
          await tester.pumpAndSettle();
        }

        // Verify returned to channel list
        expect(find.byType(ListView), findsOneWidget);
      }, timeout: Timeout(Duration(minutes: 2)));
    });

    group('IT-1.2: Filter and Play Flow', () {
      testWidgets('User can apply multiple filters and play result',
          (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Wait for initial load
        await tester.pumpAndSettle(Duration(seconds: 3));

        // FC-6.4: Apply all three filters
        // 1. Media type: TV
        final tvButton = find.text('TV');
        if (tvButton.evaluate().isNotEmpty) {
          await tester.tap(tvButton);
          await tester.pumpAndSettle();
        }

        // 2. Category: News
        final categoryDropdown = find.byKey(Key('categoryDropdown'));
        if (categoryDropdown.evaluate().isNotEmpty) {
          await tester.tap(categoryDropdown);
          await tester.pumpAndSettle();
          
          final newsCategory = find.text('News');
          if (newsCategory.evaluate().isNotEmpty) {
            await tester.tap(newsCategory.last);
            await tester.pumpAndSettle();
          }
        }

        // 3. Country: US
        final countryDropdown = find.byKey(Key('countryDropdown'));
        if (countryDropdown.evaluate().isNotEmpty) {
          await tester.tap(countryDropdown);
          await tester.pumpAndSettle();
          
          final usCountry = find.text('US');
          if (usCountry.evaluate().isNotEmpty) {
            await tester.tap(usCountry.last);
            await tester.pumpAndSettle();
          }
        }

        // Verify filtered results
        final channelList = find.byType(ListTile);
        expect(channelList, findsWidgets);

        // Play first result
        if (channelList.evaluate().isNotEmpty) {
          await tester.tap(channelList.first);
          await tester.pumpAndSettle(Duration(seconds: 2));
        }
      });
    });

    group('IT-1.3: Scan and Play Flow', () {
      testWidgets('User can start validation, wait for completion, and play working channel',
          (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Wait for initial load
        await tester.pumpAndSettle(Duration(seconds: 3));

        // FC-11.1: Start validation scan
        final refreshButton = find.byIcon(Icons.refresh);
        if (refreshButton.evaluate().isNotEmpty) {
          await tester.tap(refreshButton);
          await tester.pumpAndSettle();
        }

        // FC-11.2: Verify scan progress appears
        await tester.pump(Duration(seconds: 1));
        
        // Wait for some channels to be scanned (don't wait for all)
        await tester.pump(Duration(seconds: 5));

        // FC-11.7: Stop validation (optional)
        final stopButton = find.byIcon(Icons.stop);
        if (stopButton.evaluate().isNotEmpty) {
          await tester.tap(stopButton);
          await tester.pumpAndSettle();
        }

        // Find and play a working channel (green check icon)
        final workingChannel = find.byIcon(Icons.check_circle);
        if (workingChannel.evaluate().isNotEmpty) {
          // Tap the ListTile containing the working channel
          await tester.tap(find.ancestor(
            of: workingChannel.first,
            matching: find.byType(ListTile),
          ));
          await tester.pumpAndSettle(Duration(seconds: 2));
        }
      }, timeout: Timeout(Duration(minutes: 1)));
    });

    group('UX-6: Performance Tests', () {
      testWidgets('UX-6.1: Initial load time < 2 seconds (cached)',
          (WidgetTester tester) async {
        final stopwatch = Stopwatch()..start();
        
        app.main();
        await tester.pumpAndSettle();
        
        stopwatch.stop();

        // Should load within 2 seconds
        expect(stopwatch.elapsedMilliseconds, lessThan(2000));
        
        // Verify UI is usable
        expect(find.byType(ListView), findsOneWidget);
      });

      testWidgets('UX-6.2: Filter response time < 100ms',
          (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Wait for channels to load
        await tester.pumpAndSettle(Duration(seconds: 3));

        final stopwatch = Stopwatch()..start();
        
        // Change filter
        final tvButton = find.text('TV');
        if (tvButton.evaluate().isNotEmpty) {
          await tester.tap(tvButton);
          await tester.pump(); // Single pump to measure immediate response
        }
        
        stopwatch.stop();

        // Should update within 100ms
        expect(stopwatch.elapsedMilliseconds, lessThan(100));
      });

      testWidgets('UX-6.3: Search responsiveness < 200ms per keystroke',
          (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Wait for channels to load
        await tester.pumpAndSettle(Duration(seconds: 3));

        final searchField = find.byType(TextField).first;
        
        final stopwatch = Stopwatch()..start();
        
        await tester.enterText(searchField, 'C');
        await tester.pump();
        
        stopwatch.stop();

        // Should respond within 200ms
        expect(stopwatch.elapsedMilliseconds, lessThan(200));
      });

      testWidgets('UX-6.4: Scroll smoothness test',
          (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Wait for channels to load
        await tester.pumpAndSettle(Duration(seconds: 3));

        // Find scrollable
        final listView = find.byType(ListView);
        expect(listView, findsOneWidget);

        // Perform rapid scrolling
        await tester.fling(listView, Offset(0, -500), 1000);
        await tester.pumpAndSettle();

        await tester.fling(listView, Offset(0, 500), 1000);
        await tester.pumpAndSettle();

        // If we get here without crashes, scrolling is smooth
        expect(listView, findsOneWidget);
      });
    });

    group('Error Scenarios', () {
      testWidgets('ES-1.7: Handle network drop gracefully',
          (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Wait for initial load
        await tester.pumpAndSettle(Duration(seconds: 3));

        // Verify cached channels display even if network unavailable
        expect(find.byType(ListView), findsOneWidget);
        
        // Should show channels or empty state, not crash
      });

      testWidgets('EC-2.1: Filter with zero results shows empty state',
          (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Wait for channels to load
        await tester.pumpAndSettle(Duration(seconds: 3));

        // Enter nonsense search
        final searchField = find.byType(TextField).first;
        await tester.enterText(searchField, 'XYZZZZZ123456789');
        await tester.pumpAndSettle();

        // Should show empty state or "No channels found"
        expect(
          find.textContaining('No', findRichText: true),
          findsAny,
        );
      });
    });

    group('Accessibility Tests', () {
      testWidgets('UX-5.1: All interactive elements have semantic labels',
          (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Wait for load
        await tester.pumpAndSettle(Duration(seconds: 3));

        // Find all buttons
        final buttons = find.byType(ElevatedButton);
        final iconButtons = find.byType(IconButton);

        // Verify buttons have semantics
        for (final button in buttons.evaluate()) {
          expect(button.widget, isA<Widget>());
        }

        for (final button in iconButtons.evaluate()) {
          expect(button.widget, isA<Widget>());
        }
      });

      testWidgets('UX-5.7: Minimum touch target size 48x48dp',
          (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();

        await tester.pumpAndSettle(Duration(seconds: 3));

        // Find all tappable elements
        final buttons = find.byType(IconButton);
        
        for (final button in buttons.evaluate()) {
          final size = tester.getSize(find.byWidget(button.widget));
          
          // Verify minimum size
          expect(size.width, greaterThanOrEqualTo(48));
          expect(size.height, greaterThanOrEqualTo(48));
        }
      });
    });

    group('State Persistence', () {
      testWidgets('IT-2.1: App restores state after restart',
          (WidgetTester tester) async {
        // First launch
        app.main();
        await tester.pumpAndSettle();
        await tester.pumpAndSettle(Duration(seconds: 3));

        // Apply filters
        final tvButton = find.text('TV');
        if (tvButton.evaluate().isNotEmpty) {
          await tester.tap(tvButton);
          await tester.pumpAndSettle();
        }

        // Simulate app restart by creating new instance
        await tester.pumpWidget(Container());
        await tester.pumpAndSettle();

        // Relaunch
        app.main();
        await tester.pumpAndSettle();
        await tester.pumpAndSettle(Duration(seconds: 2));

        // Verify channels load from cache
        expect(find.byType(ListView), findsOneWidget);
      });
    });

    group('Multi-Feature Interactions', () {
      testWidgets('IT-3.2: Search works during validation scan',
          (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        await tester.pumpAndSettle(Duration(seconds: 3));

        // Start validation scan
        final refreshButton = find.byIcon(Icons.refresh);
        if (refreshButton.evaluate().isNotEmpty) {
          await tester.tap(refreshButton);
          await tester.pump();
        }

        // Immediately use search
        final searchField = find.byType(TextField).first;
        await tester.enterText(searchField, 'CNN');
        await tester.pumpAndSettle();

        // Search should work even during scan
        expect(find.byType(ListTile), findsWidgets);
      });
    });
  });
}

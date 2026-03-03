import 'package:flutter_test/flutter_test.dart';
import 'package:tv_viewer/providers/channel_provider.dart';
import 'package:tv_viewer/models/channel.dart';

/// Unit tests for ChannelProvider
/// Coverage: Filtering logic, state management, search functionality
void main() {
  group('ChannelProvider Tests', () {
    late ChannelProvider provider;
    late List<Channel> sampleChannels;

    setUp(() {
      provider = ChannelProvider();
      
      // Create sample channels for testing
      sampleChannels = [
        Channel(
          name: 'CNN International',
          url: 'http://example.com/cnn.m3u8',
          category: 'News',
          country: 'US',
          logo: 'http://example.com/cnn.png',
          language: 'English',
          mediaType: 'TV',
          resolution: '720p',
          bitrate: 2500000,
          isWorking: true,
        ),
        Channel(
          name: 'BBC World News',
          url: 'http://example.com/bbc.m3u8',
          category: 'News',
          country: 'UK',
          logo: 'http://example.com/bbc.png',
          language: 'English',
          mediaType: 'TV',
          resolution: '1080p',
          bitrate: 3500000,
          isWorking: true,
        ),
        Channel(
          name: 'ESPN Sports',
          url: 'http://example.com/espn.m3u8',
          category: 'Sports',
          country: 'US',
          logo: 'http://example.com/espn.png',
          language: 'English',
          mediaType: 'TV',
          resolution: '720p',
          bitrate: 2000000,
          isWorking: true,
        ),
        Channel(
          name: 'BBC Radio 1',
          url: 'http://example.com/radio1.mp3',
          category: 'Radio',
          country: 'UK',
          logo: 'http://example.com/radio1.png',
          language: 'English',
          mediaType: 'Radio',
          resolution: '',
          bitrate: 128000,
          isWorking: true,
        ),
        Channel(
          name: 'France 24',
          url: 'http://example.com/france24.m3u8',
          category: 'News',
          country: 'FR',
          logo: 'http://example.com/france24.png',
          language: 'French',
          mediaType: 'TV',
          resolution: '720p',
          bitrate: 2500000,
          isWorking: false,
        ),
      ];

      // Manually set channels (bypassing network calls for testing)
      provider.setChannelsForTesting(sampleChannels);
    });

    group('Media Type Filtering', () {
      test('FC-2.1: Default "All" filter shows both TV and Radio', () {
        final filtered = provider.filteredChannels;
        
        expect(filtered.length, 5);
        expect(filtered.where((ch) => ch.mediaType == 'TV').length, 4);
        expect(filtered.where((ch) => ch.mediaType == 'Radio').length, 1);
      });

      test('FC-2.2: Filter TV channels only', () {
        provider.setMediaType('TV');
        final filtered = provider.filteredChannels;
        
        expect(filtered.length, 4);
        expect(filtered.every((ch) => ch.mediaType == 'TV'), true);
      });

      test('FC-2.3: Filter Radio channels only', () {
        provider.setMediaType('Radio');
        final filtered = provider.filteredChannels;
        
        expect(filtered.length, 1);
        expect(filtered.every((ch) => ch.mediaType == 'Radio'), true);
        expect(filtered[0].name, 'BBC Radio 1');
      });

      test('FC-2.4: Toggle back to All from TV', () {
        provider.setMediaType('TV');
        expect(provider.filteredChannels.length, 4);
        
        provider.setMediaType('All');
        expect(provider.filteredChannels.length, 5);
      });
    });

    group('Category Filtering', () {
      test('FC-3.2: Default "All Categories" shows all channels', () {
        final filtered = provider.filteredChannels;
        expect(filtered.length, 5);
      });

      test('FC-3.3: Select specific category "News"', () {
        provider.setCategory('News');
        final filtered = provider.filteredChannels;
        
        expect(filtered.length, 3);
        expect(filtered.every((ch) => ch.category == 'News'), true);
      });

      test('FC-3.3: Select specific category "Sports"', () {
        provider.setCategory('Sports');
        final filtered = provider.filteredChannels;
        
        expect(filtered.length, 1);
        expect(filtered[0].name, 'ESPN Sports');
      });

      test('FC-3.5: Reset category filter', () {
        provider.setCategory('News');
        expect(provider.filteredChannels.length, 3);
        
        provider.setCategory('All Categories');
        expect(provider.filteredChannels.length, 5);
      });

      test('FC-3.1: Categories list populated correctly', () {
        final categories = provider.categories;
        
        expect(categories.contains('News'), true);
        expect(categories.contains('Sports'), true);
        expect(categories.contains('Radio'), true);
        expect(categories.length, 3);
      });

      test('EC-2.1: Category with zero results', () {
        provider.setCategory('NonExistentCategory');
        final filtered = provider.filteredChannels;
        
        expect(filtered.isEmpty, true);
      });
    });

    group('Country Filtering', () {
      test('FC-4.2: Default "All Countries" shows all channels', () {
        final filtered = provider.filteredChannels;
        expect(filtered.length, 5);
      });

      test('FC-4.3: Select specific country "US"', () {
        provider.setCountry('US');
        final filtered = provider.filteredChannels;
        
        expect(filtered.length, 2);
        expect(filtered.every((ch) => ch.country == 'US'), true);
      });

      test('FC-4.3: Select specific country "UK"', () {
        provider.setCountry('UK');
        final filtered = provider.filteredChannels;
        
        expect(filtered.length, 2);
        expect(filtered.every((ch) => ch.country == 'UK'), true);
      });

      test('FC-4.5: Reset country filter', () {
        provider.setCountry('US');
        expect(provider.filteredChannels.length, 2);
        
        provider.setCountry('All Countries');
        expect(provider.filteredChannels.length, 5);
      });

      test('FC-4.1: Countries list populated correctly', () {
        final countries = provider.countries;
        
        expect(countries.contains('US'), true);
        expect(countries.contains('UK'), true);
        expect(countries.contains('FR'), true);
        expect(countries.length, 3);
      });

      test('FC-4.4: Countries sorted alphabetically', () {
        final countries = provider.countries;
        final sorted = List<String>.from(countries)..sort();
        
        expect(countries, equals(sorted));
      });
    });

    group('Search Functionality', () {
      test('FC-5.2: Search by channel name', () {
        provider.setSearchQuery('CNN');
        final filtered = provider.filteredChannels;
        
        expect(filtered.length, 1);
        expect(filtered[0].name, 'CNN International');
      });

      test('FC-5.3: Case-insensitive search', () {
        provider.setSearchQuery('cnn');
        expect(provider.filteredChannels.length, 1);
        
        provider.setSearchQuery('CNN');
        expect(provider.filteredChannels.length, 1);
        
        provider.setSearchQuery('CnN');
        expect(provider.filteredChannels.length, 1);
      });

      test('FC-5.7: Partial match search', () {
        provider.setSearchQuery('BBC');
        final filtered = provider.filteredChannels;
        
        // Should match both "BBC World News" and "BBC Radio 1"
        expect(filtered.length, 2);
        expect(filtered.every((ch) => ch.name.contains('BBC')), true);
      });

      test('FC-5.5: Clear search', () {
        provider.setSearchQuery('CNN');
        expect(provider.filteredChannels.length, 1);
        
        provider.setSearchQuery('');
        expect(provider.filteredChannels.length, 5);
      });

      test('FC-5.6: Search with no results', () {
        provider.setSearchQuery('XYZ123NotFound');
        final filtered = provider.filteredChannels;
        
        expect(filtered.isEmpty, true);
      });

      test('EC-2.2: Search with only spaces', () {
        provider.setSearchQuery('   ');
        final filtered = provider.filteredChannels;
        
        // Should either show all or none based on trim logic
        expect(filtered.length, anyOf(0, 5));
      });

      test('EC-2.3: Search with special characters', () {
        provider.setSearchQuery(r'!@#$%');
        final filtered = provider.filteredChannels;
        
        // Should not crash, returns no matches
        expect(filtered.isEmpty, true);
      });
    });

    group('Combined Filters', () {
      test('FC-6.1: Media type + Category', () {
        provider.setMediaType('TV');
        provider.setCategory('News');
        final filtered = provider.filteredChannels;
        
        expect(filtered.length, 3);
        expect(filtered.every((ch) => ch.mediaType == 'TV' && ch.category == 'News'), true);
      });

      test('FC-6.2: Media type + Country', () {
        provider.setMediaType('Radio');
        provider.setCountry('UK');
        final filtered = provider.filteredChannels;
        
        expect(filtered.length, 1);
        expect(filtered[0].name, 'BBC Radio 1');
      });

      test('FC-6.3: Category + Country', () {
        provider.setCategory('News');
        provider.setCountry('US');
        final filtered = provider.filteredChannels;
        
        expect(filtered.length, 1);
        expect(filtered[0].name, 'CNN International');
      });

      test('FC-6.4: All three filters', () {
        provider.setMediaType('TV');
        provider.setCategory('News');
        provider.setCountry('US');
        final filtered = provider.filteredChannels;
        
        expect(filtered.length, 1);
        expect(filtered[0].name, 'CNN International');
      });

      test('FC-6.5: Filters + Search', () {
        provider.setMediaType('TV');
        provider.setCategory('News');
        provider.setSearchQuery('BBC');
        final filtered = provider.filteredChannels;
        
        expect(filtered.length, 1);
        expect(filtered[0].name, 'BBC World News');
      });

      test('FC-6.6: Clear all filters', () {
        // Apply all filters
        provider.setMediaType('TV');
        provider.setCategory('News');
        provider.setCountry('US');
        provider.setSearchQuery('CNN');
        expect(provider.filteredChannels.length, 1);
        
        // Clear all
        provider.setMediaType('All');
        provider.setCategory('All Categories');
        provider.setCountry('All Countries');
        provider.setSearchQuery('');
        expect(provider.filteredChannels.length, 5);
      });

      test('EC-2.1: Combined filters with zero results', () {
        provider.setMediaType('Radio');
        provider.setCategory('Sports');
        final filtered = provider.filteredChannels;
        
        expect(filtered.isEmpty, true);
      });
    });

    group('Validation State', () {
      test('FC-11.1: Initial scan progress state', () {
        expect(provider.isScanning, false);
        expect(provider.scanProgress, 0);
        expect(provider.scanTotal, 0);
      });

      test('FC-11.2: Scan progress updates', () {
        // Simulate scan progress
        provider.updateScanProgress(10, 100, 8, 2);
        
        expect(provider.scanProgress, 10);
        expect(provider.scanTotal, 100);
        expect(provider.workingCount, 8);
        expect(provider.failedCount, 2);
      });

      test('FC-11.6: Update channel working status', () {
        final channel = sampleChannels[4]; // France 24 (initially not working)
        expect(channel.isWorking, false);
        
        // Update status
        provider.updateChannelStatus(channel.url, true);
        
        final updated = provider.channels.firstWhere((ch) => ch.url == channel.url);
        expect(updated.isWorking, true);
      });
    });

    group('Loading State', () {
      test('Initial loading state', () {
        final freshProvider = ChannelProvider();
        expect(freshProvider.isLoading, false);
      });

      test('Loading state during fetch', () async {
        final freshProvider = ChannelProvider();
        
        // Start loading
        final future = freshProvider.fetchChannels();
        expect(freshProvider.isLoading, true);
        
        // Wait for completion
        await future;
        expect(freshProvider.isLoading, false);
      });
    });

    group('Edge Cases', () {
      test('EC-2.5: Rapid filter changes', () {
        // Rapidly change filters
        for (int i = 0; i < 100; i++) {
          provider.setMediaType(i % 2 == 0 ? 'TV' : 'Radio');
          provider.setCategory(i % 3 == 0 ? 'News' : 'Sports');
          provider.setCountry(i % 2 == 0 ? 'US' : 'UK');
        }
        
        // Should complete without errors
        expect(provider.filteredChannels, isNotEmpty);
      });

      test('EC-DATA-1: Empty channel list', () {
        provider.setChannelsForTesting([]);
        
        expect(provider.channels.isEmpty, true);
        expect(provider.filteredChannels.isEmpty, true);
        expect(provider.categories.isEmpty, true);
        expect(provider.countries.isEmpty, true);
      });

      test('EC-DATA-2: Single channel', () {
        provider.setChannelsForTesting([sampleChannels[0]]);
        
        expect(provider.channels.length, 1);
        expect(provider.filteredChannels.length, 1);
      });

      test('EC-1.10: Very large channel list (10000+)', () {
        final largeList = List.generate(10000, (i) => Channel(
          name: 'Channel $i',
          url: 'http://example.com/channel$i.m3u8',
          category: 'Category ${i % 10}',
          country: 'Country ${i % 50}',
          mediaType: i % 2 == 0 ? 'TV' : 'Radio',
        ));
        
        provider.setChannelsForTesting(largeList);
        
        expect(provider.channels.length, 10000);
        
        // Test filtering performance
        final stopwatch = Stopwatch()..start();
        provider.setCategory('Category 5');
        stopwatch.stop();
        
        expect(stopwatch.elapsedMilliseconds, lessThan(200));
        expect(provider.filteredChannels.length, 1000);
      });
    });

    group('Performance', () {
      test('PT-1.4: Filter application time < 200ms', () {
        // Create medium dataset (500 channels)
        final mediumList = List.generate(500, (i) => Channel(
          name: 'Channel $i',
          url: 'http://example.com/channel$i.m3u8',
          category: 'Category ${i % 20}',
          country: 'Country ${i % 50}',
          mediaType: i % 2 == 0 ? 'TV' : 'Radio',
        ));
        
        provider.setChannelsForTesting(mediumList);
        
        final stopwatch = Stopwatch()..start();
        provider.setCategory('Category 5');
        provider.setCountry('Country 10');
        provider.setMediaType('TV');
        stopwatch.stop();
        
        expect(stopwatch.elapsedMilliseconds, lessThan(200));
      });

      test('PT-1.5: Search performance < 100ms per keystroke', () {
        final largeList = List.generate(5000, (i) => Channel(
          name: 'Channel $i',
          url: 'http://example.com/channel$i.m3u8',
          category: 'Category ${i % 20}',
        ));
        
        provider.setChannelsForTesting(largeList);
        
        final stopwatch = Stopwatch()..start();
        provider.setSearchQuery('Channel 123');
        stopwatch.stop();
        
        expect(stopwatch.elapsedMilliseconds, lessThan(100));
      });
    });
  });
}

// Extension for testing
extension ChannelProviderTesting on ChannelProvider {
  void setChannelsForTesting(List<Channel> channels) {
    // This would need to be added to the actual ChannelProvider class
    // For now, this shows the concept
  }
  
  void updateScanProgress(int progress, int total, int working, int failed) {
    // Test helper method
  }
  
  void updateChannelStatus(String url, bool isWorking) {
    // Test helper method
  }
}

// Example: How to integrate the feedback screen into home_screen.dart
// This file shows the exact changes needed to add the new feedback screen

// =============================================================================
// STEP 1: Add import at the top of home_screen.dart
// =============================================================================

import 'feedback_screen.dart';  // ADD THIS LINE


// =============================================================================
// STEP 2: Update the popup menu handler (around line 235)
// =============================================================================

// BEFORE:
void _handleMenuSelection(String value) async {
  switch (value) {
    case 'help':
      Navigator.push(
        context,
        MaterialPageRoute(builder: (context) => const HelpScreen()),
      );
      break;
    case 'diagnostics':
      Navigator.push(
        context,
        MaterialPageRoute(builder: (context) => const DiagnosticsScreen()),
      );
      break;
    case 'feedback':
      FeedbackService.showFeedbackDialog(context);  // OLD METHOD
      break;
    // ... rest of cases
  }
}

// AFTER:
void _handleMenuSelection(String value) async {
  switch (value) {
    case 'help':
      Navigator.push(
        context,
        MaterialPageRoute(builder: (context) => const HelpScreen()),
      );
      break;
    case 'diagnostics':
      Navigator.push(
        context,
        MaterialPageRoute(builder: (context) => const DiagnosticsScreen()),
      );
      break;
    case 'feedback':
      // Navigate to the new full feedback screen with star rating
      Navigator.push(
        context,
        MaterialPageRoute(builder: (context) => const FeedbackScreen()),
      );
      break;
    // ... rest of cases
  }
}


// =============================================================================
// ALTERNATIVE: Keep both options (quick feedback dialog + full screen)
// =============================================================================

// If you want to offer both a quick feedback dialog AND the detailed screen:

PopupMenuButton<String>(
  onSelected: (value) async {
    switch (value) {
      case 'feedback_quick':
        // Quick feedback dialog (existing)
        FeedbackService.showFeedbackDialog(context);
        break;
      case 'feedback_detailed':
        // New detailed feedback screen with star rating
        Navigator.push(
          context,
          MaterialPageRoute(builder: (context) => const FeedbackScreen()),
        );
        break;
      // ... other cases
    }
  },
  itemBuilder: (context) => [
    // ... other menu items ...
    
    const PopupMenuItem(
      value: 'feedback_quick',
      child: Row(
        children: [
          Icon(Icons.chat_bubble_outline),
          SizedBox(width: 12),
          Text('Quick Feedback'),
        ],
      ),
    ),
    const PopupMenuItem(
      value: 'feedback_detailed',
      child: Row(
        children: [
          Icon(Icons.star_rate),
          SizedBox(width: 12),
          Text('Rate & Review'),
        ],
      ),
    ),
    
    // ... rest of menu items ...
  ],
)


// =============================================================================
// ALTERNATIVE: Add a FloatingActionButton for feedback
// =============================================================================

@override
Widget build(BuildContext context) {
  return Scaffold(
    appBar: AppBar(
      // ... app bar configuration
    ),
    body: // ... your body widget
    floatingActionButton: FloatingActionButton.extended(
      onPressed: () {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (context) => const FeedbackScreen()),
        );
      },
      icon: const Icon(Icons.star_rate),
      label: const Text('Rate Us'),
    ),
  );
}


// =============================================================================
// ALTERNATIVE: Add to a settings/about screen
// =============================================================================

class SettingsScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        children: [
          ListTile(
            leading: const Icon(Icons.star_rate),
            title: const Text('Rate & Provide Feedback'),
            subtitle: const Text('Help us improve the app'),
            trailing: const Icon(Icons.arrow_forward_ios, size: 16),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => const FeedbackScreen(),
                ),
              );
            },
          ),
          // ... other settings
        ],
      ),
    );
  }
}


// =============================================================================
// ALTERNATIVE: Show after specific events (channel scan, etc.)
// =============================================================================

void _onChannelScanComplete() async {
  // ... scan completion logic ...
  
  // Show a dialog asking for feedback
  final shouldRate = await showDialog<bool>(
    context: context,
    builder: (context) => AlertDialog(
      title: const Text('Scan Complete!'),
      content: const Text(
        'We found ${channelCount} channels. '
        'Would you like to rate your experience?'
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, false),
          child: const Text('Maybe Later'),
        ),
        ElevatedButton.icon(
          onPressed: () => Navigator.pop(context, true),
          icon: const Icon(Icons.star),
          label: const Text('Rate Now'),
        ),
      ],
    ),
  );
  
  if (shouldRate == true && mounted) {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const FeedbackScreen()),
    );
  }
}


// =============================================================================
// TESTING: Test the feedback screen directly
// =============================================================================

void main() {
  runApp(
    MaterialApp(
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF0078D4)),
      ),
      home: const FeedbackScreen(),  // Test the screen directly
    ),
  );
}


// =============================================================================
// USAGE: Programmatic feedback submission
// =============================================================================

import 'package:tv_viewer/services/feedback_service.dart';

Future<void> submitProgrammaticFeedback() async {
  final result = await FeedbackService.submitFeedbackWithRating(
    rating: 5,
    feedbackText: 'Great app! Works perfectly.',
    includeDeviceInfo: true,
  );
  
  if (result.isSuccess) {
    print('Feedback submitted successfully!');
  } else if (result.isCopiedToClipboard) {
    print('Feedback copied to clipboard');
    print('GitHub URL: ${result.githubUrl}');
  } else {
    print('Error: ${result.message}');
  }
}


// =============================================================================
// TESTING: Test star rating widget independently
// =============================================================================

import 'package:tv_viewer/widgets/star_rating.dart';

class StarRatingDemo extends StatefulWidget {
  @override
  State<StarRatingDemo> createState() => _StarRatingDemoState();
}

class _StarRatingDemoState extends State<StarRatingDemo> {
  int rating = 0;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Star Rating Demo')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              'Your Rating: $rating/5',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 20),
            StarRating(
              rating: rating,
              size: 50,
              onRatingChanged: (newRating) {
                setState(() => rating = newRating);
              },
            ),
          ],
        ),
      ),
    );
  }
}

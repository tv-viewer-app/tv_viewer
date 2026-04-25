import 'package:flutter/material.dart';

/// A reusable star rating widget that allows users to select a rating from 1 to 5 stars.
///
/// This widget displays a row of stars that can be tapped to select a rating.
/// Stars are filled up to the selected rating and can be interactive or read-only.
class StarRating extends StatefulWidget {
  /// The current rating value (1-5)
  final int rating;

  /// Callback when the rating changes
  final ValueChanged<int>? onRatingChanged;

  /// Size of each star icon
  final double size;

  /// Color of filled stars
  final Color? filledColor;

  /// Color of empty stars
  final Color? emptyColor;

  /// Whether the rating can be changed by user interaction
  final bool interactive;

  /// Number of stars to display
  final int starCount;

  const StarRating({
    Key? key,
    required this.rating,
    this.onRatingChanged,
    this.size = 40.0,
    this.filledColor,
    this.emptyColor,
    this.interactive = true,
    this.starCount = 5,
  }) : super(key: key);

  @override
  State<StarRating> createState() => _StarRatingState();
}

class _StarRatingState extends State<StarRating> {
  late int _currentRating;

  @override
  void initState() {
    super.initState();
    _currentRating = widget.rating;
  }

  @override
  void didUpdateWidget(StarRating oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.rating != oldWidget.rating) {
      _currentRating = widget.rating;
    }
  }

  void _updateRating(int index) {
    if (!widget.interactive) return;

    setState(() {
      _currentRating = index + 1;
    });

    widget.onRatingChanged?.call(_currentRating);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final filledColor = widget.filledColor ?? theme.colorScheme.primary;
    final emptyColor = widget.emptyColor ?? theme.colorScheme.outline;

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(
        widget.starCount,
        (index) {
          final isFilled = index < _currentRating;
          return GestureDetector(
            onTap: widget.interactive ? () => _updateRating(index) : null,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4.0),
              child: Icon(
                isFilled ? Icons.star : Icons.star_border,
                size: widget.size,
                color: isFilled ? filledColor : emptyColor,
              ),
            ),
          );
        },
      ),
    );
  }
}

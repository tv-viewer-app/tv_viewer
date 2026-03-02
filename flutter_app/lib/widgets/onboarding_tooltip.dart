import 'package:flutter/material.dart';
import 'dart:math' as math;

/// Position of the arrow relative to the tooltip
enum ArrowPosition {
  top,
  bottom,
  left,
  right,
}

/// Custom tooltip overlay for onboarding
class OnboardingTooltip extends StatefulWidget {
  final String message;
  final GlobalKey targetKey;
  final VoidCallback onDismiss;
  final ArrowPosition arrowPosition;
  final Duration animationDuration;

  const OnboardingTooltip({
    super.key,
    required this.message,
    required this.targetKey,
    required this.onDismiss,
    this.arrowPosition = ArrowPosition.bottom,
    this.animationDuration = const Duration(milliseconds: 300),
  });

  @override
  State<OnboardingTooltip> createState() => _OnboardingTooltipState();
}

class _OnboardingTooltipState extends State<OnboardingTooltip>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: widget.animationDuration,
    );

    _fadeAnimation = CurvedAnimation(
      parent: _controller,
      curve: Curves.easeInOut,
    );

    _scaleAnimation = Tween<double>(
      begin: 0.8,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOutBack,
    ));

    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleDismiss() async {
    await _controller.reverse();
    widget.onDismiss();
  }

  Offset? _getTargetPosition() {
    final renderBox =
        widget.targetKey.currentContext?.findRenderObject() as RenderBox?;
    if (renderBox == null) return null;
    return renderBox.localToGlobal(Offset.zero);
  }

  Size? _getTargetSize() {
    final renderBox =
        widget.targetKey.currentContext?.findRenderObject() as RenderBox?;
    return renderBox?.size;
  }

  @override
  Widget build(BuildContext context) {
    final targetPosition = _getTargetPosition();
    final targetSize = _getTargetSize();

    if (targetPosition == null || targetSize == null) {
      // Target not found, dismiss
      WidgetsBinding.instance.addPostFrameCallback((_) => widget.onDismiss());
      return const SizedBox.shrink();
    }

    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Stack(
          children: [
            // Semi-transparent backdrop
            Positioned.fill(
              child: GestureDetector(
                onTap: _handleDismiss,
                child: Container(
                  color: Colors.black.withOpacity(0.5 * _fadeAnimation.value),
                ),
              ),
            ),

            // Highlight the target area
            Positioned(
              left: targetPosition.dx - 8,
              top: targetPosition.dy - 8,
              child: IgnorePointer(
                child: Container(
                  width: targetSize.width + 16,
                  height: targetSize.height + 16,
                  decoration: BoxDecoration(
                    color: Colors.transparent,
                    border: Border.all(
                      color: Theme.of(context)
                          .colorScheme
                          .primary
                          .withOpacity(_fadeAnimation.value),
                      width: 2,
                    ),
                    borderRadius: BorderRadius.circular(8),
                    boxShadow: [
                      BoxShadow(
                        color: Theme.of(context)
                            .colorScheme
                            .primary
                            .withOpacity(0.3 * _fadeAnimation.value),
                        blurRadius: 20,
                        spreadRadius: 5,
                      ),
                    ],
                  ),
                ),
              ),
            ),

            // Tooltip content
            Positioned(
              left: _calculateTooltipLeft(
                  targetPosition, targetSize, context),
              top: _calculateTooltipTop(
                  targetPosition, targetSize, context),
              child: FadeTransition(
                opacity: _fadeAnimation,
                child: ScaleTransition(
                  scale: _scaleAnimation,
                  child: _buildTooltipContent(context),
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildTooltipContent(BuildContext context) {
    return Material(
      elevation: 8,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        constraints: const BoxConstraints(maxWidth: 280),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.primaryContainer,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              widget.message,
              style: TextStyle(
                color: Theme.of(context).colorScheme.onPrimaryContainer,
                fontSize: 15,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: _handleDismiss,
                style: TextButton.styleFrom(
                  backgroundColor: Theme.of(context).colorScheme.primary,
                  foregroundColor: Theme.of(context).colorScheme.onPrimary,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                ),
                child: const Text('Got it'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  double _calculateTooltipLeft(
      Offset targetPosition, Size targetSize, BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    const tooltipWidth = 280.0;
    const padding = 16.0;

    switch (widget.arrowPosition) {
      case ArrowPosition.left:
        return targetPosition.dx + targetSize.width + 16;
      case ArrowPosition.right:
        return targetPosition.dx - tooltipWidth - 16;
      case ArrowPosition.top:
      case ArrowPosition.bottom:
      default:
        // Center horizontally, but keep within screen bounds
        double left = targetPosition.dx + (targetSize.width / 2) - (tooltipWidth / 2);
        if (left < padding) left = padding;
        if (left + tooltipWidth > screenWidth - padding) {
          left = screenWidth - tooltipWidth - padding;
        }
        return left;
    }
  }

  double _calculateTooltipTop(
      Offset targetPosition, Size targetSize, BuildContext context) {
    final screenHeight = MediaQuery.of(context).size.height;
    const tooltipHeight = 120.0; // Approximate
    const padding = 16.0;

    double top;
    switch (widget.arrowPosition) {
      case ArrowPosition.top:
        top = targetPosition.dy + targetSize.height + 16;
        break;
      case ArrowPosition.bottom:
        top = targetPosition.dy - tooltipHeight - 16;
        // If tooltip would go above the screen, flip to below the target
        if (top < padding) {
          top = targetPosition.dy + targetSize.height + 16;
        }
        break;
      case ArrowPosition.left:
      case ArrowPosition.right:
        // Center vertically relative to target
        top = targetPosition.dy + (targetSize.height / 2) - (tooltipHeight / 2);
        break;
    }

    // Clamp within screen bounds
    if (top < padding) top = padding;
    if (top + tooltipHeight > screenHeight - padding) {
      top = screenHeight - tooltipHeight - padding;
    }
    return top;
  }
}

/// Overlay entry wrapper for showing onboarding tooltips
class OnboardingOverlay {
  static OverlayEntry? _currentOverlay;

  /// Show a tooltip over a target widget
  static void show(
    BuildContext context, {
    required String message,
    required GlobalKey targetKey,
    required VoidCallback onDismiss,
    ArrowPosition arrowPosition = ArrowPosition.bottom,
  }) {
    // Remove any existing overlay
    dismiss();

    _currentOverlay = OverlayEntry(
      builder: (context) => OnboardingTooltip(
        message: message,
        targetKey: targetKey,
        arrowPosition: arrowPosition,
        onDismiss: () {
          dismiss();
          onDismiss();
        },
      ),
    );

    Overlay.of(context).insert(_currentOverlay!);
  }

  /// Dismiss the current tooltip
  static void dismiss() {
    _currentOverlay?.remove();
    _currentOverlay = null;
  }

  /// Check if a tooltip is currently showing
  static bool get isShowing => _currentOverlay != null;
}

import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/parental_controls_service.dart';

/// Reusable PIN entry dialog with 4 auto-advancing digit fields,
/// shake animation on wrong PIN, and lockout countdown display.
class PinDialog extends StatefulWidget {
  /// Title displayed at the top of the dialog.
  final String title;

  /// Optional subtitle/description text.
  final String? subtitle;

  /// Called when a complete PIN is submitted. Return true if PIN is valid.
  final Future<bool> Function(String pin) onSubmit;

  /// Whether to show a "Cancel" button.
  final bool showCancel;

  const PinDialog({
    super.key,
    this.title = 'Enter PIN',
    this.subtitle,
    required this.onSubmit,
    this.showCancel = true,
  });

  /// Show the PIN dialog and return true if PIN was verified successfully.
  static Future<bool> show(
    BuildContext context, {
    String title = 'Enter PIN',
    String? subtitle,
    required Future<bool> Function(String pin) onSubmit,
    bool showCancel = true,
  }) async {
    final result = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => PinDialog(
        title: title,
        subtitle: subtitle,
        onSubmit: onSubmit,
        showCancel: showCancel,
      ),
    );
    return result ?? false;
  }

  @override
  State<PinDialog> createState() => _PinDialogState();
}

class _PinDialogState extends State<PinDialog>
    with SingleTickerProviderStateMixin {
  final List<TextEditingController> _controllers = List.generate(
    4,
    (_) => TextEditingController(),
  );
  final List<FocusNode> _focusNodes = List.generate(4, (_) => FocusNode());

  late AnimationController _shakeController;
  late Animation<double> _shakeAnimation;

  bool _isVerifying = false;
  String? _errorMessage;
  Timer? _lockoutTimer;
  int _lockoutSeconds = 0;

  // Track previous text to detect backspace
  final List<String> _previousText = ['', '', '', ''];

  @override
  void initState() {
    super.initState();
    _shakeController = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );
    _shakeAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _shakeController, curve: Curves.elasticIn),
    );

    // Focus first field after build
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        _focusNodes[0].requestFocus();
      }
    });

    // Check initial lockout state
    _checkLockout();
  }

  @override
  void dispose() {
    for (final c in _controllers) {
      c.dispose();
    }
    for (final f in _focusNodes) {
      f.dispose();
    }
    _shakeController.dispose();
    _lockoutTimer?.cancel();
    super.dispose();
  }

  void _checkLockout() {
    final service = ParentalControlsService.instance;
    if (service.isLockedOut) {
      _lockoutSeconds = service.lockoutRemaining;
      _startLockoutCountdown();
    }
  }

  void _startLockoutCountdown() {
    _lockoutTimer?.cancel();
    setState(() {
      _errorMessage = 'Too many attempts. Try again in $_lockoutSeconds seconds.';
    });
    _lockoutTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      setState(() {
        _lockoutSeconds--;
        if (_lockoutSeconds <= 0) {
          timer.cancel();
          _errorMessage = null;
          _lockoutSeconds = 0;
        } else {
          _errorMessage =
              'Too many attempts. Try again in $_lockoutSeconds seconds.';
        }
      });
    });
  }

  String get _currentPin => _controllers.map((c) => c.text).join();

  void _onChanged(int index, String value) {
    if (value.isEmpty) {
      // Backspace was pressed — move focus back
      if (_previousText[index].isNotEmpty && index > 0) {
        _focusNodes[index - 1].requestFocus();
      }
      _previousText[index] = '';
      return;
    }

    // Ensure only a single digit
    if (value.length > 1) {
      _controllers[index].text = value[value.length - 1];
      _controllers[index].selection = TextSelection.fromPosition(
        const TextPosition(offset: 1),
      );
    }

    final digit = _controllers[index].text;
    if (!RegExp(r'^\d$').hasMatch(digit)) {
      _controllers[index].clear();
      _previousText[index] = '';
      return;
    }

    _previousText[index] = digit;

    // Auto-advance to next field
    if (index < 3) {
      _focusNodes[index + 1].requestFocus();
    } else {
      // All 4 digits entered — submit
      _focusNodes[index].unfocus();
      _submitPin();
    }
  }

  Future<void> _submitPin() async {
    final pin = _currentPin;
    if (pin.length != 4) return;

    setState(() {
      _isVerifying = true;
      _errorMessage = null;
    });

    final success = await widget.onSubmit(pin);

    if (!mounted) return;

    if (success) {
      Navigator.of(context).pop(true);
    } else {
      // Check if now locked out
      final service = ParentalControlsService.instance;
      if (service.isLockedOut) {
        _lockoutSeconds = service.lockoutRemaining;
        _startLockoutCountdown();
      } else {
        setState(() {
          _errorMessage = 'Incorrect PIN. '
              '${ParentalControlsService.maxFailedAttempts - service.failedAttempts} '
              'attempts remaining.';
        });
      }

      // Shake animation
      _shakeController.forward(from: 0);

      // Clear fields
      for (int i = 0; i < 4; i++) {
        _controllers[i].clear();
        _previousText[i] = '';
      }

      // Refocus first field
      Future.delayed(const Duration(milliseconds: 100), () {
        if (mounted) {
          _focusNodes[0].requestFocus();
        }
      });

      setState(() {
        _isVerifying = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isLocked = _lockoutSeconds > 0;
    final theme = Theme.of(context);

    return AlertDialog(
      title: Text(widget.title, textAlign: TextAlign.center),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (widget.subtitle != null) ...[
            Text(
              widget.subtitle!,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 16),
          ],

          // PIN input fields with shake animation
          AnimatedBuilder(
            animation: _shakeAnimation,
            builder: (context, child) {
              final dx = sin(_shakeAnimation.value * pi * 4) * 10;
              return Transform.translate(
                offset: Offset(dx, 0),
                child: child,
              );
            },
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(4, (index) {
                final isLandscape = MediaQuery.of(context).orientation == Orientation.landscape;
                final pinFieldSize = isLandscape ? 40.0 : 50.0;
                final pinFieldHeight = isLandscape ? 48.0 : 60.0;
                final pinFieldMargin = isLandscape ? 4.0 : 6.0;
                return Container(
                  width: pinFieldSize,
                  height: pinFieldHeight,
                  margin: EdgeInsets.symmetric(horizontal: pinFieldMargin),
                  child: TextField(
                    controller: _controllers[index],
                    focusNode: _focusNodes[index],
                    enabled: !isLocked && !_isVerifying,
                    textAlign: TextAlign.center,
                    keyboardType: TextInputType.number,
                    maxLength: 1,
                    obscureText: true,
                    style: theme.textTheme.headlineMedium,
                    decoration: InputDecoration(
                      counterText: '',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      filled: true,
                      fillColor: isLocked
                          ? theme.colorScheme.surfaceVariant
                          : null,
                    ),
                    inputFormatters: [
                      FilteringTextInputFormatter.digitsOnly,
                      LengthLimitingTextInputFormatter(1),
                    ],
                    onChanged: (value) => _onChanged(index, value),
                  ),
                );
              }),
            ),
          ),

          // Error / lockout message
          if (_errorMessage != null) ...[
            const SizedBox(height: 16),
            Text(
              _errorMessage!,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.error,
              ),
            ),
          ],

          // Loading indicator
          if (_isVerifying) ...[
            const SizedBox(height: 16),
            const SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
          ],
        ],
      ),
      actions: [
        if (widget.showCancel)
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel'),
          ),
      ],
    );
  }
}

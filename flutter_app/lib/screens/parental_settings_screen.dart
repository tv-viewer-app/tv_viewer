import 'package:flutter/material.dart';
import '../services/parental_controls_service.dart';
import '../widgets/pin_dialog.dart';

/// Parental Controls settings screen.
///
/// Allows the user to:
/// - Enable/disable parental controls
/// - Set or change the 4-digit PIN
/// - Select blocked content categories
/// - Confirm age (over/under 18) for adult content access
class ParentalSettingsScreen extends StatefulWidget {
  const ParentalSettingsScreen({super.key});

  @override
  State<ParentalSettingsScreen> createState() => _ParentalSettingsScreenState();
}

class _ParentalSettingsScreenState extends State<ParentalSettingsScreen> {
  final ParentalControlsService _service = ParentalControlsService.instance;

  // Common TV content categories that can be blocked
  static const List<String> _availableCategories = [
    'Adult',
    'Entertainment',
    'Movies',
    'Music',
    'News',
    'Religious',
    'Sports',
    'Kids',
    'Documentary',
    'Lifestyle',
    'Comedy',
    'Drama',
    'Horror',
    'Animation',
    'Reality',
    'Science',
    'Gaming',
  ];

  late Set<String> _selectedCategories;

  @override
  void initState() {
    super.initState();
    _selectedCategories = _service.blockedCategories.toSet();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Parental Controls'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: ListenableBuilder(
        listenable: _service,
        builder: (context, _) {
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Status card
              _buildStatusCard(theme),
              const SizedBox(height: 16),

              // Enable/Disable toggle
              _buildEnableToggle(theme),
              const SizedBox(height: 16),

              // PIN management
              _buildPinSection(theme),
              const SizedBox(height: 16),

              // Category blocking (only when enabled)
              if (_service.enabled) ...[
                _buildCategorySection(theme),
                const SizedBox(height: 16),

                // Over-18 toggle
                _buildOver18Section(theme),
                const SizedBox(height: 24),

                // Reset button
                _buildResetButton(theme),
              ],
            ],
          );
        },
      ),
    );
  }

  Widget _buildStatusCard(ThemeData theme) {
    final isActive = _service.enabled && _service.hasPin;
    return Card(
      color: isActive
          ? theme.colorScheme.primaryContainer
          : theme.colorScheme.surfaceVariant,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(
              isActive ? Icons.lock : Icons.lock_open,
              size: 32,
              color: isActive
                  ? theme.colorScheme.primary
                  : theme.colorScheme.onSurfaceVariant,
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    isActive ? 'Parental Controls Active' : 'Parental Controls Off',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    isActive
                        ? '${_service.blockedCategories.length} categories blocked • '
                            'Over 18: ${_service.isOver18 ? "Yes" : "No"}'
                        : 'Set up a PIN to restrict content',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEnableToggle(ThemeData theme) {
    return Card(
      child: SwitchListTile(
        title: const Text('Enable Parental Controls'),
        subtitle: Text(
          _service.hasPin
              ? 'Require PIN to access blocked content'
              : 'Set up a PIN first to enable',
          style: theme.textTheme.bodySmall,
        ),
        value: _service.enabled,
        onChanged: _service.hasPin
            ? (value) async {
                if (!value) {
                  // Require PIN to disable
                  final verified = await PinDialog.show(
                    context,
                    title: 'Verify PIN',
                    subtitle: 'Enter your PIN to disable parental controls',
                    onSubmit: (pin) async => _service.verifyPin(pin),
                  );
                  if (verified) {
                    await _service.setEnabled(false);
                  }
                } else {
                  await _service.setEnabled(true);
                }
              }
            : null,
        secondary: Icon(
          _service.enabled ? Icons.shield : Icons.shield_outlined,
          color: _service.enabled ? theme.colorScheme.primary : null,
        ),
      ),
    );
  }

  Widget _buildPinSection(ThemeData theme) {
    return Card(
      child: Column(
        children: [
          ListTile(
            leading: const Icon(Icons.pin),
            title: Text(_service.hasPin ? 'Change PIN' : 'Set Up PIN'),
            subtitle: Text(
              _service.hasPin
                  ? 'Change your 4-digit parental controls PIN'
                  : 'Create a 4-digit PIN to protect settings',
              style: theme.textTheme.bodySmall,
            ),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _service.hasPin ? _showChangePinFlow() : _showSetupPinFlow(),
          ),
        ],
      ),
    );
  }

  Widget _buildCategorySection(ThemeData theme) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.category, color: theme.colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  'Blocked Categories',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Channels in these categories will be hidden',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 4,
              children: _availableCategories.map((category) {
                final isSelected = _selectedCategories.contains(category);
                return FilterChip(
                  label: Text(category),
                  selected: isSelected,
                  onSelected: (selected) {
                    setState(() {
                      if (selected) {
                        _selectedCategories.add(category);
                      } else {
                        _selectedCategories.remove(category);
                      }
                    });
                    _service.setBlockedCategories(
                      _selectedCategories.toList(),
                    );
                  },
                  selectedColor: theme.colorScheme.primaryContainer,
                  checkmarkColor: theme.colorScheme.primary,
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOver18Section(ThemeData theme) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.eighteen_up_rating, color: theme.colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  'Age Verification',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Confirm your age to access adult content settings',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 12),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('I confirm I am 18 or older'),
              subtitle: _service.isOver18
                  ? Text(
                      'This enables access to adult content settings',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.error,
                      ),
                    )
                  : null,
              value: _service.isOver18,
              onChanged: (value) async {
                await _service.setOver18(value);
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResetButton(ThemeData theme) {
    return OutlinedButton.icon(
      onPressed: _showResetConfirmation,
      icon: const Icon(Icons.restore),
      label: const Text('Reset Parental Controls'),
      style: OutlinedButton.styleFrom(
        foregroundColor: theme.colorScheme.error,
        side: BorderSide(color: theme.colorScheme.error),
        minimumSize: const Size(double.infinity, 48),
      ),
    );
  }

  // ------------------------------------------------------------------
  // PIN flows
  // ------------------------------------------------------------------

  Future<void> _showSetupPinFlow() async {
    String? firstPin;

    // Step 1: Enter new PIN
    final entered = await PinDialog.show(
      context,
      title: 'Create PIN',
      subtitle: 'Enter a 4-digit PIN for parental controls',
      onSubmit: (pin) async {
        if (!ParentalControlsService.validatePinFormat(pin)) {
          return false;
        }
        firstPin = pin;
        return true;
      },
    );
    if (!entered || firstPin == null || !mounted) return;

    // Step 2: Confirm PIN
    final confirmed = await PinDialog.show(
      context,
      title: 'Confirm PIN',
      subtitle: 'Re-enter your PIN to confirm',
      onSubmit: (pin) async {
        return pin == firstPin;
      },
    );
    if (!confirmed || !mounted) return;

    // Set up the PIN
    await _service.setupPin(firstPin!);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Parental controls PIN set successfully'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  Future<void> _showChangePinFlow() async {
    // Step 1: Verify current PIN
    final verified = await PinDialog.show(
      context,
      title: 'Current PIN',
      subtitle: 'Enter your current PIN',
      onSubmit: (pin) async => _service.verifyPin(pin),
    );
    if (!verified || !mounted) return;

    // Step 2: Enter new PIN
    String? newPin;
    final entered = await PinDialog.show(
      context,
      title: 'New PIN',
      subtitle: 'Enter your new 4-digit PIN',
      onSubmit: (pin) async {
        if (!ParentalControlsService.validatePinFormat(pin)) {
          return false;
        }
        newPin = pin;
        return true;
      },
    );
    if (!entered || newPin == null || !mounted) return;

    // Step 3: Confirm new PIN
    final confirmed = await PinDialog.show(
      context,
      title: 'Confirm New PIN',
      subtitle: 'Re-enter your new PIN to confirm',
      onSubmit: (pin) async {
        return pin == newPin;
      },
    );
    if (!confirmed || !mounted) return;

    // Change the PIN (we already verified old PIN, just set new one directly)
    await _service.setupPin(newPin!);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('PIN changed successfully'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  Future<void> _showResetConfirmation() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Reset Parental Controls?'),
        content: const Text(
          'This will remove your PIN and all blocking settings. '
          'You will need to set up parental controls again.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(
              foregroundColor: Theme.of(context).colorScheme.error,
            ),
            child: const Text('Reset'),
          ),
        ],
      ),
    );

    if (confirm != true || !mounted) return;

    // Require PIN verification to reset
    final verified = await PinDialog.show(
      context,
      title: 'Verify PIN',
      subtitle: 'Enter your PIN to confirm reset',
      onSubmit: (pin) async => _service.verifyPin(pin),
    );

    if (!verified || !mounted) return;

    // We already verified the PIN above, so directly clear settings
    await _service.setBlockedCategories([]);
    await _service.setOver18(false);
    await _service.setEnabled(false);

    setState(() {
      _selectedCategories = {};
    });

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Parental controls have been reset'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }
}

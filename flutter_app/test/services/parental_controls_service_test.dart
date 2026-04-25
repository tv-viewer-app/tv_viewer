import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tv_viewer/services/parental_controls_service.dart';

/// Unit tests for ParentalControlsService
/// Ported from Python: utils/parental.py test scenarios
void main() {
  late ParentalControlsService service;

  setUp(() {
    // Mock SharedPreferences for each test
    SharedPreferences.setMockInitialValues({});
    service = ParentalControlsService.forTesting();
  });

  group('ParentalControlsService - PIN Management', () {
    test('hasPin returns false initially', () {
      expect(service.hasPin, isFalse);
    });

    test('setupPin stores hashed PIN and enables controls', () async {
      await service.setupPin('1234');

      expect(service.hasPin, isTrue);
      expect(service.enabled, isTrue);
    });

    test('setupPin rejects non-4-digit PINs', () async {
      expect(
        () => service.setupPin('123'),
        throwsA(isA<ArgumentError>()),
      );
      expect(
        () => service.setupPin('12345'),
        throwsA(isA<ArgumentError>()),
      );
      expect(
        () => service.setupPin('abcd'),
        throwsA(isA<ArgumentError>()),
      );
      expect(
        () => service.setupPin(''),
        throwsA(isA<ArgumentError>()),
      );
    });

    test('verifyPin returns true for correct PIN', () async {
      await service.setupPin('5678');

      expect(service.verifyPin('5678'), isTrue);
    });

    test('verifyPin returns false for incorrect PIN', () async {
      await service.setupPin('5678');

      expect(service.verifyPin('0000'), isFalse);
      expect(service.verifyPin('1234'), isFalse);
    });

    test('verifyPin returns false when no PIN is set', () {
      expect(service.verifyPin('1234'), isFalse);
    });

    test('changePin works with correct old PIN', () async {
      await service.setupPin('1111');

      final result = await service.changePin('1111', '2222');

      expect(result, isTrue);
      expect(service.verifyPin('2222'), isTrue);
      expect(service.verifyPin('1111'), isFalse);
    });

    test('changePin fails with incorrect old PIN', () async {
      await service.setupPin('1111');

      final result = await service.changePin('9999', '2222');

      expect(result, isFalse);
      // Original PIN should still work
      expect(service.verifyPin('1111'), isTrue);
    });

    test('changePin rejects invalid new PIN format', () async {
      await service.setupPin('1111');

      expect(
        () => service.changePin('1111', 'abc'),
        throwsA(isA<ArgumentError>()),
      );
    });
  });

  group('ParentalControlsService - Lockout', () {
    test('lockout after max failed attempts', () async {
      await service.setupPin('1234');

      // Fail 3 times
      service.verifyPin('0000');
      service.verifyPin('0000');
      service.verifyPin('0000');

      expect(service.isLockedOut, isTrue);
      expect(service.lockoutRemaining, greaterThan(0));
    });

    test('correct PIN rejected during lockout', () async {
      await service.setupPin('1234');

      // Trigger lockout
      service.verifyPin('0000');
      service.verifyPin('0000');
      service.verifyPin('0000');

      // Even correct PIN fails during lockout
      expect(service.verifyPin('1234'), isFalse);
    });

    test('failed attempts reset on successful verification', () async {
      await service.setupPin('1234');

      // Fail twice (below threshold)
      service.verifyPin('0000');
      service.verifyPin('0000');
      expect(service.failedAttempts, equals(2));

      // Succeed
      service.verifyPin('1234');
      expect(service.failedAttempts, equals(0));
      expect(service.isLockedOut, isFalse);
    });

    test('lockoutRemaining returns 0 when not locked out', () async {
      await service.setupPin('1234');
      expect(service.lockoutRemaining, equals(0));
    });
  });

  group('ParentalControlsService - Channel Filtering', () {
    test('isChannelBlocked returns false when disabled', () async {
      // Not enabled
      expect(service.enabled, isFalse);
      expect(
        service.isChannelBlocked(category: 'Adult'),
        isFalse,
      );
    });

    test('isChannelBlocked checks category (case-insensitive)', () async {
      await service.setupPin('1234');
      await service.setBlockedCategories(['Adult', 'Horror']);

      expect(
        service.isChannelBlocked(category: 'Adult'),
        isTrue,
      );
      expect(
        service.isChannelBlocked(category: 'adult'),
        isTrue,
      );
      expect(
        service.isChannelBlocked(category: 'HORROR'),
        isTrue,
      );
      expect(
        service.isChannelBlocked(category: 'News'),
        isFalse,
      );
    });

    test('isChannelBlocked checks age rating', () async {
      await service.setupPin('1234');
      await service.setMinAge(12);

      expect(
        service.isChannelBlocked(minimumAge: 16),
        isTrue,
      );
      expect(
        service.isChannelBlocked(minimumAge: 12),
        isFalse,
      );
      expect(
        service.isChannelBlocked(minimumAge: 8),
        isFalse,
      );
    });

    test('isChannelBlocked with age 0 means no restriction', () async {
      await service.setupPin('1234');
      await service.setMinAge(0);

      expect(
        service.isChannelBlocked(minimumAge: 18),
        isFalse,
      );
    });

    test('isChannelBlocked with null category', () async {
      await service.setupPin('1234');
      await service.setBlockedCategories(['Adult']);

      expect(
        service.isChannelBlocked(category: null),
        isFalse,
      );
    });

    test('isChannelBlocked with empty category', () async {
      await service.setupPin('1234');
      await service.setBlockedCategories(['Adult']);

      expect(
        service.isChannelBlocked(category: ''),
        isFalse,
      );
    });
  });

  group('ParentalControlsService - Settings', () {
    test('setBlockedCategories persists correctly', () async {
      await service.setupPin('1234');
      await service.setBlockedCategories(['News', 'Sports', 'Adult']);

      expect(service.blockedCategories, containsAll(['News', 'Sports', 'Adult']));
      expect(service.blockedCategories.length, equals(3));
    });

    test('setMinAge clamps to 0-18 range', () async {
      await service.setupPin('1234');

      await service.setMinAge(-5);
      expect(service.minAge, equals(0));

      await service.setMinAge(25);
      expect(service.minAge, equals(18));

      await service.setMinAge(12);
      expect(service.minAge, equals(12));
    });

    test('setEnabled requires PIN to be set', () async {
      expect(
        () => service.setEnabled(true),
        throwsA(isA<StateError>()),
      );
    });

    test('setEnabled works after PIN is set', () async {
      await service.setupPin('1234');

      await service.setEnabled(false);
      expect(service.enabled, isFalse);

      await service.setEnabled(true);
      expect(service.enabled, isTrue);
    });
  });

  group('ParentalControlsService - Persistence', () {
    test('settings survive re-initialization', () async {
      // Set up initial state
      SharedPreferences.setMockInitialValues({});
      final service1 = ParentalControlsService.forTesting();
      await service1.initialize();
      await service1.setupPin('4321');
      await service1.setBlockedCategories(['Adult', 'Horror']);
      await service1.setMinAge(16);

      // Create new instance and load (simulates app restart)
      final service2 = ParentalControlsService.forTesting();
      await service2.initialize();

      expect(service2.enabled, isTrue);
      expect(service2.hasPin, isTrue);
      expect(service2.verifyPin('4321'), isTrue);
      expect(service2.blockedCategories, containsAll(['Adult', 'Horror']));
      expect(service2.minAge, equals(16));
    });
  });

  group('ParentalControlsService - Reset', () {
    test('reset clears all settings with valid PIN', () async {
      await service.setupPin('1234');
      await service.setBlockedCategories(['Adult']);
      await service.setMinAge(12);

      final result = await service.reset('1234');

      expect(result, isTrue);
      expect(service.enabled, isFalse);
      expect(service.hasPin, isFalse);
      expect(service.blockedCategories, isEmpty);
      expect(service.minAge, equals(0));
    });

    test('reset fails with incorrect PIN', () async {
      await service.setupPin('1234');
      await service.setBlockedCategories(['Adult']);

      final result = await service.reset('0000');

      expect(result, isFalse);
      // Settings should remain unchanged
      expect(service.enabled, isTrue);
      expect(service.hasPin, isTrue);
      expect(service.blockedCategories, contains('Adult'));
    });
  });

  group('ParentalControlsService - PIN Format Validation', () {
    test('validatePinFormat accepts valid PINs', () {
      expect(ParentalControlsService.validatePinFormat('0000'), isTrue);
      expect(ParentalControlsService.validatePinFormat('1234'), isTrue);
      expect(ParentalControlsService.validatePinFormat('9999'), isTrue);
    });

    test('validatePinFormat rejects invalid PINs', () {
      expect(ParentalControlsService.validatePinFormat(''), isFalse);
      expect(ParentalControlsService.validatePinFormat('123'), isFalse);
      expect(ParentalControlsService.validatePinFormat('12345'), isFalse);
      expect(ParentalControlsService.validatePinFormat('abcd'), isFalse);
      expect(ParentalControlsService.validatePinFormat('12ab'), isFalse);
      expect(ParentalControlsService.validatePinFormat('12 4'), isFalse);
    });
  });
}

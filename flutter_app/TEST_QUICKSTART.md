# Quick Start - Testing Setup

## ⚡ Quick Setup (5 minutes)

### 1. Install Test Dependencies
```bash
cd "D:\Visual Studio 2017\tv_viewer_project\flutter_app"
flutter pub add --dev mockito build_runner
flutter pub add --dev integration_test
flutter pub get
```

### 2. Generate Mock Files
```bash
flutter pub run build_runner build
```

### 3. Run Your First Test
```bash
# Run unit tests
flutter test test/models/channel_test.dart

# Run all tests
flutter test

# Run with coverage
flutter test --coverage
```

### 4. Run Integration Tests
```bash
# Start an Android emulator first, then:
flutter test integration_test/app_test.dart
```

---

## 📊 Test Execution Priority

### Phase 1: Smoke Tests (15 minutes)
**Critical functionality only - must pass before any release**

```bash
# Run these specific tests:
flutter test --name "Display all channels"
flutter test --name "Filter TV channels"
flutter test --name "Search by channel name"
flutter test --name "Parse valid M3U"
```

**Manual Tests:**
- FC-1.1: Launch app and verify channels load
- FC-1.5: Tap a channel and verify video plays
- FC-7.9: Press back button and return to list
- FC-11.1: Start validation scan

**Expected time:** 15 minutes  
**Pass criteria:** All tests pass, app doesn't crash

---

### Phase 2: Functional Tests (1-2 hours)
**All feature functionality**

```bash
# Run all unit tests
flutter test

# Run specific feature tests
flutter test test/providers/channel_provider_test.dart  # Filtering
flutter test test/services/m3u_service_test.dart        # M3U parsing
```

**Manual Tests from CSV:**
- All FC-* test cases (Functional)
- Focus on: Filters, Search, Playback, Validation

**Expected time:** 1-2 hours  
**Pass criteria:** 95%+ tests pass

---

### Phase 3: Comprehensive Tests (4-8 hours)
**Everything including edge cases and performance**

```bash
# Run all tests with coverage
flutter test --coverage

# Run integration tests
flutter test integration_test/app_test.dart

# Generate coverage report
genhtml coverage/lcov.info -o coverage/html
open coverage/html/index.html
```

**Manual Tests from CSV:**
- All test cases (FC, EC, ES, UX, PT, SEC, REG)
- Test on multiple devices/screen sizes
- Test different network conditions
- Performance benchmarks

**Expected time:** 4-8 hours  
**Pass criteria:** 
- 80%+ code coverage
- All critical tests pass
- No high-severity bugs

---

## 🎯 Critical Test Cases (Must Pass)

### Channel Loading
- [ ] FC-1.1: Channels display on launch
- [ ] FC-12.2: Cached channels load instantly
- [ ] ES-1.1: Handle no internet gracefully

### Filtering
- [ ] FC-2.2: TV filter works
- [ ] FC-3.3: Category filter works
- [ ] FC-4.3: Country filter works
- [ ] FC-6.5: Combined filters + search works

### Video Playback
- [ ] FC-7.1: Video plays when channel tapped
- [ ] FC-7.9: Back button returns to list
- [ ] ES-2.1: Handle stream errors gracefully

### Validation Scanning
- [ ] FC-11.1: Scan starts when refresh tapped
- [ ] FC-11.2: Progress displays during scan
- [ ] FC-11.7: Stop button stops scan
- [ ] FC-11.10: Results persist after restart

---

## 🐛 Bug Severity Guide

When logging bugs in TEST_CASES.csv:

### Critical (P0) - Fix immediately
- App crashes
- Cannot load channels
- Cannot play any videos
- Data loss/corruption

### High (P1) - Fix before release
- Major features broken (filter, search)
- Frequent crashes in specific scenarios
- Poor performance (>5s load time)
- UI completely broken

### Medium (P2) - Fix if time permits
- Minor feature issues
- UI glitches
- Moderate performance issues
- Workarounds available

### Low (P3) - Track for future
- Cosmetic issues
- Edge cases
- Enhancement requests

---

## 📱 Device Testing Matrix

Test on at least these configurations:

| Device | Android | Screen | Priority |
|--------|---------|--------|----------|
| Pixel 5 | 12 | 6.0" FHD+ | High |
| Galaxy S21 | 11 | 6.2" QHD+ | High |
| Pixel 4a | 11 | 5.8" FHD+ | Medium |
| Older device | 8 | 5.5" HD | Medium |
| Tablet | 11+ | 10" | Low |

### Network Conditions
- [ ] WiFi (fast)
- [ ] 4G (medium)
- [ ] 3G (slow)
- [ ] Offline (cached data)

---

## ✅ Test Checklist Before Release

### Code Quality
- [ ] `flutter analyze` passes with no errors
- [ ] All unit tests pass (`flutter test`)
- [ ] Code coverage ≥80%
- [ ] No compiler warnings

### Functional Testing
- [ ] All High priority tests pass
- [ ] 95%+ Medium priority tests pass
- [ ] Critical user flows work end-to-end
- [ ] External player integration works

### Performance Testing
- [ ] App launches in <2 seconds (cached)
- [ ] Filters update in <100ms
- [ ] Search responds in <200ms per keystroke
- [ ] Scrolling is smooth (60fps)
- [ ] No memory leaks during extended use

### Device Testing
- [ ] Tested on Android 5.0 (minimum)
- [ ] Tested on Android 12+ (latest)
- [ ] Tested on small screen (5")
- [ ] Tested on large screen (6.7"+)
- [ ] Tested on tablet (10")

### Network Testing
- [ ] Works on WiFi
- [ ] Works on 4G
- [ ] Handles slow network (3G)
- [ ] Handles offline mode
- [ ] Recovers from network drops

### Error Handling
- [ ] Handles empty channel list
- [ ] Handles invalid M3U data
- [ ] Handles stream playback errors
- [ ] Handles full device storage
- [ ] Shows clear error messages

### Accessibility
- [ ] Screen reader support (TalkBack)
- [ ] All buttons have labels
- [ ] Minimum 48x48dp touch targets
- [ ] Text scales with system font
- [ ] WCAG AA color contrast

### Regression Testing
- [ ] All previously fixed bugs still fixed
- [ ] No new crashes introduced
- [ ] Performance not degraded
- [ ] All features still work

---

## 🚀 Continuous Integration

### Pre-Commit Checks
```bash
# Run before every commit
flutter analyze
flutter test
```

### Pull Request Checks
```bash
# Run before merging PR
flutter test --coverage
flutter test integration_test/app_test.dart
```

### Release Checklist
```bash
# Full test suite
flutter analyze
flutter test --coverage
flutter test integration_test/app_test.dart
# Manual testing of critical flows
# Device testing on multiple configurations
# Performance benchmarking
```

---

## 📞 Getting Help

### Test Failures
1. Read the error message carefully
2. Check if it's a flaky test (network-dependent)
3. Run the test in isolation: `flutter test --name "test name"`
4. Check test assumptions and mock data
5. Ask QA team if unsure

### Coverage Issues
1. Generate coverage report: `flutter test --coverage`
2. Identify uncovered lines
3. Add tests for uncovered code
4. Focus on critical paths first

### Integration Test Issues
1. Ensure emulator/device is running
2. Check app builds successfully
3. Look for timing issues (add more `pumpAndSettle`)
4. Check for widget key mismatches

---

## 📈 Success Metrics

### Test Coverage
- **Current:** Check with `flutter test --coverage`
- **Target:** 80%+
- **Critical Paths:** 100%

### Test Execution Time
- **Unit Tests:** <30 seconds
- **Integration Tests:** <5 minutes
- **Full Manual Suite:** <4 hours

### Bug Escape Rate
- **Target:** <5% of bugs found in production
- **Track:** Bugs found in testing vs. production

### Automation Rate
- **Target:** 70%+ of tests automated
- **Current:** Check test/ directory coverage

---

## 🎓 Learning Resources

### Flutter Testing
- [Official Testing Guide](https://flutter.dev/docs/testing)
- [Widget Test Introduction](https://flutter.dev/docs/cookbook/testing/widget/introduction)
- [Integration Testing](https://flutter.dev/docs/testing/integration-tests)

### Best Practices
- [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
- [Testing Best Practices](https://flutter.dev/docs/testing/best-practices)

### Tools
- [Mockito Documentation](https://pub.dev/packages/mockito)
- [Provider Testing](https://pub.dev/packages/provider#testing)

---

**Last Updated:** 2024  
**Version:** 1.0  
**Maintained by:** QA Team

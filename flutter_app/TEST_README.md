# TV Viewer Flutter App - Test Documentation

## Running Tests

### Prerequisites
1. Ensure Flutter SDK 3.0.0+ is installed
2. Install dependencies:
   ```bash
   flutter pub get
   ```

### Unit Tests

Run all unit tests:
```bash
flutter test
```

Run specific test file:
```bash
flutter test test/models/channel_test.dart
flutter test test/services/m3u_service_test.dart
flutter test test/providers/channel_provider_test.dart
```

Run with coverage:
```bash
flutter test --coverage
```

View coverage report:
```bash
# Install lcov first (Linux/Mac)
# sudo apt-get install lcov
# brew install lcov

genhtml coverage/lcov.info -o coverage/html
open coverage/html/index.html
```

### Integration Tests

Run integration tests on Android emulator:
```bash
flutter test integration_test/app_test.dart
```

Run on connected device:
```bash
flutter test integration_test/app_test.dart -d <device-id>
```

Run specific integration test:
```bash
flutter test integration_test/app_test.dart --name "Complete First-Time Flow"
```

### Widget Tests

Run widget tests:
```bash
flutter test test/widgets/
```

## Test Structure

```
flutter_app/
├── test/                           # Unit & Widget Tests
│   ├── models/
│   │   └── channel_test.dart      # Channel model tests
│   ├── services/
│   │   └── m3u_service_test.dart  # M3U service tests
│   ├── providers/
│   │   └── channel_provider_test.dart  # Provider tests
│   └── widgets/
│       └── (widget tests here)
├── integration_test/               # Integration Tests
│   └── app_test.dart              # End-to-end flow tests
├── TEST_PLAN.md                    # Comprehensive test plan
└── TEST_CASES.csv                  # Test case tracking spreadsheet
```

## Test Coverage Goals

- **Unit Tests:** 80%+ code coverage
- **Widget Tests:** All custom widgets
- **Integration Tests:** Critical user flows
- **Manual Tests:** Use TEST_CASES.csv for tracking

## Test Categories

### 1. Unit Tests (test/)
- **Models:** Channel parsing, normalization, serialization
- **Services:** M3U fetching, parsing, validation
- **Providers:** State management, filtering logic

### 2. Widget Tests (test/widgets/)
- Channel list item rendering
- Filter dropdown behavior
- Search bar functionality
- Loading states
- Empty states

### 3. Integration Tests (integration_test/)
- Complete user flows
- Filter + Search + Play combinations
- Validation scanning flows
- Performance benchmarks
- Error handling scenarios

### 4. Manual Tests (TEST_CASES.csv)
- Use spreadsheet to track manual test execution
- Mark status: Not Tested, Passed, Failed
- Record actual results and bug IDs
- Export to Excel for test reports

## Test Data

### Sample M3U for Testing
Create `test_data/sample.m3u`:
```m3u
#EXTM3U
#EXTINF:-1 tvg-logo="http://example.com/cnn.png" tvg-country="US" group-title="News",CNN International (720p)
http://stream.example.com/cnn.m3u8
#EXTINF:-1 tvg-logo="http://example.com/bbc.png" tvg-country="UK" group-title="News",BBC World News (1080p)
http://stream.example.com/bbc.m3u8
#EXTINF:-1 tvg-logo="http://example.com/espn.png" tvg-country="US" group-title="Sports",ESPN
http://stream.example.com/espn.m3u8
```

### Mock Data in Tests
Tests use mock data to avoid network dependencies:
- Mock channel lists
- Mock M3U content
- Mock HTTP responses (using mockito)

## CI/CD Integration

### GitHub Actions Example
Create `.github/workflows/test.yml`:
```yaml
name: Flutter Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - uses: subosito/flutter-action@v2
      with:
        flutter-version: '3.0.0'
        
    - name: Install dependencies
      run: flutter pub get
      
    - name: Analyze code
      run: flutter analyze
      
    - name: Run unit tests
      run: flutter test --coverage
      
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: coverage/lcov.info
        
    - name: Check test coverage
      run: |
        COVERAGE=$(lcov --summary coverage/lcov.info | grep lines | awk '{print $2}' | cut -d'%' -f1)
        echo "Coverage: $COVERAGE%"
        if (( $(echo "$COVERAGE < 80" | bc -l) )); then
          echo "Coverage below 80% threshold"
          exit 1
        fi
```

## Debugging Tests

### Run tests in verbose mode:
```bash
flutter test --verbose
```

### Run specific test:
```bash
flutter test --name "Parse valid M3U line"
```

### Debug test in VS Code:
1. Set breakpoint in test file
2. Click "Debug" above test method
3. Use debugger controls to step through

## Performance Testing

### Benchmark Tests
```bash
flutter test --profile test/models/channel_test.dart
```

### Memory Profiling
```bash
flutter run --profile
# Use DevTools to analyze memory usage
```

## Known Issues & Limitations

### Unit Tests
- Network tests require mocking (mockito)
- Video player tests may need platform-specific setup
- Some tests require SharedPreferences mocking

### Integration Tests
- Require emulator/device to run
- Network-dependent tests may be flaky
- Video playback tests need actual stream URLs

### Manual Tests
- External player tests require VLC/MX Player installed
- Cast functionality requires Chromecast device
- Network condition tests need manual setup

## Test Maintenance

### Adding New Tests
1. Create test file in appropriate directory
2. Follow naming convention: `<feature>_test.dart`
3. Group related tests with `group()`
4. Use descriptive test names with test ID references
5. Update TEST_PLAN.md and TEST_CASES.csv

### Updating Tests
- Keep tests synchronized with code changes
- Update test data when models change
- Maintain test coverage above 80%
- Run full test suite before commits

## Test Reporting

### Generate Test Report
```bash
# Run tests with JSON output
flutter test --machine > test-results.json

# Generate HTML report (requires custom tool)
# npm install -g flutter-test-report
# flutter-test-report -i test-results.json -o test-report.html
```

### Manual Test Tracking
1. Open TEST_CASES.csv in Excel/Google Sheets
2. For each test execution:
   - Update Status column
   - Record Actual Result
   - Add Bug ID if failed
   - Record Tester name and Date
3. Generate test summary report

## Test Best Practices

1. **Isolation:** Tests should not depend on each other
2. **Repeatability:** Tests should produce same results every run
3. **Fast:** Unit tests should complete in seconds
4. **Readable:** Test names should describe what they test
5. **Maintainable:** Avoid hardcoded values, use constants
6. **Coverage:** Aim for 80%+ code coverage
7. **Mocking:** Mock external dependencies (network, storage)
8. **Assertions:** Use descriptive expect messages

## Contact

For test-related questions:
- **QA Lead:** [Contact Info]
- **Development Lead:** [Contact Info]

## Resources

- [Flutter Testing Documentation](https://flutter.dev/docs/testing)
- [Mockito Package](https://pub.dev/packages/mockito)
- [Integration Test Package](https://pub.dev/packages/integration_test)
- [TEST_PLAN.md](TEST_PLAN.md) - Complete test plan
- [TEST_CASES.csv](TEST_CASES.csv) - Test case tracking

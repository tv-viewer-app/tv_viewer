# Logger Integration Testing Checklist

## Pre-Testing Setup
- [x] Verify `share_plus: ^9.0.0` is in pubspec.yaml
- [x] Verify `path_provider` and `intl` dependencies exist
- [ ] Run `flutter pub get` (if needed)
- [ ] Run `flutter clean` and rebuild (recommended)

## Test 1: App Initialization Logging
**Objective**: Verify logger initializes and logs app start

**Steps**:
1. Launch the app
2. Check device logs (via `flutter run` or Android Studio logcat)

**Expected Results**:
- See log: `[INFO] Logger service initialized`
- See log: `[INFO] TV Viewer app starting...`
- No initialization errors

**Status**: [ ] Pass [ ] Fail

---

## Test 2: Channel Loading Logging
**Objective**: Verify channel operations are logged

**Steps**:
1. Launch app (first time with no cache)
2. Wait for channels to load
3. Check logs

**Expected Results**:
- See log: `[INFO] Loading channels...`
- See log: `[INFO] No cached channels found, fetching fresh data`
- See log: `[INFO] Fetching channels from repositories...`
- See log: `[INFO] Successfully fetched X channels`

**Subsequent Launch**:
- See log: `[INFO] Loaded X channels from cache`
- See log: `[DEBUG] Starting background channel fetch...`

**Status**: [ ] Pass [ ] Fail

---

## Test 3: Channel Validation Logging
**Objective**: Verify scan/validation is logged

**Steps**:
1. Launch app
2. Tap the scan/validate button
3. Wait for validation to complete
4. Check logs

**Expected Results**:
- See log: `[INFO] Starting channel validation for X channels`
- See log: `[DEBUG] Saved X channels to cache` (during scan)
- See log: `[INFO] Channel validation completed: X working, Y failed`

**Status**: [ ] Pass [ ] Fail

---

## Test 4: Error Logging (Network Error)
**Objective**: Verify errors are properly logged with stack traces

**Steps**:
1. Turn off device network/WiFi
2. Clear app cache (or reinstall)
3. Launch app
4. Wait for fetch to fail
5. Check logs

**Expected Results**:
- See log: `[ERROR] Error fetching channels`
- Error log includes exception details
- Error log includes stack trace
- App doesn't crash (graceful error handling)

**Status**: [ ] Pass [ ] Fail

---

## Test 5: Log Export Functionality
**Objective**: Verify users can export and share logs

**Steps**:
1. Use app for a few minutes (load channels, scan, etc.)
2. Navigate to Help & Support screen
3. Tap "Export Logs"
4. Wait for share dialog

**Expected Results**:
- Loading indicator appears
- Share dialog appears with log file
- File name format: `tv_viewer_logs_export_YYYYMMDD_HHMMSS.txt`
- Success SnackBar: "Logs exported successfully"
- Log shows: `[INFO] User requested log export`
- Log shows: `[INFO] Logs exported and shared successfully`

**Status**: [ ] Pass [ ] Fail

---

## Test 6: Log Export (Empty Case)
**Objective**: Verify behavior when no logs exist

**Steps**:
1. Fresh install (clear all data)
2. Navigate to Help & Support immediately
3. Tap "Export Logs"

**Expected Results**:
- Orange SnackBar: "No logs available to export"
- Log shows: `[WARNING] No logs available to export`
- No crash or error

**Status**: [ ] Pass [ ] Fail

---

## Test 7: Log File Content Verification
**Objective**: Verify log files are properly formatted

**Steps**:
1. Generate some logs (use app normally)
2. Export logs and save to device
3. Open log file in text editor

**Expected Results**:
- File starts with header (export date, app name)
- Each log file section is labeled
- Entries format: `[YYYY-MM-DD HH:MM:SS.mmm] [LEVEL] message`
- All logged events are present
- Stack traces are complete (if errors occurred)

**Status**: [ ] Pass [ ] Fail

---

## Test 8: Uncaught Error Logging
**Objective**: Verify global error zone catches errors

**Steps**:
1. Temporarily add code to trigger an error:
   ```dart
   // In any provider or screen
   Future.delayed(Duration(seconds: 2), () {
     throw Exception('Test uncaught error');
   });
   ```
2. Launch app
3. Wait for error to trigger
4. Check logs

**Expected Results**:
- See log: `[ERROR] Uncaught async error`
- Error includes exception message
- Error includes stack trace
- App doesn't crash completely

**Status**: [ ] Pass [ ] Fail

---

## Test 9: Log Rotation
**Objective**: Verify logs rotate when file size limit is reached

**Steps**:
1. Generate lots of logs (run validation multiple times)
2. Check logs directory on device
3. Verify rotation

**Expected Results**:
- Maximum of 5 log files exist
- Each file is ~1MB or less
- Oldest files are deleted when limit is reached
- New logs continue in new file

**Note**: This test requires extensive logging to trigger rotation

**Status**: [ ] Pass [ ] Fail

---

## Test 10: Cache Error Handling
**Objective**: Verify cache errors are logged but don't crash app

**Steps**:
1. Simulate cache error (corrupt cache data)
2. Launch app
3. Check logs

**Expected Results**:
- See log: `[ERROR] Error loading cache` (if load fails)
- See log: `[ERROR] Error saving cache` (if save fails)
- App continues to function (fetches fresh data)
- Full stack trace in logs

**Status**: [ ] Pass [ ] Fail

---

## Log Levels Reference

When reviewing logs, verify appropriate levels are used:

- **DEBUG**: Background operations, detailed state information
- **INFO**: Normal operations, key events (start, load, complete)
- **WARNING**: Issues that don't prevent operation
- **ERROR**: Failures, exceptions with stack traces

---

## Post-Testing Verification

After all tests:
- [ ] No unnecessary debug prints in release build
- [ ] Log files are created in correct location
- [ ] Old logs are properly rotated
- [ ] App performance is not impacted by logging
- [ ] Memory usage is reasonable (logs are flushed, not held in memory)
- [ ] Logs contain enough detail for debugging issues
- [ ] No sensitive information in logs (passwords, API keys, etc.)

---

## Performance Notes

- Logger uses buffering (5-second flush interval)
- Errors are flushed immediately
- Background logging doesn't block UI
- Log rotation is automatic
- Consider adjusting log level for production (info or warning)

---

## Troubleshooting

**If logs aren't appearing**:
1. Check logger initialization in main()
2. Verify LogLevel isn't too high (debug logs won't show if minLogLevel is info)
3. Check device logs with `adb logcat -s flutter`

**If export fails**:
1. Verify share_plus dependency is installed
2. Check device storage permissions
3. Verify logs directory exists and is accessible

**If app crashes on error**:
1. Verify runZonedGuarded is properly set up
2. Check FlutterError.onError handler
3. Ensure all catch blocks have stack trace parameter

---

## Sign-off

Tester: _____________________
Date: _____________________
Version: 1.5.0+1

All tests passed: [ ] Yes [ ] No
Notes: _____________________

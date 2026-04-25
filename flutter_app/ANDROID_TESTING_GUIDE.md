# Android Features - Testing Guide

## 🧪 Comprehensive Test Plan

This document provides detailed test cases for the newly implemented Android features.

---

## 📋 Test Environment Setup

### Prerequisites
- Android device or emulator with Android 8.0+ (API 26+)
- Flutter SDK installed
- TV Viewer app installed (debug or release build)
- Test video stream URLs ready
- Screen timeout set to 30 seconds (for wake lock testing)

### Test Devices Recommended
- **Minimum:** Android 8.0 (API 26)
- **Target:** Android 10+ (API 29+)
- **Optimal:** Android 13+ (API 33+)

---

## 🎯 Feature 1: Wake Lock Testing (BL-013)

### Test Case 1.1: Wake Lock Activation
**Objective:** Verify wake lock is enabled when video playback starts

**Steps:**
1. Open TV Viewer app
2. Navigate to channel list
3. Select any channel
4. Video player screen opens
5. Wait for video to start playing

**Expected Result:**
✅ Screen stays on during playback  
✅ No screen dim or timeout  
✅ Device remains active

**How to Verify:**
- Note device's normal screen timeout (e.g., 30 seconds)
- Let video play for longer than timeout period
- Screen should remain at full brightness
- Device should not go to sleep

**Pass/Fail Criteria:**
- ✅ PASS: Screen stays on for entire video duration
- ❌ FAIL: Screen dims or turns off during playback

---

### Test Case 1.2: Wake Lock Release
**Objective:** Verify wake lock is released when player is closed

**Steps:**
1. Play any video (wake lock active)
2. Press back button to exit player
3. Return to home screen or channel list
4. Wait for normal screen timeout period

**Expected Result:**
✅ Wake lock is released  
✅ Screen timeout returns to normal  
✅ Device screen turns off as usual

**How to Verify:**
- Exit player screen
- Wait for device's configured timeout
- Screen should dim and turn off normally

**Pass/Fail Criteria:**
- ✅ PASS: Screen timeout works normally after exit
- ❌ FAIL: Screen stays on permanently

---

### Test Case 1.3: Wake Lock During App Switch
**Objective:** Verify wake lock behavior when switching apps

**Steps:**
1. Start playing a video
2. Press home button (app goes to background)
3. Open another app
4. Return to TV Viewer

**Expected Result:**
✅ Wake lock released when app backgrounded  
✅ Wake lock re-acquired when app resumed  
✅ No battery drain in background

**Pass/Fail Criteria:**
- ✅ PASS: Proper lifecycle management
- ❌ FAIL: Wake lock persists in background

---

### Test Case 1.4: Wake Lock on Multiple Plays
**Objective:** Verify wake lock works across multiple playback sessions

**Steps:**
1. Play video #1 → exit player
2. Play video #2 → exit player
3. Play video #3 → exit player
4. Verify screen timeout between plays

**Expected Result:**
✅ Wake lock works for each playback  
✅ Released properly each time  
✅ No memory leaks

**Pass/Fail Criteria:**
- ✅ PASS: Consistent behavior across sessions
- ❌ FAIL: Wake lock stops working or persists

---

### Test Case 1.5: Wake Lock with Screen Rotation
**Objective:** Verify wake lock persists through orientation changes

**Steps:**
1. Start video playback (landscape)
2. Rotate device (if app supports portrait player)
3. Rotate back to landscape
4. Observe screen behavior

**Expected Result:**
✅ Wake lock maintained through rotation  
✅ Screen stays on  
✅ No interruption

**Pass/Fail Criteria:**
- ✅ PASS: Screen stays on during rotation
- ❌ FAIL: Wake lock lost on rotation

---

## 📱 Feature 2: Picture-in-Picture Testing (BL-023)

### Test Case 2.1: PiP Availability Check
**Objective:** Verify PiP button visibility based on Android version

**Steps:**
1. Install app on Android 8.0+ device
2. Open player screen
3. Check top control bar

**Expected Result:**
✅ PiP button visible on Android 8.0+  
✅ Button shows picture-in-picture icon  
✅ Button positioned correctly (top-right area)

**Test on Android < 8.0:**
- PiP button should not appear
- No crash or errors

**Pass/Fail Criteria:**
- ✅ PASS: PiP button visible only on supported devices
- ❌ FAIL: Button missing or always shows

---

### Test Case 2.2: Enter PiP Mode
**Objective:** Verify app can enter PiP mode successfully

**Steps:**
1. Play any video
2. Tap PiP button in top-right corner
3. Observe screen transition

**Expected Result:**
✅ Video minimizes to floating window  
✅ Aspect ratio maintained correctly  
✅ Video continues playing  
✅ Controls hidden in PiP

**How to Verify:**
- Window appears in corner of screen
- Video is visible and playing
- No black bars (proper aspect ratio)

**Pass/Fail Criteria:**
- ✅ PASS: Smooth transition to PiP
- ❌ FAIL: Crash, freeze, or video stops

---

### Test Case 2.3: PiP Window Interaction
**Objective:** Verify PiP window can be moved and interacted with

**Steps:**
1. Enter PiP mode (from Test 2.2)
2. Drag PiP window to different corners
3. Tap PiP window
4. Observe behavior

**Expected Result:**
✅ Window can be dragged  
✅ Snaps to corners automatically  
✅ Tap returns to full screen  
✅ Video still playing

**Pass/Fail Criteria:**
- ✅ PASS: Window interactive and responsive
- ❌ FAIL: Window stuck or unresponsive

---

### Test Case 2.4: PiP with App Switching
**Objective:** Verify PiP persists when switching apps

**Steps:**
1. Enter PiP mode
2. Press home button
3. Open another app (e.g., browser, settings)
4. PiP window should float on top
5. Navigate through other app

**Expected Result:**
✅ PiP window stays visible  
✅ Floats above all apps  
✅ Video continues playing  
✅ Can still interact with PiP

**How to Verify:**
- Open 3-4 different apps
- PiP should remain visible in all
- Video should keep playing

**Pass/Fail Criteria:**
- ✅ PASS: PiP persists across all apps
- ❌ FAIL: PiP disappears or crashes

---

### Test Case 2.5: Exit PiP Mode
**Objective:** Verify multiple ways to exit PiP

**Method 1: Tap to Expand**
1. Enter PiP mode
2. Tap PiP window
3. App returns to full screen

**Method 2: Close PiP**
1. Enter PiP mode
2. Swipe PiP window off screen
3. Or tap close button (if available)
4. App closes or backgrounds

**Expected Result:**
✅ Tap returns to full player screen  
✅ Close button stops playback  
✅ Smooth transitions

**Pass/Fail Criteria:**
- ✅ PASS: Both methods work correctly
- ❌ FAIL: Cannot exit PiP or crashes

---

### Test Case 2.6: PiP Aspect Ratios
**Objective:** Verify PiP handles different video aspect ratios

**Steps:**
1. Test with 16:9 video (most common)
2. Test with 4:3 video (classic)
3. Test with 21:9 video (ultrawide)
4. Check PiP window shape for each

**Expected Result:**
✅ 16:9 → Landscape rectangle  
✅ 4:3 → More square-ish  
✅ 21:9 → Wide rectangle  
✅ No black bars in any case

**Pass/Fail Criteria:**
- ✅ PASS: Proper aspect ratio maintained
- ❌ FAIL: Black bars or wrong dimensions

---

### Test Case 2.7: PiP with System UI
**Objective:** Verify PiP works with system notifications and UI

**Steps:**
1. Enter PiP mode
2. Pull down notification shade
3. Open quick settings
4. Receive a notification
5. Check PiP visibility

**Expected Result:**
✅ PiP visible over notification shade  
✅ PiP not covered by system UI  
✅ Still interactive

**Pass/Fail Criteria:**
- ✅ PASS: PiP always visible
- ❌ FAIL: PiP hidden by system UI

---

### Test Case 2.8: PiP Battery Impact
**Objective:** Monitor battery usage in PiP mode

**Steps:**
1. Note battery level
2. Enter PiP mode
3. Let video play for 30 minutes
4. Check battery drain

**Expected Result:**
✅ Similar battery drain as normal playback  
✅ No excessive drain  
✅ No device heating

**Pass/Fail Criteria:**
- ✅ PASS: Battery drain acceptable (~10-15% for 30 min)
- ❌ FAIL: Excessive drain (>20% for 30 min)

---

## 🔧 Integration Testing

### Test Case 3.1: Wake Lock + PiP Combined
**Objective:** Verify both features work together

**Steps:**
1. Start video playback (wake lock active)
2. Enter PiP mode
3. Switch to another app
4. Return to TV Viewer
5. Tap PiP to restore full screen

**Expected Result:**
✅ Wake lock active during full screen  
✅ Wake lock managed properly in PiP  
✅ No conflicts between features  
✅ Smooth transitions

**Pass/Fail Criteria:**
- ✅ PASS: Both features work harmoniously
- ❌ FAIL: Conflicts or issues

---

### Test Case 3.2: Multiple PiP Instances
**Objective:** Verify app handles PiP correctly when reopened

**Steps:**
1. Play video #1, enter PiP
2. Open TV Viewer again (via launcher)
3. Play video #2
4. Check behavior

**Expected Result:**
✅ First PiP closes or pauses  
✅ New video plays normally  
✅ No duplicate PiP windows

**Pass/Fail Criteria:**
- ✅ PASS: Proper PiP management
- ❌ FAIL: Multiple PiP windows or crashes

---

### Test Case 3.3: PiP with External Player
**Objective:** Verify PiP button + external player button don't conflict

**Steps:**
1. Play video
2. Verify both PiP and "Open in External" buttons visible
3. Tap external player button
4. Return to app
5. Try PiP mode

**Expected Result:**
✅ Both buttons work independently  
✅ No conflicts  
✅ Proper button spacing

**Pass/Fail Criteria:**
- ✅ PASS: Independent functionality
- ❌ FAIL: Buttons interfere with each other

---

## 🏗️ Build & Release Testing

### Test Case 4.1: Debug Build
**Objective:** Verify features work in debug build

**Steps:**
```bash
flutter build apk --debug
flutter install
```

**Expected Result:**
✅ Build completes successfully  
✅ App installs on device  
✅ All features work  
✅ Debug logs visible

**Pass/Fail Criteria:**
- ✅ PASS: Debug build works perfectly
- ❌ FAIL: Build errors or runtime issues

---

### Test Case 4.2: Release Build
**Objective:** Verify features work with ProGuard enabled

**Steps:**
```bash
flutter build apk --release
adb install build/app/outputs/flutter-apk/app-release.apk
```

**Expected Result:**
✅ Build completes with ProGuard  
✅ APK size reduced  
✅ All features still work  
✅ No ProGuard-related crashes

**Important Checks:**
- Wake lock still functions
- PiP still functions
- No missing classes errors
- Video playback works

**Pass/Fail Criteria:**
- ✅ PASS: Release build fully functional
- ❌ FAIL: ProGuard breaks features

---

### Test Case 4.3: ProGuard Verification
**Objective:** Verify ProGuard rules are correct

**Steps:**
1. Build release APK
2. Check for ProGuard warnings
3. Run app and check logcat for errors
4. Test all features thoroughly

**Expected Result:**
✅ No ProGuard warnings for our classes  
✅ No ClassNotFoundException errors  
✅ All plugins work correctly

**Check logs for:**
```
E/AndroidRuntime: ClassNotFoundException
E/flutter: PlatformException
```

**Pass/Fail Criteria:**
- ✅ PASS: Clean build and runtime
- ❌ FAIL: ProGuard warnings or errors

---

## 🔍 Edge Case Testing

### Test Case 5.1: Low Battery Mode
**Objective:** Verify features work with battery saver

**Steps:**
1. Enable battery saver mode
2. Test wake lock
3. Test PiP mode

**Expected Result:**
✅ Features still work  
⚠️ May have reduced performance  
✅ Graceful degradation

**Pass/Fail Criteria:**
- ✅ PASS: Features work (possibly limited)
- ❌ FAIL: Complete failure

---

### Test Case 5.2: Memory Pressure
**Objective:** Verify app handles low memory

**Steps:**
1. Open several heavy apps
2. Enter PiP mode with TV Viewer
3. Open more apps
4. System may kill background processes

**Expected Result:**
✅ PiP handles memory pressure  
✅ Graceful recovery if killed  
✅ No data corruption

**Pass/Fail Criteria:**
- ✅ PASS: Handles gracefully
- ❌ FAIL: Crashes or corrupts data

---

### Test Case 5.3: Network Interruption
**Objective:** Verify PiP/wake lock with network issues

**Steps:**
1. Start video playback
2. Enter PiP mode
3. Disable WiFi/data
4. Re-enable network

**Expected Result:**
✅ PiP window remains  
✅ Shows appropriate error  
✅ Recovers when network returns  
✅ Wake lock managed properly

**Pass/Fail Criteria:**
- ✅ PASS: Graceful error handling
- ❌ FAIL: Crash or freeze

---

### Test Case 5.4: Rapid State Changes
**Objective:** Stress test feature transitions

**Steps:**
1. Rapidly tap PiP button (enter/exit)
2. Quickly switch between apps
3. Rotate device rapidly
4. Play/pause repeatedly

**Expected Result:**
✅ No crashes  
✅ Stable behavior  
✅ Proper state management

**Pass/Fail Criteria:**
- ✅ PASS: Handles rapid changes
- ❌ FAIL: Crashes or freezes

---

## 📊 Performance Testing

### Test Case 6.1: App Startup Time
**Objective:** Measure startup time with new features

**Metrics:**
- Cold start: < 3 seconds
- Warm start: < 1 second
- Hot start: < 0.5 seconds

**How to Test:**
```bash
adb shell am start -W com.tvviewer.app/.MainActivity
```

**Pass/Fail Criteria:**
- ✅ PASS: Meets timing targets
- ❌ FAIL: Significantly slower

---

### Test Case 6.2: Memory Usage
**Objective:** Monitor memory consumption

**Steps:**
1. Check baseline memory usage
2. Play video (measure)
3. Enter PiP (measure)
4. Exit PiP (measure)

**Expected Values:**
- Baseline: ~80-100 MB
- Playing: ~120-150 MB
- PiP: ~120-150 MB (same as playing)

**Pass/Fail Criteria:**
- ✅ PASS: Within expected ranges
- ❌ FAIL: Memory leaks or excessive usage

---

### Test Case 6.3: Frame Rate
**Objective:** Verify smooth video playback

**Steps:**
1. Enable "Show frame rate" in developer options
2. Play video
3. Check frame rate overlay

**Expected Result:**
✅ Consistent 30 or 60 FPS  
✅ No significant drops  
✅ Same in PiP mode

**Pass/Fail Criteria:**
- ✅ PASS: Stable frame rate
- ❌ FAIL: Frequent drops or stuttering

---

## ✅ Test Summary Template

Use this template to record test results:

```
Test Date: __________
Tester: __________
Device: __________
Android Version: __________
App Version: __________

WAKE LOCK TESTS:
[ ] Test 1.1: Wake Lock Activation - PASS / FAIL
[ ] Test 1.2: Wake Lock Release - PASS / FAIL
[ ] Test 1.3: Wake Lock App Switch - PASS / FAIL
[ ] Test 1.4: Wake Lock Multiple Plays - PASS / FAIL
[ ] Test 1.5: Wake Lock Rotation - PASS / FAIL

PIP TESTS:
[ ] Test 2.1: PiP Availability - PASS / FAIL
[ ] Test 2.2: Enter PiP Mode - PASS / FAIL
[ ] Test 2.3: PiP Window Interaction - PASS / FAIL
[ ] Test 2.4: PiP App Switching - PASS / FAIL
[ ] Test 2.5: Exit PiP Mode - PASS / FAIL
[ ] Test 2.6: PiP Aspect Ratios - PASS / FAIL
[ ] Test 2.7: PiP System UI - PASS / FAIL
[ ] Test 2.8: PiP Battery Impact - PASS / FAIL

INTEGRATION TESTS:
[ ] Test 3.1: Wake Lock + PiP Combined - PASS / FAIL
[ ] Test 3.2: Multiple PiP Instances - PASS / FAIL
[ ] Test 3.3: PiP with External Player - PASS / FAIL

BUILD TESTS:
[ ] Test 4.1: Debug Build - PASS / FAIL
[ ] Test 4.2: Release Build - PASS / FAIL
[ ] Test 4.3: ProGuard Verification - PASS / FAIL

EDGE CASES:
[ ] Test 5.1: Low Battery Mode - PASS / FAIL
[ ] Test 5.2: Memory Pressure - PASS / FAIL
[ ] Test 5.3: Network Interruption - PASS / FAIL
[ ] Test 5.4: Rapid State Changes - PASS / FAIL

PERFORMANCE:
[ ] Test 6.1: App Startup Time - PASS / FAIL
[ ] Test 6.2: Memory Usage - PASS / FAIL
[ ] Test 6.3: Frame Rate - PASS / FAIL

OVERALL RESULT: PASS / FAIL

Notes:
____________________________________________
____________________________________________
____________________________________________
```

---

## 🐛 Bug Reporting Template

If you find bugs, use this template:

```
BUG REPORT

Title: [Short description]

Severity: [ ] Critical [ ] High [ ] Medium [ ] Low

Feature: [ ] Wake Lock [ ] PiP [ ] Both

Environment:
- Device: 
- Android Version: 
- App Version: 
- Build Type: Debug / Release

Steps to Reproduce:
1. 
2. 
3. 

Expected Behavior:


Actual Behavior:


Screenshots/Logs:


Additional Notes:

```

---

## 📱 Recommended Test Devices

### Minimum Test Coverage
1. **Google Pixel** (Stock Android) - API 26+
2. **Samsung Galaxy** (One UI) - API 26+
3. **OnePlus** (OxygenOS) - API 26+

### Optional Extended Coverage
4. Xiaomi (MIUI) - May have aggressive battery optimization
5. Huawei (EMUI) - May have PiP restrictions
6. Oppo (ColorOS) - Different PiP behavior

---

## 🎯 Success Criteria

### Must Pass (Blocking)
- ✅ All wake lock tests (1.1-1.5)
- ✅ Basic PiP tests (2.1-2.5)
- ✅ Release build test (4.2)
- ✅ No critical bugs

### Should Pass (Important)
- ✅ Integration tests (3.1-3.3)
- ✅ PiP aspect ratio (2.6)
- ✅ ProGuard verification (4.3)

### Nice to Have (Optional)
- ✅ Edge cases (5.1-5.4)
- ✅ Performance tests (6.1-6.3)
- ✅ Extended device coverage

---

**Test Plan Version:** 1.0  
**Last Updated:** 2024  
**Status:** Ready for QA

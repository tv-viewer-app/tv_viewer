# TV Viewer Flutter App - Comprehensive Test Plan
**Version:** 1.5.0  
**Date:** 2024  
**Test Environment:** Flutter 3.0.0+

---

## Table of Contents
1. [Test Scope](#test-scope)
2. [Test Environment](#test-environment)
3. [Functional Test Cases](#functional-test-cases)
4. [Edge Case Test Cases](#edge-case-test-cases)
5. [Error Scenario Test Cases](#error-scenario-test-cases)
6. [UI/UX Validation Test Cases](#uiux-validation-test-cases)
7. [Integration Test Cases](#integration-test-cases)
8. [Performance Test Cases](#performance-test-cases)
9. [Security Test Cases](#security-test-cases)
10. [Regression Test Cases](#regression-test-cases)

---

## Test Scope

### In-Scope Features
- Channel list display and rendering
- TV/Radio media type filtering
- Category dropdown filter
- Country dropdown filter
- Search functionality
- Video playback with VideoPlayer
- External player integration (VLC, MX Player)
- Cast button
- Resolution/bitrate display
- Channel validation scanning
- Caching and persistence
- Dark/Light theme switching

### Out-of-Scope
- Backend API testing (external M3U repositories)
- Actual video streaming quality
- External app behavior (VLC, MX Player)
- Network infrastructure

---

## Test Environment

### Required Devices/Emulators
- Android 5.0+ (API 21+) - Minimum supported
- Android 10+ (API 29+) - Recommended
- Various screen sizes: Phone (5", 6", 6.7"), Tablet (7", 10")

### Network Conditions
- WiFi (High speed)
- 4G/LTE (Medium speed)
- 3G (Low speed)
- Offline mode
- Intermittent connectivity

### Test Data
- Live M3U repositories:
  - `https://iptv-org.github.io/iptv/index.m3u`
  - `https://iptv-org.github.io/iptv/index.category.m3u`
- Cached channel data
- Sample channels with various attributes

---

## Functional Test Cases

### FC-1: Channel List Display

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| FC-1.1 | Display all channels on app launch | 1. Launch app<br>2. Observe channel list | All channels displayed with name, logo, category, resolution, bitrate, country | High |
| FC-1.2 | Display working status icon | 1. Launch app<br>2. Check validated channels | Green checkmark for working channels, red X for failed channels | High |
| FC-1.3 | Display channel logos | 1. Scroll through channel list<br>2. Observe logos | Channel logos load correctly, fallback to TV/Radio icon if missing | Medium |
| FC-1.4 | Display channel metadata | 1. View channel subtitle<br>2. Verify format | Shows: Category + Resolution + Bitrate + Country (e.g., "News - 720p - 2.5 Mbps - US") | Medium |
| FC-1.5 | Tap channel to play | 1. Tap any channel<br>2. Observe navigation | Navigates to PlayerScreen with video playing | High |
| FC-1.6 | Efficient scrolling | 1. Scroll rapidly through 1000+ channels | Smooth scrolling without lag or stuttering | High |

### FC-2: TV/Radio Media Type Filtering

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| FC-2.1 | Default "All" filter | 1. Launch app<br>2. Observe filter state | Media type shows "All", displays both TV and Radio channels | High |
| FC-2.2 | Filter TV channels | 1. Tap TV filter button<br>2. Observe list | Only TV channels displayed, Radio channels hidden | High |
| FC-2.3 | Filter Radio channels | 1. Tap Radio filter button<br>2. Observe list | Only Radio channels displayed, TV channels hidden | High |
| FC-2.4 | Toggle back to All | 1. Select TV or Radio<br>2. Tap All button<br>3. Observe list | All channels displayed again | High |
| FC-2.5 | Visual indication of active filter | 1. Select TV/Radio<br>2. Check button style | Active filter button shows selected state (filled style) | Medium |

### FC-3: Category Dropdown Filter

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| FC-3.1 | Display category dropdown | 1. Tap category dropdown<br>2. Observe options | Shows "All Categories" + list of unique categories from channels | High |
| FC-3.2 | Default category selection | 1. Launch app<br>2. Check category dropdown | Default shows "All Categories", no filtering applied | High |
| FC-3.3 | Select specific category | 1. Open category dropdown<br>2. Select a category (e.g., "News")<br>3. Observe list | Only channels with selected category displayed | High |
| FC-3.4 | Category normalization | 1. Check categories with semicolons (e.g., "News;Sports")<br>2. Verify dropdown | Only first part "News" appears, properly capitalized | Medium |
| FC-3.5 | Reset category filter | 1. Select a category<br>2. Select "All Categories"<br>3. Observe list | All channels displayed again | High |
| FC-3.6 | Category count accuracy | 1. Select a category<br>2. Count displayed channels<br>3. Verify count | Channel count matches filter result | Low |

### FC-4: Country Dropdown Filter

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| FC-4.1 | Display country dropdown | 1. Tap country dropdown<br>2. Observe options | Shows "All Countries" + alphabetically sorted list of countries | High |
| FC-4.2 | Default country selection | 1. Launch app<br>2. Check country dropdown | Default shows "All Countries", no filtering applied | High |
| FC-4.3 | Select specific country | 1. Open country dropdown<br>2. Select a country (e.g., "US")<br>3. Observe list | Only channels from selected country displayed | High |
| FC-4.4 | Country alphabetical sorting | 1. Open country dropdown<br>2. Verify order | Countries listed alphabetically | Medium |
| FC-4.5 | Reset country filter | 1. Select a country<br>2. Select "All Countries"<br>3. Observe list | All channels displayed again | High |

### FC-5: Search Functionality

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| FC-5.1 | Display search bar | 1. Launch app<br>2. Locate search bar | Search bar visible at top with hint text | High |
| FC-5.2 | Search by channel name | 1. Type "CNN" in search<br>2. Observe results | Only channels with "CNN" in name displayed | High |
| FC-5.3 | Case-insensitive search | 1. Type "cnn" (lowercase)<br>2. Observe results | Same results as "CNN" or "Cnn" | High |
| FC-5.4 | Real-time search | 1. Type characters one by one<br>2. Observe list updates | List filters after each character typed | Medium |
| FC-5.5 | Clear search | 1. Enter search text<br>2. Tap clear button (X)<br>3. Observe list | Search cleared, all channels displayed | High |
| FC-5.6 | Search with no results | 1. Type gibberish text<br>2. Observe result | Shows empty state or "No channels found" message | Medium |
| FC-5.7 | Partial match search | 1. Type "news"<br>2. Observe results | Matches "News", "CNN News", "BBC World News", etc. | High |

### FC-6: Combined Filters

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| FC-6.1 | Media type + Category | 1. Select TV<br>2. Select "News" category<br>3. Observe results | Only TV channels in News category | High |
| FC-6.2 | Media type + Country | 1. Select Radio<br>2. Select "US" country<br>3. Observe results | Only Radio channels from US | High |
| FC-6.3 | Category + Country | 1. Select "Sports" category<br>2. Select "UK" country<br>3. Observe results | Only Sports channels from UK | High |
| FC-6.4 | All three filters | 1. Select TV<br>2. Select "News"<br>3. Select "US"<br>4. Observe results | Only US TV News channels | High |
| FC-6.5 | Filters + Search | 1. Select TV<br>2. Select "News"<br>3. Type "CNN"<br>4. Observe results | Only TV News channels with "CNN" in name | High |
| FC-6.6 | Clear all filters | 1. Apply multiple filters<br>2. Reset each to default<br>3. Observe results | All channels displayed | Medium |

### FC-7: Video Playback

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| FC-7.1 | Play channel | 1. Tap a working channel<br>2. Observe playback | Video starts playing automatically in landscape mode | High |
| FC-7.2 | Auto-landscape orientation | 1. Open player<br>2. Check orientation | Forces landscape orientation | High |
| FC-7.3 | Fullscreen immersive mode | 1. Play video<br>2. Check UI | Status/navigation bars hidden, fullscreen video | High |
| FC-7.4 | Display video metadata | 1. Play video<br>2. Check top bar | Shows channel name, resolution, bitrate | Medium |
| FC-7.5 | Play/Pause button | 1. Tap play/pause button<br>2. Verify state | Video pauses/resumes correctly | High |
| FC-7.6 | Double-tap to play/pause | 1. Double-tap anywhere on video<br>2. Verify state | Video pauses/resumes | Medium |
| FC-7.7 | Single tap to toggle controls | 1. Tap once on video<br>2. Observe controls | Controls show/hide | Medium |
| FC-7.8 | Auto-hide controls | 1. Show controls<br>2. Wait 3 seconds<br>3. Observe | Controls automatically hide | Low |
| FC-7.9 | Back button | 1. Play video<br>2. Tap back button<br>3. Verify navigation | Returns to channel list in portrait mode | High |
| FC-7.10 | System back button | 1. Play video<br>2. Press Android back button<br>3. Verify navigation | Returns to channel list in portrait mode | High |

### FC-8: External Player Integration

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| FC-8.1 | Open in VLC | 1. Play channel<br>2. Tap external player button<br>3. Select VLC | Opens VLC app with stream URL | High |
| FC-8.2 | Open in MX Player | 1. Play channel<br>2. Tap external player button<br>3. Select MX Player | Opens MX Player app with stream URL | High |
| FC-8.3 | VLC not installed fallback | 1. Uninstall VLC<br>2. Tap external player button<br>3. Observe behavior | Tries MX Player or shows error dialog | Medium |
| FC-8.4 | No external player installed | 1. Ensure no players installed<br>2. Tap external player button<br>3. Observe behavior | Shows error with option to copy URL to clipboard | Medium |
| FC-8.5 | External player button visibility | 1. Play any channel<br>2. Check player controls | External player button visible and accessible | Medium |

### FC-9: Cast Button

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| FC-9.1 | Cast button display | 1. Play any channel<br>2. Check controls | Cast button visible in player controls | High |
| FC-9.2 | Tap cast button | 1. Tap cast button<br>2. Observe behavior | Shows informational dialog about casting | High |
| FC-9.3 | Cast dialog content | 1. Open cast dialog<br>2. Read content | Explains casting requires external apps, provides instructions | Medium |
| FC-9.4 | Close cast dialog | 1. Open cast dialog<br>2. Tap outside or close button | Dialog closes, returns to video | Low |

### FC-10: Resolution/Bitrate Display

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| FC-10.1 | Display in channel list | 1. View channel list<br>2. Check subtitle | Shows resolution (e.g., "720p") and bitrate (e.g., "2.5 Mbps") | High |
| FC-10.2 | Display in player | 1. Play channel<br>2. Check top bar | Shows resolution and bitrate in player metadata | High |
| FC-10.3 | Resolution extraction | 1. Play channel with "(720p)" in name<br>2. Verify display | Correctly extracts and displays "720p" | Medium |
| FC-10.4 | Bitrate formatting | 1. Check channels with various bitrates<br>2. Verify format | Formats as Mbps (e.g., "2.5 Mbps") or Kbps (e.g., "500 Kbps") | Medium |
| FC-10.5 | Missing resolution/bitrate | 1. Check channels without metadata<br>2. Verify display | Shows "N/A" or omits field gracefully | Low |

### FC-11: Channel Validation Scanning

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| FC-11.1 | Start validation scan | 1. Tap refresh button<br>2. Observe behavior | Validation scan starts, progress bar appears | High |
| FC-11.2 | Display scan progress | 1. Start scan<br>2. Observe progress bar | Shows "X/Y channels scanned" with live updates | High |
| FC-11.3 | Display working count | 1. During scan<br>2. Check working count | Shows incrementing count of working channels | High |
| FC-11.4 | Display failed count | 1. During scan<br>2. Check failed count | Shows incrementing count of failed channels | High |
| FC-11.5 | Batch processing | 1. Start scan<br>2. Monitor network requests | Processes 5 channels concurrently with 50ms delays | Medium |
| FC-11.6 | Update channel status | 1. Complete scan<br>2. Check channel icons | Working channels show green check, failed show red X | High |
| FC-11.7 | Stop validation | 1. Start scan<br>2. Tap stop button<br>3. Verify behavior | Scan stops immediately, partial results saved | High |
| FC-11.8 | Scan timeout | 1. Start scan on slow network<br>2. Observe behavior | Each channel times out after 5 seconds | Medium |
| FC-11.9 | Accept valid status codes | 1. Check validation logic<br>2. Verify codes | Accepts 200, 206, 301, 302 as working | Low |
| FC-11.10 | Cache validation results | 1. Complete scan<br>2. Restart app<br>3. Check status | Validation results persist across app restarts | High |
| FC-11.11 | Timestamp last checked | 1. Complete scan<br>2. Check channel data | Each channel has `lastChecked` timestamp | Low |

### FC-12: Caching and Persistence

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| FC-12.1 | First launch load | 1. Fresh install<br>2. Launch app<br>3. Observe loading | Shows loading indicator, fetches channels from network | High |
| FC-12.2 | Cached launch load | 1. Launch app after first use<br>2. Observe loading | Loads cached channels instantly, background sync updates | High |
| FC-12.3 | Background channel update | 1. Launch with cache<br>2. Wait for background sync<br>3. Check channels | New channels added, old channels updated | Medium |
| FC-12.4 | Offline mode | 1. Enable airplane mode<br>2. Launch app<br>3. Observe behavior | Shows cached channels, displays offline message | High |
| FC-12.5 | Cache invalidation | 1. Clear app data<br>2. Launch app<br>3. Observe behavior | Fetches fresh channels from network | Medium |
| FC-12.6 | Filter state persistence | 1. Apply filters<br>2. Navigate to player<br>3. Return to list | Filter state preserved (filters still applied) | Medium |

### FC-13: Theme Switching

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| FC-13.1 | Default theme | 1. Fresh install<br>2. Launch app<br>3. Check theme | Follows system theme (light/dark) | Medium |
| FC-13.2 | Light theme display | 1. Set system to light mode<br>2. Launch app<br>3. Verify colors | Uses light theme colors correctly | Medium |
| FC-13.3 | Dark theme display | 1. Set system to dark mode<br>2. Launch app<br>3. Verify colors | Uses dark theme colors correctly | Medium |
| FC-13.4 | Theme consistency | 1. Switch system theme<br>2. Check all screens | Theme consistent across channel list and player | Low |

---

## Edge Case Test Cases

### EC-1: Data Edge Cases

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| EC-1.1 | Empty channel list | 1. Mock empty M3U response<br>2. Launch app<br>3. Observe UI | Shows empty state with refresh option | High |
| EC-1.2 | Single channel | 1. Mock M3U with 1 channel<br>2. Apply filters<br>3. Verify behavior | Handles single channel correctly, filters work | Low |
| EC-1.3 | Very long channel name | 1. Load channel with 200+ char name<br>2. Observe display | Text truncates with ellipsis, no overflow | Medium |
| EC-1.4 | Missing channel name | 1. Load channel with empty name<br>2. Observe display | Shows placeholder or "Untitled Channel" | Medium |
| EC-1.5 | Missing logo URL | 1. Load channel without logo<br>2. Observe display | Shows TV/Radio fallback icon | Medium |
| EC-1.6 | Invalid logo URL | 1. Load channel with broken logo URL<br>2. Observe display | Shows fallback icon after load failure | Medium |
| EC-1.7 | Missing category | 1. Load channel without category<br>2. Check filters | Shows as "Uncategorized" or similar | Low |
| EC-1.8 | Missing country | 1. Load channel without country<br>2. Check filters | Shows as "Unknown" or omitted | Low |
| EC-1.9 | Duplicate channels | 1. Load M3U with duplicate URLs<br>2. Verify list | Deduplicates by URL, shows only once | Medium |
| EC-1.10 | 10,000+ channels | 1. Load very large M3U<br>2. Test scrolling and filtering | Handles efficiently without performance issues | High |
| EC-1.11 | Special characters in name | 1. Load channel with Unicode/emoji<br>2. Observe display | Displays special characters correctly | Low |
| EC-1.12 | Special characters in URL | 1. Load channel with encoded URL<br>2. Test playback | URL decodes and plays correctly | Medium |

### EC-2: Filter Edge Cases

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| EC-2.1 | Filter with zero results | 1. Select obscure category<br>2. Add country filter<br>3. Add search term<br>4. Observe | Shows "No channels found" message | High |
| EC-2.2 | Search with only spaces | 1. Type "   " in search<br>2. Observe results | Shows all channels or trims whitespace | Medium |
| EC-2.3 | Search with special chars | 1. Type "!@#$%^&*()" in search<br>2. Observe behavior | Handles gracefully, matches if channel name contains | Low |
| EC-2.4 | Category with no channels | 1. Select category from old cache<br>2. After update has no channels<br>3. Observe | Shows empty state or removes from dropdown | Low |
| EC-2.5 | Rapid filter changes | 1. Quickly toggle filters<br>2. Observe performance | Updates smoothly without lag or crashes | Medium |
| EC-2.6 | Filter state after clear cache | 1. Apply filters<br>2. Clear app cache<br>3. Relaunch<br>4. Verify | Filters reset to default | Low |

### EC-3: Video Playback Edge Cases

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| EC-3.1 | Play unavailable stream | 1. Play channel that's offline<br>2. Observe behavior | Shows error with retry and external player options | High |
| EC-3.2 | Play stream with auth | 1. Play channel requiring authentication<br>2. Observe behavior | Fails gracefully with error message | Medium |
| EC-3.3 | Play very slow stream | 1. Play low-bandwidth stream on WiFi<br>2. Observe buffering | Shows loading indicator, plays when buffered | Medium |
| EC-3.4 | Switch channels rapidly | 1. Play channel A<br>2. Immediately back and play B<br>3. Repeat 5 times<br>4. Verify | Handles rapid switches without crash or memory leak | High |
| EC-3.5 | Minimize app during playback | 1. Play video<br>2. Press home button<br>3. Return to app | Video pauses or continues based on implementation | Medium |
| EC-3.6 | Rotate device during playback | 1. Play video (landscape)<br>2. Rotate device<br>3. Observe | Maintains landscape lock, no disruption | Low |
| EC-3.7 | Very long playback session | 1. Play channel<br>2. Let run for 1+ hour<br>3. Monitor | Plays continuously without crashes or leaks | Medium |
| EC-3.8 | Network drop during playback | 1. Play video<br>2. Disable WiFi/data mid-stream<br>3. Observe | Shows error, offers retry when reconnected | High |
| EC-3.9 | Play stream with no video | 1. Play Radio channel<br>2. Observe player | Shows audio controls, blank video area (expected) | Low |
| EC-3.10 | Resume after interruption | 1. Play video<br>2. Receive phone call<br>3. End call<br>4. Return to app | Video pauses during call, allows resume after | Medium |

### EC-4: Validation Edge Cases

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| EC-4.1 | Validate with offline network | 1. Enable airplane mode<br>2. Start validation scan<br>3. Observe | Shows network error, scan fails gracefully | High |
| EC-4.2 | Validate single channel | 1. Filter to 1 channel<br>2. Start scan<br>3. Observe | Validates single channel correctly | Low |
| EC-4.3 | Validate 10,000 channels | 1. Load large list<br>2. Start scan<br>3. Monitor progress | Completes without crash, shows accurate progress | High |
| EC-4.4 | Stop scan immediately | 1. Start scan<br>2. Immediately tap stop<br>3. Verify | Stops with minimal channels validated | Medium |
| EC-4.5 | Network drops during scan | 1. Start scan<br>2. Disable network midway<br>3. Observe | Marks remaining as failed, shows error | Medium |
| EC-4.6 | All channels working | 1. Mock all 200 OK responses<br>2. Complete scan<br>3. Verify | Shows 100% working, 0% failed | Low |
| EC-4.7 | All channels failed | 1. Mock all timeout/error responses<br>2. Complete scan<br>3. Verify | Shows 0% working, 100% failed | Low |
| EC-4.8 | Validate immediately after app start | 1. Launch app<br>2. Immediately tap refresh<br>3. Observe | Validates while channels still loading | Medium |
| EC-4.9 | Multiple scans in succession | 1. Complete scan<br>2. Immediately start another<br>3. Repeat 3 times<br>4. Verify | Each scan completes correctly, no state issues | Medium |

### EC-5: UI/Orientation Edge Cases

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| EC-5.1 | Small screen device (4.5") | 1. Test on small phone<br>2. Verify all UI elements | All elements visible and usable | Medium |
| EC-5.2 | Large tablet (10") | 1. Test on tablet<br>2. Verify layout | Layout adapts appropriately, no stretched UI | Medium |
| EC-5.3 | Ultra-wide screen | 1. Test on 21:9 aspect ratio<br>2. Verify player | Video scales correctly, no distortion | Low |
| EC-5.4 | Split-screen mode | 1. Use Android split-screen<br>2. Open app in half-screen<br>3. Verify | App functions in reduced size | Low |
| EC-5.5 | Picture-in-picture | 1. Play video<br>2. Press home (if PiP enabled)<br>3. Observe | PiP works if implemented, otherwise pauses | Low |

### EC-6: Memory and Performance Edge Cases

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| EC-6.1 | Low memory device | 1. Test on device with <2GB RAM<br>2. Load channels<br>3. Play video | Functions without crashes or OOM errors | High |
| EC-6.2 | Background apps running | 1. Open 10+ apps<br>2. Launch TV Viewer<br>3. Test features | Performs adequately despite limited resources | Medium |
| EC-6.3 | Repeated app lifecycle | 1. Launch app<br>2. Background<br>3. Force-stop<br>4. Relaunch<br>5. Repeat 10 times | No memory leaks or degradation | Medium |
| EC-6.4 | Scroll through entire list | 1. Load 5000+ channels<br>2. Scroll from top to bottom<br>3. Monitor memory | Memory usage remains stable, no leaks | High |

---

## Error Scenario Test Cases

### ES-1: Network Errors

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| ES-1.1 | No internet on first launch | 1. Fresh install<br>2. Disable network<br>3. Launch app | Shows "No internet" error with retry button | High |
| ES-1.2 | Network timeout | 1. Simulate very slow network<br>2. Launch app<br>3. Wait for timeout | Shows timeout error after 30 seconds | High |
| ES-1.3 | M3U URL unreachable | 1. Mock 404 response from M3U URL<br>2. Fetch channels<br>3. Observe | Shows error message, tries fallback repository | High |
| ES-1.4 | Server error (500) | 1. Mock 500 response<br>2. Fetch channels<br>3. Observe | Shows server error message with retry | Medium |
| ES-1.5 | Malformed M3U response | 1. Mock invalid M3U format<br>2. Parse channels<br>3. Observe | Shows parse error, doesn't crash | Medium |
| ES-1.6 | Partial M3U download | 1. Mock incomplete response<br>2. Parse channels<br>3. Verify | Parses available channels, shows warning | Low |
| ES-1.7 | Network drops during load | 1. Start loading channels<br>2. Disable network midway<br>3. Observe | Shows error, displays cached channels if available | High |
| ES-1.8 | SSL certificate error | 1. Mock SSL error<br>2. Fetch channels<br>3. Observe | Shows security error with appropriate message | Medium |
| ES-1.9 | DNS resolution failure | 1. Mock DNS failure<br>2. Fetch channels<br>3. Observe | Shows connection error with retry | Medium |

### ES-2: Video Playback Errors

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| ES-2.1 | Stream URL 404 | 1. Play channel with dead URL<br>2. Observe error | Shows error dialog with retry and external player options | High |
| ES-2.2 | Stream URL 403 | 1. Play forbidden stream<br>2. Observe error | Shows "Access denied" error with options | High |
| ES-2.3 | Unsupported video codec | 1. Play stream with unsupported codec<br>2. Observe | Shows codec error, suggests external player | Medium |
| ES-2.4 | Corrupted stream data | 1. Play stream with corrupted data<br>2. Observe | Shows playback error, offers retry/external player | Medium |
| ES-2.5 | Infinite buffering | 1. Play very slow stream<br>2. Wait 60+ seconds<br>3. Observe | Shows timeout or buffering error, offers options | High |
| ES-2.6 | Stream stops mid-playback | 1. Play working stream<br>2. Stream ends unexpectedly<br>3. Observe | Detects end, shows error with retry | Medium |
| ES-2.7 | Invalid stream URL format | 1. Play channel with malformed URL<br>2. Observe | Shows URL error without crash | Low |
| ES-2.8 | Geoblock restriction | 1. Play geo-restricted stream<br>2. Observe | Shows access error, suggests external player | Low |

### ES-3: Data Validation Errors

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| ES-3.1 | Null channel name | 1. Load channel with null name<br>2. Observe display | Shows "Unknown Channel" placeholder | Medium |
| ES-3.2 | Null stream URL | 1. Load channel with null URL<br>2. Try to play<br>3. Observe | Shows error, doesn't crash | High |
| ES-3.3 | Extremely large bitrate | 1. Load channel with 999999999 bps<br>2. Observe display | Formats correctly as "999 Mbps" or similar | Low |
| ES-3.4 | Negative bitrate | 1. Load channel with negative bitrate<br>2. Observe display | Shows "N/A" or 0, handles gracefully | Low |
| ES-3.5 | Invalid date format | 1. Load channel with malformed lastChecked<br>2. Observe | Handles gracefully, shows "Never" or similar | Low |
| ES-3.6 | Missing required fields | 1. Load minimal channel (only name + URL)<br>2. Verify display | Shows with defaults for missing fields | Medium |

### ES-4: External App Errors

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| ES-4.1 | VLC not installed | 1. Tap external player<br>2. Select VLC<br>3. Observe | Shows "VLC not installed" error, offers MX Player | High |
| ES-4.2 | MX Player not installed | 1. VLC fails<br>2. Try MX Player<br>3. Observe | Shows "MX Player not installed" error | High |
| ES-4.3 | No external player installed | 1. Tap external player<br>2. Both players fail<br>3. Observe | Shows dialog with "Copy URL" option | High |
| ES-4.4 | External app crashes | 1. Open VLC<br>2. VLC crashes immediately<br>3. Return to app | Returns gracefully to TV Viewer app | Medium |
| ES-4.5 | External app intent failure | 1. Mock intent failure<br>2. Try external player<br>3. Observe | Shows error, offers alternative | Medium |

### ES-5: Cache and Storage Errors

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| ES-5.1 | Full storage | 1. Fill device storage to 100%<br>2. Try to cache channels<br>3. Observe | Shows storage error, functions with network only | High |
| ES-5.2 | Cache read failure | 1. Corrupt SharedPreferences<br>2. Launch app<br>3. Observe | Detects corruption, fetches fresh data | Medium |
| ES-5.3 | Cache write failure | 1. Mock write permission denial<br>2. Fetch channels<br>3. Observe | Shows channels but warns about cache failure | Medium |
| ES-5.4 | Cache version mismatch | 1. Load old cache format<br>2. Launch new app version<br>3. Observe | Migrates or clears old cache, fetches fresh | Low |

### ES-6: State Management Errors

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| ES-6.1 | Concurrent filter changes | 1. Apply multiple filters simultaneously<br>2. Observe results | Last filter applied correctly, no race conditions | Medium |
| ES-6.2 | Filter during loading | 1. Start loading channels<br>2. Apply filters immediately<br>3. Observe | Filters apply once channels loaded | Medium |
| ES-6.3 | Navigate during scan | 1. Start validation scan<br>2. Navigate to player<br>3. Return<br>4. Verify scan | Scan continues in background or pauses/resumes | Medium |
| ES-6.4 | Force-close during scan | 1. Start scan<br>2. Force-close app<br>3. Relaunch<br>4. Check state | Scan resets, no corrupted state | High |
| ES-6.5 | Multiple instances | 1. Open app<br>2. Use recent apps to "duplicate"<br>3. Interact with both | Maintains single instance or state sync | Low |

---

## UI/UX Validation Test Cases

### UX-1: Visual Design

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| UX-1.1 | Color scheme consistency | 1. Navigate all screens<br>2. Check colors | Consistent blue (#0078D4) accent color throughout | High |
| UX-1.2 | Material Design 3 compliance | 1. Check UI components<br>2. Verify MD3 patterns | Uses Material 3 components and design patterns | Medium |
| UX-1.3 | Dark theme contrast | 1. Enable dark theme<br>2. Check readability | Sufficient contrast, text easily readable | High |
| UX-1.4 | Light theme contrast | 1. Enable light theme<br>2. Check readability | Sufficient contrast, no glare issues | High |
| UX-1.5 | Icon clarity | 1. Check all icons<br>2. Verify meanings | Icons intuitive and recognizable | Medium |
| UX-1.6 | Text truncation | 1. View long channel names<br>2. Verify truncation | Truncates with ellipsis, no text cutoff | Medium |
| UX-1.7 | Image aspect ratios | 1. View channel logos<br>2. Check proportions | Logos display without distortion | Medium |
| UX-1.8 | Spacing and padding | 1. View all screens<br>2. Check element spacing | Consistent spacing, not cramped or sparse | Low |

### UX-2: Interaction Feedback

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| UX-2.1 | Button press feedback | 1. Tap any button<br>2. Observe feedback | Shows visual feedback (ripple effect) | High |
| UX-2.2 | Loading indicators | 1. Trigger loading states<br>2. Observe indicators | Shows clear loading spinner or progress bar | High |
| UX-2.3 | Pull-to-refresh | 1. Pull down on channel list<br>2. Observe | Shows refresh indicator if implemented | Medium |
| UX-2.4 | Empty state messages | 1. Filter to zero results<br>2. Read message | Shows helpful message with action suggestion | High |
| UX-2.5 | Error message clarity | 1. Trigger various errors<br>2. Read messages | Error messages clear and actionable | High |
| UX-2.6 | Success feedback | 1. Complete validation scan<br>2. Observe feedback | Shows completion message or summary | Medium |
| UX-2.7 | Tap target size | 1. Tap all interactive elements<br>2. Verify size | Minimum 48x48dp touch targets | High |

### UX-3: Navigation Flow

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| UX-3.1 | Logical navigation | 1. Navigate through app<br>2. Check flow | Navigation follows expected patterns | High |
| UX-3.2 | Back button behavior | 1. Navigate screens<br>2. Press back repeatedly<br>3. Verify | Returns to previous screen logically | High |
| UX-3.3 | Exit on final back | 1. On home screen<br>2. Press back<br>3. Observe | Exits app or shows exit confirmation | Medium |
| UX-3.4 | Deep link handling | 1. Open channel URL directly<br>2. Verify behavior | Opens player directly if implemented | Low |
| UX-3.5 | State preservation | 1. Apply filters<br>2. Navigate away and back<br>3. Verify | Preserves filter state | Medium |

### UX-4: Information Architecture

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| UX-4.1 | Channel info hierarchy | 1. View channel list<br>2. Check info display | Name prominent, metadata secondary but visible | High |
| UX-4.2 | Filter organization | 1. Check filter layout<br>2. Verify grouping | Filters logically grouped and labeled | High |
| UX-4.3 | Search placement | 1. Locate search bar<br>2. Verify position | Search easily accessible at top | High |
| UX-4.4 | Action button placement | 1. Check primary actions<br>2. Verify placement | Primary actions in expected locations (FAB, app bar) | Medium |
| UX-4.5 | Metadata readability | 1. View channel metadata<br>2. Check clarity | Resolution, bitrate, country clearly displayed | Medium |

### UX-5: Accessibility

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| UX-5.1 | Screen reader support | 1. Enable TalkBack<br>2. Navigate app<br>3. Verify | All elements have meaningful labels | High |
| UX-5.2 | Semantic labels | 1. Check button labels<br>2. Verify descriptions | Buttons have descriptive contentDescription | High |
| UX-5.3 | Focus order | 1. Tab through elements<br>2. Verify order | Focus moves in logical order | Medium |
| UX-5.4 | Color contrast (WCAG) | 1. Check text/background contrast<br>2. Verify ratio | Meets WCAG AA (4.5:1 for text) | High |
| UX-5.5 | Text scaling | 1. Increase system font size<br>2. Verify app layout | Text scales, layout doesn't break | High |
| UX-5.6 | Icon-only buttons | 1. Check buttons without text<br>2. Verify labels | All icon buttons have accessibility labels | High |

### UX-6: Performance Perception

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| UX-6.1 | Initial load time | 1. Launch app<br>2. Measure time to usable | Shows cached data within 1 second | High |
| UX-6.2 | Filter response time | 1. Change filter<br>2. Measure update time | Updates within 100ms | High |
| UX-6.3 | Search responsiveness | 1. Type in search<br>2. Measure lag | Updates within 200ms per keystroke | High |
| UX-6.4 | Scroll smoothness | 1. Scroll quickly<br>2. Observe fluidity | Maintains 60fps, no janking | High |
| UX-6.5 | Video start time | 1. Tap channel<br>2. Measure to first frame | Video starts within 3 seconds on good network | Medium |
| UX-6.6 | Animation fluidity | 1. Observe all animations<br>2. Check smoothness | Animations smooth at 60fps | Medium |

### UX-7: Usability

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| UX-7.1 | First-time user experience | 1. Fresh install<br>2. Launch app<br>3. Use features | Intuitive, no tutorial needed for basic use | High |
| UX-7.2 | Filter discoverability | 1. New user<br>2. Find filters<br>3. Verify ease | Filters easily discoverable and understandable | High |
| UX-7.3 | Search discoverability | 1. New user<br>2. Locate search<br>3. Verify ease | Search bar prominent and obvious | High |
| UX-7.4 | Action clarity | 1. View all buttons<br>2. Understand purpose | All actions clearly labeled or iconically obvious | High |
| UX-7.5 | Error recovery | 1. Trigger error<br>2. Follow recovery steps<br>3. Verify | Clear path to recover from errors | High |
| UX-7.6 | Undo capability | 1. Apply filters<br>2. Try to undo<br>3. Verify | Can easily clear/reset filters | Medium |

### UX-8: Content Display

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| UX-8.1 | Channel list density | 1. View list<br>2. Count visible items | Balanced density, ~6-8 items on average phone | Medium |
| UX-8.2 | Logo sizing | 1. View logos<br>2. Check size | Logos appropriately sized, not pixelated | Medium |
| UX-8.3 | Text hierarchy | 1. View channel info<br>2. Check sizes | Clear hierarchy: title > subtitle > metadata | High |
| UX-8.4 | Metadata formatting | 1. View channel subtitles<br>2. Check format | Metadata separated clearly (e.g., " - " separators) | Medium |
| UX-8.5 | Status indicators | 1. Check working/failed icons<br>2. Verify clarity | Icons color-coded and intuitive (green/red) | High |
| UX-8.6 | Video controls layout | 1. Play video<br>2. Check controls | Controls well-organized, not overlapping | High |

---

## Integration Test Cases

### IT-1: End-to-End User Flows

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| IT-1.1 | Complete first-time flow | 1. Fresh install<br>2. Launch app<br>3. Browse channels<br>4. Apply filters<br>5. Search<br>6. Play video<br>7. Return to list | Complete flow works seamlessly | High |
| IT-1.2 | Filter and play flow | 1. Launch app<br>2. Select category<br>3. Select country<br>4. Search<br>5. Play result | Filters work together, plays correct channel | High |
| IT-1.3 | Scan and play flow | 1. Launch app<br>2. Start validation<br>3. Wait for completion<br>4. Play working channel | Validation updates status, plays working channel | High |
| IT-1.4 | External player flow | 1. Play channel<br>2. Tap external player<br>3. Open in VLC<br>4. Return to app | External player opens, can return to app | High |
| IT-1.5 | Offline to online flow | 1. Launch offline<br>2. View cached channels<br>3. Enable network<br>4. Refresh | Transitions smoothly from cache to live data | High |

### IT-2: State Persistence Flows

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| IT-2.1 | App lifecycle flow | 1. Launch app<br>2. Apply filters<br>3. Background app<br>4. Kill from memory<br>5. Relaunch | Restores to default state, loads cached data | High |
| IT-2.2 | Validation persistence flow | 1. Complete scan<br>2. Close app<br>3. Relaunch<br>4. Check status | Validation results persist | High |
| IT-2.3 | Cache update flow | 1. Launch with cache<br>2. Background sync completes<br>3. Check channels | New channels appear without UI disruption | Medium |

### IT-3: Multi-Feature Interactions

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| IT-3.1 | Filter during scan | 1. Start validation<br>2. Apply filters mid-scan<br>3. Observe | Filters apply to validating channels correctly | Medium |
| IT-3.2 | Search during scan | 1. Start scan<br>2. Type search query<br>3. Observe | Search works, scan continues in background | Medium |
| IT-3.3 | Play during scan | 1. Start scan<br>2. Navigate to player<br>3. Return<br>4. Check scan | Scan continues or pauses appropriately | Medium |
| IT-3.4 | Multiple filters with scan | 1. Apply all filters<br>2. Start scan<br>3. Verify behavior | Scans only filtered channels or all channels | Medium |

---

## Performance Test Cases

### PT-1: Load Performance

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| PT-1.1 | Cold start time | 1. Force stop app<br>2. Clear from memory<br>3. Launch<br>4. Measure to usable | Loads within 2 seconds (cached) or 5 seconds (network) | High |
| PT-1.2 | Warm start time | 1. Background app<br>2. Relaunch from recent apps<br>3. Measure | Loads within 500ms | Medium |
| PT-1.3 | Channel list render time | 1. Load 5000 channels<br>2. Measure render time | Renders within 1 second | High |
| PT-1.4 | Filter application time | 1. Apply complex filter<br>2. Measure update time | Updates within 200ms | High |
| PT-1.5 | Search performance | 1. Type search on 5000 channels<br>2. Measure per-keystroke time | Updates within 100ms per keystroke | High |

### PT-2: Memory Performance

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| PT-2.1 | Base memory usage | 1. Launch app<br>2. Measure memory | Uses <150MB on average device | Medium |
| PT-2.2 | Memory with 5000 channels | 1. Load 5000 channels<br>2. Measure memory | Uses <200MB | Medium |
| PT-2.3 | Video playback memory | 1. Play video for 10 minutes<br>2. Monitor memory | Memory stable, no leaks | High |
| PT-2.4 | Memory after 50 channel switches | 1. Play 50 channels<br>2. Measure memory | Memory returns to baseline, no accumulation | High |
| PT-2.5 | Logo cache memory | 1. Scroll through 1000 channels<br>2. Monitor memory | Image cache doesn't exceed reasonable limit | Medium |

### PT-3: Network Performance

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| PT-3.1 | Initial fetch bandwidth | 1. Fresh install<br>2. Measure data downloaded | Downloads <5MB for channel list | Medium |
| PT-3.2 | Background sync bandwidth | 1. Trigger background sync<br>2. Measure data | Only downloads changes, not full list | Low |
| PT-3.3 | Logo loading optimization | 1. Scroll channel list<br>2. Monitor requests | Loads logos on-demand, cancels off-screen | Medium |
| PT-3.4 | Validation network efficiency | 1. Validate 1000 channels<br>2. Monitor requests | Uses HEAD requests (minimal data) | Medium |
| PT-3.5 | Concurrent request limit | 1. Validate channels<br>2. Monitor connections | Respects 5 concurrent limit | Low |

### PT-4: Battery Performance

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| PT-4.1 | Idle battery usage | 1. Open app<br>2. Leave idle for 30 min<br>3. Measure battery | Minimal battery drain when idle | Medium |
| PT-4.2 | Validation battery impact | 1. Run full validation<br>2. Measure battery drain | Reasonable drain during network-intensive task | Low |
| PT-4.3 | Video playback battery | 1. Play video for 1 hour<br>2. Measure battery | Battery drain comparable to other video apps | Medium |
| PT-4.4 | Background sync battery | 1. Background app<br>2. Monitor battery with periodic sync | Minimal background battery usage | Low |

### PT-5: Rendering Performance

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| PT-5.1 | Scroll frame rate | 1. Scroll through 5000 channels<br>2. Measure fps | Maintains 60fps consistently | High |
| PT-5.2 | Filter animation smoothness | 1. Apply/remove filters<br>2. Check animations | Smooth transitions at 60fps | Medium |
| PT-5.3 | Video playback frame rate | 1. Play various streams<br>2. Monitor fps | Maintains source frame rate (30/60fps) | High |
| PT-5.4 | UI overdraw | 1. Enable overdraw debugging<br>2. Check screens | Minimal overdraw (mostly 1-2x) | Low |

---

## Security Test Cases

### SEC-1: Data Security

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| SEC-1.1 | HTTPS for M3U fetching | 1. Monitor network requests<br>2. Verify protocol | Uses HTTPS for M3U repository URLs | High |
| SEC-1.2 | Certificate validation | 1. Test with invalid cert<br>2. Observe behavior | Rejects invalid SSL certificates | Medium |
| SEC-1.3 | Local storage security | 1. Check SharedPreferences<br>2. Verify encryption | Cache stored securely (encrypted if sensitive) | Medium |
| SEC-1.4 | URL injection prevention | 1. Try malicious URL in stream<br>2. Verify handling | Validates/sanitizes URLs, prevents injection | High |
| SEC-1.5 | Intent data validation | 1. Send malicious intent to app<br>2. Verify handling | Validates intent data, no arbitrary code execution | Medium |

### SEC-2: Permission Security

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| SEC-2.1 | Minimum permissions | 1. Check AndroidManifest.xml<br>2. Verify permissions | Only requests necessary permissions (Internet) | High |
| SEC-2.2 | Permission explanation | 1. Check if runtime permissions needed<br>2. Verify explanation | Explains why permissions needed (if any) | Medium |
| SEC-2.3 | External storage access | 1. Check file access<br>2. Verify scope | Uses scoped storage, no broad external storage access | Medium |

### SEC-3: Content Security

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| SEC-3.1 | XSS prevention in channel names | 1. Load channel with script tags in name<br>2. Verify display | Escapes/sanitizes HTML/script content | Medium |
| SEC-3.2 | Path traversal prevention | 1. Try path traversal in URLs<br>2. Verify handling | Prevents directory traversal attacks | Medium |
| SEC-3.3 | Deep link validation | 1. Send malicious deep link<br>2. Verify handling | Validates deep link parameters | Low |

---

## Regression Test Cases

### REG-1: Core Feature Regression

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| REG-1.1 | Channel list loading | Verify channels load after updates | Channels load successfully | High |
| REG-1.2 | TV/Radio filtering | Apply media type filters | Filters work correctly | High |
| REG-1.3 | Category filtering | Apply category filter | Filters work correctly | High |
| REG-1.4 | Country filtering | Apply country filter | Filters work correctly | High |
| REG-1.5 | Search functionality | Search for channels | Search works correctly | High |
| REG-1.6 | Video playback | Play various channels | Videos play successfully | High |
| REG-1.7 | External player | Open in VLC/MX Player | External players launch correctly | High |
| REG-1.8 | Validation scanning | Complete full scan | Scan completes, statuses update | High |

### REG-2: Bug Fix Verification

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| REG-2.1 | Previous crash scenarios | Test scenarios that previously crashed | No crashes occur | High |
| REG-2.2 | Fixed UI issues | Verify previously broken UI | UI displays correctly | Medium |
| REG-2.3 | Fixed data issues | Test previously corrupted data scenarios | Data handles correctly | Medium |
| REG-2.4 | Performance improvements | Compare performance to previous version | Performance improved or maintained | Medium |

### REG-3: Cross-Version Compatibility

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| REG-3.1 | Old cache format | Load app with old version cache | Migrates or clears cache correctly | High |
| REG-3.2 | Settings migration | Upgrade with old settings | Settings migrate correctly | Medium |
| REG-3.3 | Validation data migration | Upgrade with old validation results | Validation data migrates correctly | Medium |

---

## Test Execution Strategy

### Priority Levels
- **High:** Critical functionality, must pass before release
- **Medium:** Important but not blocking, should pass before release
- **Low:** Nice to have, can be deferred if necessary

### Test Phases

#### Phase 1: Smoke Testing (High Priority Only)
- Core channel loading
- Basic filtering
- Video playback
- Critical error scenarios

#### Phase 2: Functional Testing (High + Medium Priority)
- All feature functionality
- Most edge cases
- Common error scenarios
- Basic UI/UX validation

#### Phase 3: Comprehensive Testing (All Priorities)
- All edge cases
- All error scenarios
- Performance testing
- Security testing
- Accessibility testing

### Environment Setup
1. Install Flutter SDK 3.0.0+
2. Set up Android emulators (various API levels and screen sizes)
3. Configure network conditions simulator
4. Set up test devices (physical devices for final validation)

### Test Data Preparation
1. Live M3U repositories (default)
2. Backup M3U files for offline testing
3. Mock M3U with edge cases (empty, malformed, large, etc.)
4. Network simulation profiles (fast, slow, offline)

### Reporting
- Use JIRA/GitHub Issues for bug tracking
- Severity levels: Critical, High, Medium, Low
- Include: Steps to reproduce, expected vs actual, screenshots/videos
- Tag with affected features and versions

### Exit Criteria
- All High priority tests pass
- 95%+ Medium priority tests pass
- No Critical or High severity bugs open
- Performance benchmarks met
- Security audit passed

---

## Automation Recommendations

### Unit Tests (Target: 80% coverage)
```dart
// Test file structure
test/
  models/
    channel_test.dart         // Channel model methods
  services/
    m3u_service_test.dart    // M3U parsing and fetching
  providers/
    channel_provider_test.dart // State management logic
```

**Key Unit Tests:**
- Channel.fromM3ULine() parsing
- Channel.normalizeCategory()
- Channel.extractResolution()
- M3UService.parseM3U()
- ChannelProvider.applyFilters()
- ChannelProvider.setSearchQuery()

### Widget Tests
```dart
test/
  widgets/
    channel_list_item_test.dart    // Channel tile rendering
    filter_dropdown_test.dart      // Dropdown behavior
    search_bar_test.dart          // Search input
```

**Key Widget Tests:**
- Channel list item displays correct data
- Filter dropdowns populate correctly
- Search bar updates on input
- Empty states display correctly
- Loading indicators show/hide correctly

### Integration Tests
```dart
integration_test/
  app_test.dart                    // Complete user flows
  filtering_test.dart             // Filter combinations
  playback_test.dart              // Video playback flow
  validation_test.dart            // Scan flow
```

**Key Integration Tests:**
- FC-1.1 through FC-1.6 (Channel list display)
- FC-6.1 through FC-6.6 (Combined filters)
- IT-1.1 through IT-1.5 (End-to-end flows)
- PT-1.1 through PT-1.5 (Performance benchmarks)

### Automated Testing Tools
- **Flutter Test:** Unit and widget tests
- **Integration Test:** Full app testing
- **Mockito:** Mocking network and services
- **Golden Toolkit:** Visual regression testing
- **patrol:** Enhanced integration testing

### CI/CD Integration
```yaml
# .github/workflows/test.yml
on: [push, pull_request]
jobs:
  test:
    - Run flutter analyze
    - Run flutter test
    - Run integration tests on emulator
    - Generate coverage report
    - Run performance benchmarks
```

---

## Appendix

### Test Environment Specifications

**Minimum Test Device:**
- Android 5.0 (API 21)
- 2GB RAM
- 16GB Storage
- 720x1280 screen

**Recommended Test Device:**
- Android 10+ (API 29+)
- 4GB RAM
- 64GB Storage
- 1080x2340 screen

**Network Profiles:**
- WiFi: 50+ Mbps
- 4G: 10-20 Mbps, 50ms latency
- 3G: 1-5 Mbps, 100ms latency
- 2G: <500 Kbps, 300ms latency
- Offline: No connectivity

### Test Data Sets

**Small Dataset:** 50 channels
- 25 TV, 25 Radio
- 5 categories
- 10 countries
- Purpose: Quick functional testing

**Medium Dataset:** 500 channels
- 300 TV, 200 Radio
- 20 categories
- 50 countries
- Purpose: Standard testing

**Large Dataset:** 5000+ channels
- Live production data
- Purpose: Performance and stress testing

**Edge Case Dataset:** Custom channels with:
- Very long names (200+ chars)
- Missing metadata
- Special characters
- Duplicate URLs
- Various resolutions/bitrates

### Bug Severity Definitions

**Critical:**
- App crashes on launch
- Unable to load channels
- Cannot play any videos
- Data loss or corruption
- Security vulnerabilities

**High:**
- Major features not working (filtering, search, scan)
- Crashes in specific scenarios
- Performance severely degraded
- UI completely broken

**Medium:**
- Minor feature issues
- UI glitches
- Performance moderately affected
- Workarounds available

**Low:**
- Cosmetic issues
- Minor inconsistencies
- Edge cases with minimal impact
- Enhancement requests

### Contact Information

**QA Team Lead:** [Name]  
**Email:** [email]  
**Project Manager:** [Name]  
**Development Lead:** [Name]

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**Next Review:** After each major release

# Visual Test Checklist - UI Improvements

Quick visual inspection checklist for QA testers.

---

## 📱 Home Screen Tests

### Widget Display
- [ ] All channels show in list
- [ ] Channel tiles have quality badges (HD/SD/4K/FHD)
- [ ] Quality badges are color-coded (not raw resolution text)
- [ ] Favorite heart icons display
- [ ] Status indicators show (green check / red X)
- [ ] Channel logos display (or TV/radio icon fallback)

### Search & Filters
- [ ] Search bar at top
- [ ] Search works in real-time
- [ ] Clear (X) button appears when typing
- [ ] Filter dropdowns display:
  - [ ] Type (TV/Radio)
  - [ ] Category
  - [ ] Country
  - [ ] Language
- [ ] Filters apply immediately
- [ ] Stats bar shows: "X channels" and "Y favorites"

### Clear Filters Button
- [ ] **Hidden when no filters active** ⚠️ Important
- [ ] Shows when search text entered
- [ ] Shows when any filter selected
- [ ] Shows "Clear Filters" text with clear icon
- [ ] Full-width button
- [ ] Clicking clears:
  - [ ] Search text
  - [ ] All filter dropdowns
  - [ ] Button disappears after clearing

### Scan Progress
- [ ] Progress bar appears during scan
- [ ] Shows "Scanning: X/Y"
- [ ] Shows working count (✓)
- [ ] Shows failed count (✗)
- [ ] Animated progress bar
- [ ] Scan button changes to Stop button during scan

---

## 🎬 Player Screen Tests

### LIVE Badge
- [ ] **Red LIVE badge visible** ⚠️ Important
- [ ] Positioned next to channel name (top left area)
- [ ] Has white circular dot indicator
- [ ] Has "LIVE" text in white
- [ ] **Pulsing animation** (fades in/out)
- [ ] Visible even when controls are shown

### Volume Slider
- [ ] **Volume slider in bottom control bar** ⚠️ Important
- [ ] Volume icon changes:
  - [ ] 🔇 Mute icon at 0%
  - [ ] 🔉 Low volume icon at 1-49%
  - [ ] 🔊 High volume icon at 50-100%
- [ ] Slider is draggable
- [ ] Percentage displays (0% to 100%)
- [ ] Video volume changes with slider
- [ ] White slider on dark background
- [ ] Positioned above "Tap to hide controls" text

### Quality Badge
- [ ] **Quality badge next to channel name** ⚠️ Important
- [ ] Badge shows quality level:
  - [ ] "4K" in purple (for 2160p+)
  - [ ] "FHD" in blue (for 1080p)
  - [ ] "HD" in green (for 720p)
  - [ ] "SD" in orange (for <720p)
- [ ] No raw resolution text (e.g., not "1920x1080")
- [ ] Badge updates if resolution detected during playback

### Controls
- [ ] Top bar has:
  - [ ] Back button (←)
  - [ ] Channel name
  - [ ] LIVE badge
  - [ ] Quality badge
  - [ ] Bitrate (if available)
  - [ ] PiP button (if supported)
  - [ ] Cast button
  - [ ] External player button
- [ ] Bottom bar has:
  - [ ] Volume slider
  - [ ] Volume icon
  - [ ] Volume percentage
  - [ ] Info text
- [ ] Controls auto-hide after 3 seconds
- [ ] Tap to toggle controls
- [ ] Double-tap to play/pause

### Video Playback
- [ ] Video loads and plays
- [ ] Proper aspect ratio
- [ ] Play/pause button appears when controls shown
- [ ] Loading spinner during buffering
- [ ] Error screen if stream fails
- [ ] Retry button on error
- [ ] External player button on error

---

## 🎨 Visual Quality Checks

### Colors & Contrast
- [ ] Quality badges have distinct colors
- [ ] Text readable on all backgrounds
- [ ] Icons clearly visible
- [ ] Good contrast ratios

### Animations
- [ ] LIVE badge pulses smoothly
- [ ] Volume slider moves smoothly
- [ ] Controls fade in/out smoothly
- [ ] No jank or stuttering
- [ ] Scan progress animates

### Spacing & Layout
- [ ] Proper padding around elements
- [ ] Consistent spacing between items
- [ ] No overlapping elements
- [ ] Responsive to different screen sizes
- [ ] Safe area handling (notches, etc.)

### Icons & Typography
- [ ] All icons display correctly
- [ ] Text is legible
- [ ] Font sizes appropriate
- [ ] Icon sizes consistent
- [ ] Proper use of bold/normal weights

---

## 🔄 Interaction Tests

### Home Screen Interactions
| Action | Expected Result | Pass/Fail |
|--------|----------------|-----------|
| Tap channel | Opens player | [ ] |
| Tap favorite | Toggles heart icon | [ ] |
| Type in search | Filters channels | [ ] |
| Clear search | Clears text & resets | [ ] |
| Select filter | Filters channels | [ ] |
| Apply multiple filters | All filters work together | [ ] |
| Tap Clear Filters | Clears all + hides button | [ ] |
| Tap Scan | Starts validation | [ ] |
| Tap Stop | Stops scanning | [ ] |

### Player Screen Interactions
| Action | Expected Result | Pass/Fail |
|--------|----------------|-----------|
| Tap screen | Toggles controls | [ ] |
| Double-tap | Play/pause | [ ] |
| Drag volume slider | Changes volume | [ ] |
| Tap volume icon | (Visual only, no action) | [ ] |
| Wait 3 seconds | Controls auto-hide | [ ] |
| Tap back | Returns to home | [ ] |
| Tap PiP | Enters PiP mode | [ ] |
| Tap Cast | Shows cast dialog | [ ] |
| Tap External | Opens external player | [ ] |

---

## 🐛 Edge Cases to Test

### Clear Filters Button Edge Cases
- [ ] No filters applied → Button hidden ✓
- [ ] Only search text → Button shows ✓
- [ ] Only one filter → Button shows ✓
- [ ] Multiple filters → Button shows ✓
- [ ] Clear while typing → Search clears immediately ✓
- [ ] Button disappears after clearing ✓

### Quality Badge Edge Cases
- [ ] No resolution data → No badge
- [ ] Invalid resolution → No badge
- [ ] Very high resolution (8K) → Shows 4K
- [ ] Very low resolution (360p) → Shows SD
- [ ] Resolution changes during playback → Badge updates

### Volume Slider Edge Cases
- [ ] Set to 0% → Mute icon, no sound
- [ ] Set to 1% → Low icon, quiet sound
- [ ] Set to 50% → High icon, medium sound
- [ ] Set to 100% → High icon, full sound
- [ ] Drag rapidly → Smooth updates

### LIVE Badge Edge Cases
- [ ] Video loading → Badge visible
- [ ] Video playing → Badge animates
- [ ] Video paused → Badge still visible
- [ ] Controls hidden → Badge visible
- [ ] Error state → Badge visible

---

## 📋 Regression Tests

### Ensure Nothing Broke
- [ ] Channel list loads
- [ ] Favorites work
- [ ] Filters work
- [ ] Search works
- [ ] Scan works
- [ ] Video playback works
- [ ] App navigation works
- [ ] Settings accessible
- [ ] Help screen accessible
- [ ] Diagnostics screen accessible

---

## 🎯 Critical Test Points

### Must Verify (High Priority)

1. **Clear Filters Button Logic**
   - ⚠️ MUST be hidden when no filters active
   - ⚠️ MUST clear all filters when clicked
   - ⚠️ MUST disappear after clearing

2. **Quality Badges**
   - ⚠️ MUST show badges instead of raw resolution
   - ⚠️ MUST use correct colors
   - ⚠️ MUST appear in channel list AND player

3. **Volume Slider**
   - ⚠️ MUST be visible in player
   - ⚠️ MUST control video volume
   - ⚠️ MUST show percentage

4. **LIVE Badge**
   - ⚠️ MUST be visible in player
   - ⚠️ MUST animate (pulse)
   - ⚠️ MUST be red with white text

---

## ✅ Test Sign-Off

**Tester Name:** _______________________  
**Date:** _______________________  
**Build Version:** 1.5.0  

### Results
- [ ] All critical tests passed
- [ ] All visual tests passed
- [ ] All interaction tests passed
- [ ] All edge cases tested
- [ ] No regressions found

### Issues Found
1. _______________________
2. _______________________
3. _______________________

### Approval
- [ ] ✅ APPROVED - Ready for production
- [ ] ⚠️ APPROVED WITH NOTES - Minor issues documented
- [ ] ❌ REJECTED - Major issues must be fixed

**Signature:** _______________________


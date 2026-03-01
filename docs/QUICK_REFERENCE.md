# TV Viewer v1.9.0 → v1.10.0 - Quick Reference Card

**Rating Goal:** 3.5★ → 4.0★+  
**Implementation Time:** 10 hours (1 week sprint)  
**Risk:** Low (UI-only, no business logic changes)  

---

## 🎯 The Problem (User Feedback)

> "Didn't realize favorites are accessible via Category filter dropdown"  
> "Filter UI has 4 dropdowns which feels overwhelming"

---

## 💡 The Solution (4 Quick Wins)

| # | Change | Files | Hours | Impact |
|---|--------|-------|-------|--------|
| **QW-1** | Add favorites button | `home_screen.dart`, `channel_provider.dart` | 3h | ⭐⭐⭐⭐⭐ |
| **QW-2** | Collapsible filters | `home_screen.dart` | 4h | ⭐⭐⭐⭐ |
| **QW-3** | Interactive stats bar | `home_screen.dart` | 2h | ⭐⭐⭐ |
| **QW-4** | Onboarding tooltip | `home_screen.dart`, `onboarding_service.dart` | 1h | ⭐⭐⭐ |

---

## 📐 Visual Changes (Before → After)

### Before (v1.9.0)
```
┌─────────────────────────────────────────┐
│ 📺 TV Viewer               🔄 ⋮        │
├─────────────────────────────────────────┤
│ 🔍 Search...                       ✕   │
├─────────────────────────────────────────┤
│ [Type▼] [Category▼] [Country▼]         │ <- 4 dropdowns
│ [Language▼]                             │    (favorites hidden)
├─────────────────────────────────────────┤
│ 520 ch     ❤️ 12     ✅ 156 working    │ <- heart not tappable
└─────────────────────────────────────────┘
```

### After (v1.10.0)
```
┌─────────────────────────────────────────┐
│ 📺 TV Viewer               🔄 ⋮        │
├─────────────────────────────────────────┤
│ 🔍 Search...                       ✕   │
├─────────────────────────────────────────┤
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│ ┃ ❤️ My Favorites (12)          ✓ ┃  │ <- NEW: Prominent
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
├─────────────────────────────────────────┤
│ [Type▼]     [Category▼]                │ <- 2 visible
│       🔽 More Filters (2) 🔽            │ <- collapsible
├─────────────────────────────────────────┤
│ 520 ch    [❤️ 12]    ✅ 156 working   │ <- tappable
└─────────────────────────────────────────┘
```

---

## 🛠️ Implementation Checklist

### QW-1: Favorites Button (3 hours)
```dart
// 1. Add GlobalKey (line ~26)
final GlobalKey _favoritesButtonKey = GlobalKey();

// 2. Create button widget (new method)
Widget _buildFavoritesButton() { ... }

// 3. Add to Column after search (line ~276)
_buildFavoritesButton(),

// 4. Remove "Favorites" from dropdown
// In channel_provider.dart line 36:
List<String> get categories => ['All', ..._categories.toList()..sort()];

// 5. Add onboarding tooltip case
case 'favorites_button': ...
```

**Test:**
- [ ] Button appears below search
- [ ] Shows count: "Show Favorites (12)"
- [ ] Tap toggles to "My Favorites (12)" with blue background
- [ ] Tap again returns to all channels
- [ ] Works with 0 favorites

---

### QW-2: Collapsible Filters (4 hours)
```dart
// 1. Create new widget at bottom of home_screen.dart
class _FilterSection extends StatefulWidget { ... }

// 2. Replace old filter UI in Column
// REMOVE lines ~278-367 (old 4-dropdown layout)
// ADD:
const _FilterSection(),

// 3. Widget structure:
// - Row: Type + Category (always visible)
// - Toggle button: "More Filters" / "Hide Filters"
// - AnimatedSize: Country + Language (collapsible)
// - Badge: Shows active filter count when collapsed
```

**Test:**
- [ ] Default shows 2 dropdowns
- [ ] "More Filters" expands smoothly (300ms)
- [ ] Badge shows "2" when Country+Language active and collapsed
- [ ] "Hide Filters" collapses back
- [ ] Clear button works

---

### QW-3: Interactive Stats (2 hours)
```dart
// Replace stats bar Consumer (line ~370-407)
// Wrap favorites count in InkWell:
InkWell(
  onTap: () {
    provider.setCategory(
      isShowingFavorites ? 'All' : 'Favorites'
    );
  },
  child: Container(
    decoration: isShowingFavorites ? BoxDecoration(...) : null,
    child: Row([Icon(...), Text(...)]),
  ),
)
```

**Test:**
- [ ] Tap heart toggles favorites filter
- [ ] Active shows red background + border
- [ ] Icon changes: outline ↔ filled
- [ ] Bold text when active

---

### QW-4: Onboarding (1 hour - included in QW-1)
```dart
// In onboarding_service.dart:
static const List<String> _allTooltips = [
  'scan_button',
  'favorites_button',  // ADD THIS
  'filter_area',
];

// In home_screen.dart _showNextTooltip():
case 'favorites_button':
  targetKey = _favoritesButtonKey;
  message = 'Tap here to quickly view all your favorite channels';
  position = ArrowPosition.top;
  break;
```

**Test:**
- [ ] Fresh install shows tooltips in order
- [ ] Favorites tooltip appears after scan tooltip
- [ ] Dismissing works correctly

---

## 📱 Files to Modify

```
flutter_app/lib/
├── screens/
│   └── home_screen.dart          <- Main changes (all 4 QWs)
├── providers/
│   └── channel_provider.dart     <- Remove "Favorites" from dropdown
└── services/
    └── onboarding_service.dart   <- Add favorites tooltip
```

---

## 🧪 Testing Matrix

| Scenario | Expected Result |
|----------|----------------|
| **Fresh install** | Onboarding tooltips appear in sequence |
| **0 favorites** | Button shows "Show Favorites", still tappable |
| **Add first favorite** | Count updates everywhere (button + stats) |
| **Tap favorites button** | Filters to show only favorites |
| **Tap stats heart** | Same as button (toggles filter) |
| **Expand filters** | Smooth animation, shows Country + Language |
| **Active advanced filters** | Badge shows count when collapsed |
| **Clear filters** | All dropdowns reset, button/stats update |
| **Small screen (360px)** | No layout issues, text doesn't truncate |
| **Tablet (768px)** | Extra space used well, not stretched weird |

---

## 📊 Success Metrics (Track These)

```dart
// Add analytics events:
AnalyticsService.logEvent('favorites_button_tapped');
AnalyticsService.logEvent('favorites_via_stats_tapped');
AnalyticsService.logEvent('advanced_filters_expanded');
AnalyticsService.logEvent('first_favorite_added', {
  'time_since_install_seconds': duration.inSeconds,
  'discovery_method': 'button|dropdown|stats',
});
```

**Goals Week 1:**
- App Store rating: ≥3.8★ (up from 3.5★)
- Favorites discovery: ≥60% of new users
- Filter expansion: ≥40% of users (baseline TBD)

**Goals Week 4:**
- App Store rating: ≥4.0★
- Favorites engagement: ≥50% of users have favorites
- Retention: +5-10% return rate

---

## 🚨 Rollback Plan

If critical issues or ratings drop:

### Option 1: Full Rollback
- Revert to v1.9.0 via Play Console
- Halt staged rollout

### Option 2: Partial Rollback (Feature Flags)
```dart
class FeatureFlags {
  static const bool enableNewFavoritesButton = true;  // Can disable
  static const bool enableCollapsibleFilters = true;  // Can disable
  static const bool enableInteractiveStats = true;    // Can disable
}

// Wrap features:
if (FeatureFlags.enableNewFavoritesButton) {
  _buildFavoritesButton(),
}
```

### Option 3: A/B Test
- 50% get new UI
- 50% get old UI
- Compare metrics after 1 week

---

## 🎨 Design Tokens (Use These)

```dart
// Colors
primary: #2196F3           // Blue 500 (favorites active state)
primaryLight: #BBDEFB      // Blue 100 (background)
error: #EF5350             // Red 400 (favorites icon)
errorLight: #FFEBEE        // Red 50 (stats background)

// Spacing
buttonPadding: 8.0         // Outer padding
contentPadding: 16.0, 12.0 // Inner padding (h, v)
filterGap: 8.0             // Between dropdowns
sectionGap: 12.0           // Between sections

// Border
default: 1.0px #E0E0E0     // Inactive
active: 2.0px #2196F3      // Active
radius: 12.0px             // Rounded corners

// Typography
defaultSize: 15.0          // Button text
defaultWeight: 500         // Regular
activeWeight: 600          // Bold
hintSize: 13.0             // Dropdowns
badgeSize: 11.0            // Filter count
```

---

## 🐛 Common Issues & Fixes

### Issue: Button not updating on favorite add/remove
**Fix:** Ensure `notifyListeners()` called in `toggleFavorite()`

### Issue: Animation janky on low-end devices
**Fix:** Reduce duration: 300ms → 200ms or use `Fade` instead of `AnimatedSize`

### Issue: Stats bar tap area too small
**Fix:** Increase padding to meet 48dp touch target:
```dart
padding: EdgeInsets.symmetric(horizontal: 12, vertical: 12)
```

### Issue: Badge not showing correct count
**Fix:** Ensure logic counts both Country AND Language:
```dart
final count = (provider.selectedCountry != 'All' ? 1 : 0) + 
              (provider.selectedLanguage != 'All' ? 1 : 0);
```

### Issue: Onboarding tooltip appears off-screen
**Fix:** Ensure GlobalKey is on rendered widget:
```dart
key: _favoritesButtonKey,  // On outermost Padding, not InkWell
```

---

## 📞 Support

**Implementation Questions:** dev-team@tvviewer.app  
**UX Questions:** ux@tvviewer.app  
**Bug Reports:** GitHub Issues  

---

## 📚 Full Documentation

- **Executive Summary:** `UX_REVIEW_SUMMARY.md` (2 pages)
- **Full UX Review:** `UX_REVIEW_v1.9.0_FLUTTER.md` (35 pages)
- **Implementation Guide:** `QUICK_WINS_IMPLEMENTATION.md` (26 pages)
- **Visual Mockups:** `VISUAL_MOCKUPS.md` (26 pages)

---

## ✅ Pre-Commit Checklist

- [ ] All 4 Quick Wins implemented
- [ ] No compilation errors
- [ ] Manual testing completed (10+ scenarios)
- [ ] Analytics events added
- [ ] Help screen updated (optional for v1.0)
- [ ] Changelog updated
- [ ] Release notes prepared
- [ ] Code reviewed by peer
- [ ] APK tested on 3+ devices

---

**Version:** 1.0  
**Date:** January 2025  
**Estimated Time:** 10 hours  
**Estimated Impact:** +0.5 stars (3.5★ → 4.0★)

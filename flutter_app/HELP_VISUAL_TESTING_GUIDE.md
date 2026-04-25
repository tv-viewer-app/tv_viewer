# 📱 Help System & Onboarding - Visual Testing Guide

## 🎯 What to Expect

This guide shows you exactly what you'll see when testing the new help system and onboarding features.

---

## 🚀 First Launch Experience (Onboarding)

### Step 1: App Opens
```
┌─────────────────────────────┐
│     📺 TV Viewer       [⋮]  │ ← Menu icon added
├─────────────────────────────┤
│  [Type ▼] [Category ▼]      │
│  [Country ▼] [Language ▼]   │
├─────────────────────────────┤
│  🔍 Search channels...      │
├─────────────────────────────┤
│                             │
│  Loading channels...        │
│                             │
└─────────────────────────────┘
```

### Step 2: First Tooltip Appears (800ms delay)
```
┌─────────────────────────────┐
│     📺 TV Viewer    ↻  [⋮]  │ ← Scan button
├─────────────────────────────┤
│                             │
│  ┌─────────────────────┐   │
│  │ Tap to check which  │   │ ← Tooltip with message
│  │ channels are working│   │
│  │                     │   │
│  │    [Got it]         │   │ ← Dismiss button
│  └─────────▲───────────┘   │
│            │                │ ← Arrow pointing up
│                             │
└─────────────────────────────┘
```

**What happens:**
- Semi-transparent black backdrop (50% opacity)
- White rounded tooltip box
- Arrow pointing to scan button
- "Got it" button to dismiss
- Smooth fade + scale animation (300ms)

### Step 3: Second Tooltip (500ms after dismissing first)
```
┌─────────────────────────────┐
│     📺 TV Viewer    ↻  [⋮]  │
├─────────────────────────────┤
│  ┌─────────────────────┐   │
│  │ Filter by category, │   │ ← Tooltip message
│  │ country, or type    │   │
│  │                     │   │
│  │    [Got it]         │   │ ← Dismiss button
│  └─────────▼───────────┘   │
│            │                │ ← Arrow pointing down
│  [Type ▼] [Category ▼]     │ ← Filter dropdowns
│  [Country ▼] [Language ▼]  │
└─────────────────────────────┘
```

**What happens:**
- First tooltip disappears
- 500ms delay
- Second tooltip appears
- Points to filter area
- Same animation style

### Step 4: Onboarding Complete
```
┌─────────────────────────────┐
│     📺 TV Viewer    ↻  [⋮]  │
├─────────────────────────────┤
│  [Type ▼] [Category ▼]      │
│  [Country ▼] [Language ▼]   │
├─────────────────────────────┤
│  🔍 Search channels...      │
├─────────────────────────────┤
│  📊 5,234 channels          │
│  ❤️  12 favorites           │
│  ✅ 3,421 working           │
├─────────────────────────────┤
│  🎬 ESPN HD                 │
│  🌐 News • 1080p • USA      │
│                         ♡   │
└─────────────────────────────┘
```

**What happens:**
- Normal app view restored
- No more tooltips
- State saved to SharedPreferences
- Won't show again on next launch

---

## 📋 Menu Testing

### Opening the Menu
```
Tap here ──────────┐
                   │
┌──────────────────▼──────────┐
│     📺 TV Viewer    ↻  [⋮]  │ ← Three-dot menu
└─────────────────────────────┘
```

### Menu Opened
```
┌─────────────────────────────┐
│     📺 TV Viewer    ↻  [⋮]  │
│                        │    │
│                    ┌───┴────────────┐
│                    │ ? Help & Supp… │ ← New!
│                    ├────────────────┤
│                    │ 🐛 Diagnostics │
│                    │ 💬 Send Feed…  │
│                    │ ⭐ Rate App    │
│                    ├────────────────┤
│                    │ ℹ️  About       │
│                    └────────────────┘
└─────────────────────────────┘
```

**Menu Items:**
1. **Help & Support** (NEW) - Opens help screen
2. **Diagnostics** - Opens diagnostics screen
3. **Send Feedback** - Opens feedback dialog
4. **Rate App** - Opens app store
5. **About** - Shows about dialog

---

## 🆘 Help Screen

### Main Help Screen
```
┌─────────────────────────────┐
│  ← Help & Support           │
├─────────────────────────────┤
│                             │
│  ❓ Frequently Asked Q…     │ ← Section header
│                             │
│  ┌─────────────────────┐   │
│  │ How do I add chann… │ ▶ │ ← Collapsed FAQ
│  └─────────────────────┘   │
│                             │
│  ┌─────────────────────┐   │
│  │ Why aren't some ch… │ ▶ │
│  └─────────────────────┘   │
│                             │
│  ... 8 more FAQ items ...   │
│                             │
│  🔧 Troubleshooting         │ ← Section header
│                             │
│  🔌 Channels not loading    │ ← Guide
│  Check your internet conne… │
│                             │
│  ▶️ Playback issues          │
│  Try using an external pla… │
│                             │
│  ... 3 more guides ...      │
│                             │
│  📧 Contact Support         │ ← Section header
│                             │
│  ┌─────────────────────┐   │
│  │    Email Support    │   │ ← Button
│  └─────────────────────┘   │
│                             │
│  ℹ️  Version: 1.5.0+1       │ ← Dynamic
│                             │
│  ┌─────────────────────┐   │
│  │    Export Logs      │   │ ← Button
│  └─────────────────────┘   │
│                             │
│  ┌─────────────────────┐   │
│  │  Reset Onboarding   │   │ ← Button
│  └─────────────────────┘   │
│                             │
│  ⚠️  Legal Disclaimer       │
│  This app does not host or │
│  store any streams...       │
└─────────────────────────────┘
```

### FAQ Expanded
```
Tap to expand ────────┐
                      │
┌─────────────────────▼───────┐
│  ┌─────────────────────┐   │
│  │ How do I add chann… │ ▼ │ ← Arrow rotated
│  │                     │   │
│  │ Channels are autom… │   │ ← Answer visible
│  │ loaded from public… │   │
│  │ repositories. You…  │   │
│  │ don't need to man…  │   │
│  │                     │   │
│  └─────────────────────┘   │
│                             │
│  ┌─────────────────────┐   │
│  │ Why aren't some ch… │ ▶ │ ← Still collapsed
│  └─────────────────────┘   │
└─────────────────────────────┘
```

**Interaction:**
- Tap to expand/collapse
- Smooth animation
- Only one expanded at a time (optional)
- Full answer text revealed

---

## 🎬 Animation Details

### Tooltip Entry Animation
```
Time: 0ms          100ms         200ms         300ms
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│         │   │  ▪️      │   │  ◾️      │   │  ◼️      │
│         │   │ (faint) │   │ (50%)   │   │ (full)  │
│ Hidden  │ → │ Scale   │ → │ Scale   │ → │ Visible │
│         │   │  0.8    │   │  0.9    │   │  1.0    │
└─────────┘   └─────────┘   └─────────┘   └─────────┘
```

**Properties:**
- Fade: 0% → 100% opacity
- Scale: 0.8 → 1.0
- Curve: `Curves.easeInOut`
- Duration: 300ms

### Tooltip Exit Animation
```
Time: 0ms          100ms         200ms         300ms
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│  ◼️      │   │  ◾️      │   │  ▪️      │   │         │
│ (full)  │   │ (50%)   │   │ (faint) │   │         │
│ Visible │ → │ Scale   │ → │ Scale   │ → │ Hidden  │
│  1.0    │   │  0.9    │   │  0.8    │   │         │
└─────────┘   └─────────┘   └─────────┘   └─────────┘
```

**Properties:**
- Fade: 100% → 0% opacity
- Scale: 1.0 → 0.8
- Curve: `Curves.easeInOut`
- Duration: 300ms

---

## 🔄 Reset Onboarding Flow

### Step 1: Tap Reset Button
```
┌─────────────────────────────┐
│  ← Help & Support           │
├─────────────────────────────┤
│                             │
│  ┌─────────────────────┐   │
│  │  Reset Onboarding   │ ← │ ← Tap here
│  └─────────────────────┘   │
└─────────────────────────────┘
```

### Step 2: Confirmation Dialog
```
┌─────────────────────────────┐
│    ┌────────────────┐       │
│    │ Reset Onboardi…│       │ ← Dialog title
│    ├────────────────┤       │
│    │ This will show │       │
│    │ the onboarding │       │
│    │ tooltips again │       │
│    │ on next launch.│       │
│    │                │       │
│    │   [Cancel]     │       │
│    │        [Reset] │       │ ← Confirm
│    └────────────────┘       │
└─────────────────────────────┘
```

### Step 3: Success Message
```
┌─────────────────────────────┐
│    ┌────────────────┐       │
│    │ ✅ Onboarding  │       │
│    │    reset!      │       │
│    │                │       │
│    │ Tooltips will  │       │
│    │ appear next    │       │
│    │ time you open  │       │
│    │ the app.       │       │
│    │                │       │
│    │      [OK]      │       │
│    └────────────────┘       │
└─────────────────────────────┘
```

### Step 4: Restart App
```
Close and reopen app
         ↓
┌─────────────────────────────┐
│     📺 TV Viewer    ↻  [⋮]  │
├─────────────────────────────┤
│  ┌─────────────────────┐   │
│  │ Tap to check which  │   │ ← Tooltips back!
│  │ channels are working│   │
│  │                     │   │
│  │    [Got it]         │   │
│  └─────────▲───────────┘   │
└─────────────────────────────┘
```

---

## 📧 Email Support Flow

### Step 1: Tap Email Support
```
┌─────────────────────────────┐
│  📧 Contact Support         │
│                             │
│  ┌─────────────────────┐   │
│  │    Email Support    │ ← │ ← Tap here
│  └─────────────────────┘   │
└─────────────────────────────┘
```

### Step 2: Email Client Opens
```
┌─────────────────────────────┐
│  📧 New Email               │
├─────────────────────────────┤
│  To: github.com/tv-viewer-app/tv_viewer/issues │ ← Pre-filled
│  Subject: TV Viewer Supp…   │ ← Pre-filled
│                             │
│  App Version: 1.5.0+1       │ ← Pre-filled
│                             │
│  Describe your issue:       │ ← Pre-filled
│  [Cursor here]              │ ← User types
│                             │
│                             │
│              [Send]         │
└─────────────────────────────┘
```

---

## 🎨 Color & Styling

### Light Theme
```
Tooltip Background:   #FFFFFF (White)
Text Color:          #000000 (Black)
Button Color:        #0078D4 (Microsoft Blue)
Backdrop:            #000000 @ 50% opacity
Border Radius:       12px
Elevation:           8dp shadow
```

### Dark Theme
```
Tooltip Background:   #1E1E1E (Dark gray)
Text Color:          #FFFFFF (White)
Button Color:        #4A9EFF (Light blue)
Backdrop:            #000000 @ 70% opacity
Border Radius:       12px
Elevation:           8dp shadow
```

---

## ✅ Expected Behavior Checklist

### First Launch
- [ ] App opens normally
- [ ] 800ms delay before first tooltip
- [ ] Tooltip animates in smoothly
- [ ] Backdrop dims screen
- [ ] Arrow points to scan button
- [ ] "Got it" button visible
- [ ] Tap "Got it" dismisses tooltip
- [ ] 500ms delay before second tooltip
- [ ] Second tooltip points to filters
- [ ] Final "Got it" completes onboarding
- [ ] No tooltips on second launch

### Menu
- [ ] Menu icon visible in app bar
- [ ] Tap menu opens popup
- [ ] "Help & Support" first item
- [ ] Divider after help item
- [ ] All menu items have icons
- [ ] Tap "Help & Support" opens help screen
- [ ] Tap outside closes menu

### Help Screen
- [ ] Screen opens from menu
- [ ] Back button returns to home
- [ ] FAQ items collapsed by default
- [ ] Tap FAQ expands it
- [ ] Tap again collapses it
- [ ] Troubleshooting guides readable
- [ ] Email button opens email app
- [ ] App version displays correctly
- [ ] Export logs navigates to diagnostics
- [ ] Reset button shows confirmation
- [ ] Legal disclaimer at bottom

### Reset Onboarding
- [ ] Tap reset shows confirmation
- [ ] Cancel dismisses dialog
- [ ] Reset shows success message
- [ ] Restart app shows tooltips again

---

## 🐛 Common Issues & Solutions

### Tooltips Don't Appear
**Check:**
- SharedPreferences cleared? (Try `adb shell pm clear com.tvviewer.app`)
- 800ms initial delay passed?
- GlobalKeys properly assigned to widgets?

### Menu Not Visible
**Check:**
- App bar actions list
- PopupMenuButton added?
- Build successful?

### Email Doesn't Open
**Check:**
- Email app installed on device?
- url_launcher package installed?
- mailto: URI properly formatted?

### App Version Shows "Loading..."
**Check:**
- package_info_plus package installed?
- Async loading completed?
- Fallback version set?

---

## 📱 Device Testing Matrix

### Screen Sizes
- [ ] Phone (5.5" - 6.5")
- [ ] Tablet (7" - 10")
- [ ] Small phone (< 5.5")
- [ ] Large tablet (> 10")

### Android Versions
- [ ] Android 6 (API 23) - Minimum
- [ ] Android 8 (API 26)
- [ ] Android 10 (API 29)
- [ ] Android 12+ (API 31+) - Latest

### Themes
- [ ] Light theme
- [ ] Dark theme
- [ ] System theme switching

### Orientations
- [ ] Portrait
- [ ] Landscape (tooltips adjust)

---

## 🎯 Success Criteria

**Onboarding**
✅ Tooltips show on first launch only  
✅ Sequential with smooth transitions  
✅ Easy to dismiss  
✅ Non-intrusive design  
✅ State persists correctly  

**Help Screen**
✅ Easy to access from menu  
✅ Comprehensive FAQ content  
✅ Working email integration  
✅ Accurate version display  
✅ Functional reset button  

**Overall**
✅ No crashes or errors  
✅ Smooth animations  
✅ Material3 compliant  
✅ Consistent with app theme  
✅ Great user experience  

---

**Status**: ✅ Ready for Testing  
**Version**: 1.0.0  
**Last Updated**: 2024

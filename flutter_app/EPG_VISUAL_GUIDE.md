# EPG Feature Visual Guide

## 🎨 Visual Overview

This document provides a visual representation of the EPG (Electronic Program Guide) feature implementation.

---

## 📺 Player Screen Integration

### Top Overlay - Compact EPG Display

```
┌─────────────────────────────────────────────────────────────┐
│ [←] 🔴 LIVE  CNN International            720p  2.5 Mbps  [i]│
│     ● NOW: Live Broadcast  14:00-15:00 • 30 min left       │
└─────────────────────────────────────────────────────────────┘
```

**Components:**
- Back button
- LIVE badge (red)
- Channel name
- Quality badge (720p)
- Bitrate display
- **Compact EPG** showing current program
- Info button to toggle full EPG

---

### Full EPG Overlay (When Info Button Pressed)

```
┌─────────────────────────────────────────────────────────────┐
│                                                               │
│                      [VIDEO PLAYING]                          │
│                                                               │
│  ╔════════════════════════════════════════════════════════╗  │
│  ║ 🕐 SCHEDULE                               ⓘ             ║  │
│  ║                                                          ║  │
│  ║  ┌────────────────────────────────────────────────────┐ ║  │
│  ║  │ NOW PLAYING  14:00 - 15:00        1h               │ ║  │
│  ║  │ Live Broadcast                                     │ ║  │
│  ║  │ EPG data not available for this channel            │ ║  │
│  ║  │ ████████████████░░░░░░░░ 75%   30 min remaining   │ ║  │
│  ║  └────────────────────────────────────────────────────┘ ║  │
│  ║                                                          ║  │
│  ║  ┌────────────────────────────────────────────────────┐ ║  │
│  ║  │ NEXT  15:00 - 16:00               1h               │ ║  │
│  ║  │ Scheduled Program                                  │ ║  │
│  ║  │ EPG data not available for this channel            │ ║  │
│  ║  └────────────────────────────────────────────────────┘ ║  │
│  ╚════════════════════════════════════════════════════════╝  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 🔊 ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░ 60%      │ │
│  │ ℹ️ Tap to hide • Double-tap to play/pause              │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Layout:**
- Video background
- EPG overlay card (center-bottom)
- Two program cards: NOW and NEXT
- Progress bar for live content
- Volume controls below

---

## 🎯 EPG Display Variants

### 1. Full EPG Display (EpgDisplay)

#### With Placeholder Data
```
╔══════════════════════════════════════════════════════╗
║ 🕐 SCHEDULE                              ⓘ           ║
║                                                      ║
║  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  ║
║  ┃ NOW PLAYING  13:30 - 14:30            1h       ┃  ║
║  ┃ Live Broadcast                                 ┃  ║
║  ┃ EPG data not available for this channel        ┃  ║
║  ┃ ████████████░░░░░░░░ 60%   24 min remaining   ┃  ║
║  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  ║
║                                                      ║
║  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  ║
║  ┃ NEXT  15:00 - 16:00                   1h       ┃  ║
║  ┃ Scheduled Program                              ┃  ║
║  ┃ EPG data not available for this channel        ┃  ║
║  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  ║
╚══════════════════════════════════════════════════════╝
```

#### With Real EPG Data
```
╔══════════════════════════════════════════════════════╗
║ 🕐 SCHEDULE (green indicator for real data)          ║
║                                                      ║
║  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  ║
║  ┃ NOW PLAYING  18:00 - 19:00            1h       ┃  ║
║  ┃ CNN Newsroom                                   ┃  ║
║  ┃ Breaking news and analysis from around world   ┃  ║
║  ┃ 📁 News                                        ┃  ║
║  ┃ ████████████████░░░░ 80%   12 min remaining   ┃  ║
║  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  ║
║                                                      ║
║  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  ║
║  ┃ NEXT  19:00 - 20:00                   1h       ┃  ║
║  ┃ Anderson Cooper 360                            ┃  ║
║  ┃ In-depth reporting and analysis                ┃  ║
║  ┃ 📁 News                                        ┃  ║
║  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  ║
╚══════════════════════════════════════════════════════╝
```

### 2. Compact EPG Display (CompactEpgDisplay)

#### Placeholder
```
┌────────────────────────────────────────────┐
│ ⚫ NOW: Live Broadcast                     │
│    14:00 - 15:00 • 30 min left             │
└────────────────────────────────────────────┘
```

#### With Data
```
┌────────────────────────────────────────────┐
│ 🟢 NOW: CNN Newsroom                       │
│    18:00 - 19:00 • 12 min left             │
└────────────────────────────────────────────┘
```

---

## 🎨 Color Scheme

### Status Indicators
- 🟢 **Green**: Real EPG data available
- ⚫ **Grey**: Placeholder data (EPG unavailable)

### Program Labels
- 🔴 **Red**: "NOW PLAYING" label and accent
- 🔵 **Blue**: "NEXT" label and accent

### UI Elements
- **Black/Dark**: Background overlays (50% opacity)
- **White**: Text and icons
- **White 70%**: Secondary text (time, bitrate)
- **White 54%**: Tertiary text (hints, info)

---

## 📱 Responsive Layouts

### Mobile Portrait
```
┌─────────────┐
│ [Compact]   │ ← Always visible with controls
│             │
│   [Video]   │
│             │
│             │
│ [Full EPG]  │ ← Shows on info button press
│ (if toggled)│
└─────────────┘
```

### Tablet/Landscape
```
┌────────────────────────────────────────────┐
│ [Compact EPG]                        [Info]│ ← Top bar
│                                            │
│              [Video Player]                │
│                                            │
│        [Full EPG] (if toggled)             │ ← Center-bottom
└────────────────────────────────────────────┘
```

---

## 🔄 State Transitions

### EPG Toggle Flow
```
1. Initial State
   ┌──────────────┐
   │ Compact EPG  │ ← Always visible
   │   visible    │
   └──────────────┘

2. User Presses Info Button
   ┌──────────────┐
   │ Compact EPG  │
   │   visible    │
   ├──────────────┤
   │  Full EPG    │ ← Fades in
   │   appears    │
   └──────────────┘

3. After 10 Seconds (Auto-hide)
   ┌──────────────┐
   │ Compact EPG  │
   │   visible    │ ← Full EPG fades out
   └──────────────┘
```

---

## 🎬 Animation Details

### Show EPG
- **Duration**: 300ms
- **Curve**: easeInOut
- **Effect**: Fade in + scale (0.9 → 1.0)

### Hide EPG
- **Duration**: 300ms
- **Curve**: easeInOut
- **Effect**: Fade out + scale (1.0 → 0.9)

### Progress Bar
- **Update**: Every second
- **Animation**: Smooth linear interpolation
- **Color**: Matches label color (red for NOW)

---

## 📐 Dimensions

### Full EPG Display
- **Width**: Screen width - 32px (16px margin each side)
- **Padding**: 12px all around
- **Border Radius**: 8px
- **Card Spacing**: 8px between NOW and NEXT

### Program Card
- **Padding**: 8px
- **Border**: 1px solid (accent color with 30% opacity)
- **Border Radius**: 6px
- **Background**: White with 5% opacity

### Compact EPG Display
- **Padding**: 8px horizontal, 4px vertical
- **Border Radius**: 4px
- **Background**: Black with 60% opacity

---

## 🔠 Typography

### Headers
- **SCHEDULE**: 11px, bold, uppercase, letter-spacing: 0.5
- **NOW PLAYING / NEXT**: 9px, bold, uppercase, letter-spacing: 0.5

### Content
- **Program Title**: 14px, semi-bold (600)
- **Description**: 12px, regular
- **Time Range**: 11px, regular
- **Duration**: 10px, regular
- **Category**: 11px, regular with icon

### Hints
- **Info Text**: 10-12px, regular, white 54%

---

## 🎯 Accessibility

### Visual Indicators
- ✅ Color coding with icons (not color-only)
- ✅ High contrast text (white on dark)
- ✅ Clear label hierarchy
- ✅ Status tooltips

### Interactive Elements
- ✅ Info button with tooltip
- ✅ Tap to toggle full EPG
- ✅ Auto-hide to prevent obstruction
- ✅ Touch-friendly sizes (44x44 minimum)

---

## 📊 Component Hierarchy

```
PlayerScreen (Video Player)
├── Video Background
├── Top Overlay
│   ├── Back Button
│   ├── Channel Info
│   │   ├── LIVE Badge
│   │   ├── Channel Name
│   │   ├── Quality Badge
│   │   ├── Bitrate
│   │   └── CompactEpgDisplay ← HERE
│   ├── Info Button
│   ├── PiP Button
│   ├── Cast Button
│   └── External Player Button
├── Full EPG Overlay (Conditional)
│   └── EpgDisplay ← HERE
└── Bottom Controls
    ├── Volume Slider
    └── Info Text
```

---

## ✨ Key Features Visualization

### 1. Graceful Degradation
```
┌─────────────────┐     ┌─────────────────┐
│ Real EPG Data   │     │ Placeholder     │
│ Available       │ OR  │ (No Data)       │
├─────────────────┤     ├─────────────────┤
│ CNN Newsroom    │     │ Live Broadcast  │
│ 18:00-19:00     │     │ 14:00-15:00     │
│ Breaking news   │     │ EPG unavailable │
│ 🟢 (green icon) │     │ ⚫ (grey icon)   │
└─────────────────┘     └─────────────────┘
```

### 2. Progress Tracking
```
NOW PLAYING
CNN Newsroom
18:00 - 19:00
████████████████░░░░░░░░ 80%
12 min remaining
```

### 3. Time Formatting
```
Input:  DateTime(2024, 1, 15, 9, 5)
Output: "09:05 - 10:30"
        (with leading zeros)
```

### 4. Duration Formatting
```
90 minutes  → "1h 30min"
120 minutes → "2h"
45 minutes  → "45 min"
```

---

## 🎉 Summary

The EPG feature provides:
- ✨ Beautiful, consistent UI design
- ✨ Clear visual hierarchy
- ✨ Graceful degradation with placeholders
- ✨ Progress tracking for live content
- ✨ Responsive layouts for all screen sizes
- ✨ Smooth animations and transitions
- ✨ High accessibility standards
- ✨ Intuitive user interactions

---

**Status**: ✅ Visual Design Complete  
**Issue**: #20 - Add channel EPG/schedule info (simplified version)  
**Version**: 1.0.0

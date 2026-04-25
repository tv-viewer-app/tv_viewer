# TV Viewer - User Guide

Welcome to TV Viewer, a free and open-source IPTV streaming app for Android. This guide will help you get the most out of the app.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Features Overview](#features-overview)
3. [Common Workflows](#common-workflows)
4. [Tips and Tricks](#tips-and-tricks)
5. [Troubleshooting](#troubleshooting)

---

## Getting Started

### First Launch

When you first open TV Viewer, the app will:

1. **Auto-load channels** from public IPTV repositories
2. **Display tooltips** highlighting key features:
   - Scan button for checking stream availability
   - Filter dropdowns for organizing channels
   - Favorite button for saving channels

### Understanding the Interface

#### Home Screen Layout

- **Search Bar**: Quick text search across all channel names
- **Filter Dropdowns**:
  - **Type**: Filter by TV or Radio
  - **Category**: News, Sports, Entertainment, Movies, etc.
  - **Country**: Filter by broadcasting country
  - **Language**: Filter by audio language
- **Stats Bar**: Shows total channels, favorites count, and working streams
- **Channel List**: Scrollable list with channel info and status indicators

#### Channel Information

Each channel tile displays:
- **Logo**: Channel branding (if available)
- **Name**: Channel title
- **Subtitle**: Category, resolution, bitrate, country
- **Status Indicator**:
  - ✅ **Green checkmark**: Stream is working
  - ❌ **Red X**: Stream failed validation
  - ⚪ **No indicator**: Not yet scanned

---

## Features Overview

### 1. Channel Scanning

**What it does**: Validates whether IPTV streams are currently accessible.

**How to use**:
1. Tap the **Refresh** icon (↻) in the top-right corner
2. Watch the progress bar showing validation status
3. Tap **Stop** anytime to cancel
4. Results update in real-time with green/red indicators

**Note**: Scanning 5000+ channels may take 5-10 minutes.

---

### 2. Filtering Channels

**Multiple filter options**:

- **Search**: Type channel name (e.g., "CNN", "BBC", "Sports")
- **Type**: Show only TV or Radio channels
- **Category**: Focus on News, Sports, Movies, Kids, etc.
- **Country**: Browse channels from specific countries
- **Language**: Filter by audio language

**Combining filters**: All filters work together. For example:
- Type: TV
- Category: Sports
- Country: USA
= Shows only American TV sports channels

**Clear all filters**: Tap "Clear Filters" button to reset.

---

### 3. Favorites

**Save your favorite channels**:

1. Tap the **heart icon** (♡) on any channel
2. Heart turns red (♥) when saved
3. Access favorites using the filter or stats display

**Managing favorites**:
- Tap the heart again to remove from favorites
- Favorites persist across app restarts
- Export favorites using the M3U export feature

---

### 4. Playing Channels

**Built-in Player**:

1. Tap any channel to open the player
2. Video starts automatically if stream is available
3. Player controls:
   - **Play/Pause**: Tap screen center
   - **Rotate**: Auto-rotates to landscape for better viewing
   - **PiP**: Press home button (Android 8.0+) for floating window

**External Players** (Settings menu):

Supported players:
- VLC for Android
- MX Player
- MPV
- Just Player

To enable:
1. Open **Settings** from the menu
2. Toggle "Use External Player"
3. Select your preferred player

---

### 5. Picture-in-Picture (PiP)

**Requirements**: Android 8.0 or higher

**How to activate**:
1. Start playing a channel
2. Press the **Home button** OR tap the PiP icon
3. Video continues in a floating window
4. Resize and position the window as needed

**Controls**:
- Tap window to show play/pause/close
- Drag window to reposition
- Tap "X" or return to app to exit PiP

---

### 6. Exporting Channel Lists

**Create M3U playlists**:

1. Tap the **three-dot menu** (⋮) in top-right
2. Select **"Export Channels"**
3. Choose export options:
   - All channels
   - Favorites only
   - Working channels only
4. M3U file saved to Downloads folder

**Use cases**:
- Backup your channel list
- Share with other devices
- Import into desktop players (VLC, Kodi)

---

## Common Workflows

### Workflow 1: Finding a Specific Channel

1. Open the app
2. Tap the **search bar**
3. Type channel name (e.g., "ESPN")
4. Browse results
5. Tap to play

### Workflow 2: Discovering Sports Channels

1. Tap **Category** dropdown
2. Select "Sports"
3. Optionally filter by **Country**
4. Tap **Scan** to check which are working
5. Save favorites by tapping hearts

### Workflow 3: Setting Up for Daily Use

1. **First time**:
   - Run a full scan (takes 5-10 min)
   - Browse and add 10-20 favorites
2. **Daily**:
   - Open app → Tap heart filter to see favorites
   - Tap channel to watch
   - Use PiP for multitasking

### Workflow 4: Troubleshooting a Stream

1. If video won't play:
   - Check if channel has green checkmark
   - Try running a scan
2. If still fails:
   - Enable external player in settings
   - Try playing in VLC or MX Player
3. If buffering:
   - Check your internet speed
   - Try a different channel or time

---

## Tips and Tricks

### 🎯 Performance Tips

1. **Limit Scanning**: Only scan when needed (weekly is sufficient)
2. **Use Filters**: Narrow down channels before scanning
3. **Close Unused Apps**: Free up memory for smoother playback
4. **WiFi Recommended**: Mobile data may buffer or use lots of bandwidth

### 🌟 Discovery Tips

1. **Explore Categories**: Browse by category to find new content
2. **Country Hopping**: Check channels from different countries
3. **Language Filter**: Find channels in your native language
4. **Sort by Quality**: Look for "720p" or "1080p" in channel names

### ⚡ Playback Tips

1. **Landscape Mode**: Rotate phone for full-screen viewing
2. **Keep Screen On**: App prevents screen timeout during playback
3. **External Player**: MX Player often handles buffering better
4. **PiP Multitasking**: Watch while browsing other apps

### 💾 Data Saving Tips

1. **Download M3U**: Export working channels to avoid re-scanning
2. **Favorites Only**: Focus on 10-20 reliable channels
3. **Avoid Constant Rescanning**: Streams don't change that often
4. **WiFi for Scanning**: Checking 5000 streams uses significant data

---

## Troubleshooting

### Common Issues

#### "No channels found"

**Solutions**:
- Check internet connection
- Tap "Refresh" button
- Restart the app
- Check if firewall/VPN is blocking requests

#### "Channel won't play"

**Solutions**:
- Verify green checkmark (stream is working)
- Run a scan to update status
- Try external player (VLC)
- Stream may be geo-blocked or temporarily down

#### "Constant buffering"

**Solutions**:
- Test internet speed (need 5+ Mbps for HD)
- Switch to WiFi
- Close other apps using bandwidth
- Try lower-resolution streams
- Use external player with better buffering

#### "Scan taking forever"

**Solutions**:
- Cancel scan and use partial results
- Filter channels first, then scan
- Scanning 5000+ channels takes 5-10 minutes
- App checks streams in batches of 5

#### "App crashes"

**Solutions**:
- Clear app cache (Settings → Apps → TV Viewer → Clear Cache)
- Update to latest version
- Restart device
- Contact support with crash details

---

## Getting Help

### In-App Support

- **Help Screen**: Menu → Help & Support
- **Diagnostics**: Menu → Diagnostics (for technical details)
- **Send Feedback**: Menu → Send Feedback

### Contact Support

- **GitHub Issues**: https://github.com/tv-viewer-app/tv_viewer/issues
- Include: App version, device model, description of issue

### Community Resources

- **GitHub**: [github.com/tvviewer](https://github.com/tvviewer) (report bugs, request features)
- **FAQ**: See FAQ.md for common questions

---

## Privacy & Legal

**What TV Viewer Does**:
- Aggregates publicly available IPTV streams
- Does NOT host or provide content
- Does NOT collect personal data
- All streams from open-source repositories

**User Responsibility**:
- Ensure compliance with local laws
- Respect copyright and broadcasting rights
- Use responsibly

---

## Version History

**Current Version**: 1.5.0

**Recent Updates**:
- Added language filter
- Improved scanning performance
- Enhanced PiP support
- Material 3 design updates
- Help system and onboarding

---

**Enjoy TV Viewer!** 📺

If you find this app useful, please rate us on the Play Store and share with friends!

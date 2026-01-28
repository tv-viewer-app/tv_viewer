# TV Viewer - Frequently Asked Questions (FAQ)

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Channel Management](#channel-management)
3. [Playback Issues](#playback-issues)
4. [Features & Usage](#features--usage)
5. [Technical Questions](#technical-questions)
6. [Privacy & Legal](#privacy--legal)

---

## Installation & Setup

### 1. How do I install TV Viewer?

**Answer**: Download and install the APK from:
- Official GitHub releases page
- Google Play Store (if published)
- F-Droid (if available)

After installation, grant required permissions (internet access, storage for exports).

---

### 2. What permissions does the app need?

**Answer**: TV Viewer requires:
- **Internet**: To fetch channel lists and stream video
- **Storage** (optional): To export M3U playlists
- **Picture-in-Picture** (optional): For floating window playback

No other permissions are needed. The app does NOT access contacts, location, camera, or microphone.

---

### 3. Does the app work on iOS/iPhone?

**Answer**: Currently, TV Viewer is **Android-only**. iOS support is not planned due to App Store restrictions on IPTV apps. Consider using a web-based IPTV player on iOS.

---

### 4. What Android version do I need?

**Answer**: 
- **Minimum**: Android 6.0 (API 23)
- **Recommended**: Android 8.0+ for Picture-in-Picture support
- **Best Experience**: Android 10+ for latest features

---

## Channel Management

### 5. How do I add channels to the app?

**Answer**: Channels are automatically loaded from public IPTV repositories on first launch. The app fetches:
- iptv-org GitHub repository (5000+ channels)
- Public M3U playlists

You don't need to manually add channels. Just open the app and they'll load automatically.

---

### 6. Why are some channels not working?

**Answer**: IPTV streams can go offline for various reasons:
- **Server maintenance**: Broadcaster is updating
- **Expired links**: Stream URL changed
- **Geographic restrictions**: Channel blocked in your country
- **Temporary outages**: Try again later
- **Dead streams**: Permanently offline

Use the **Scan** feature to check which channels are currently working (green checkmark).

---

### 7. How often should I scan channels?

**Answer**: 
- **First time**: Run a full scan to identify working streams
- **Weekly**: Scan once a week for updates
- **As needed**: If favorites stop working

Scanning too frequently is unnecessary as streams don't change hourly.

---

### 8. Can I add my own M3U playlist?

**Answer**: Currently, TV Viewer only supports built-in public playlists. Custom M3U import is planned for a future update. Track this feature request on GitHub.

---

### 9. How do I save my favorite channels?

**Answer**:
1. Find a channel you like
2. Tap the **heart icon** (♡) on the right
3. Heart turns red (♥) when saved
4. View favorites by filtering or checking stats

Favorites are stored locally and persist across app restarts.

---

### 10. How many favorites can I save?

**Answer**: Unlimited. However, we recommend 10-50 favorites for best organization. Having 500+ favorites defeats the purpose of filtering.

---

## Playback Issues

### 11. The video is buffering constantly. What can I do?

**Answer**: Buffering is usually caused by:
- **Slow internet**: Need 3-5 Mbps for SD, 5-10 Mbps for HD
- **Server overload**: Popular channels may be congested
- **Peak hours**: Try different times

**Solutions**:
1. Connect to WiFi (not mobile data)
2. Close other apps using bandwidth
3. Try a different channel
4. Use an external player (VLC) with better buffering
5. Lower video quality (choose SD channels)

---

### 12. Video won't play at all

**Answer**: 
1. Check if channel has a **green checkmark** (working status)
2. If no checkmark, run a **Scan** to verify
3. If red X, stream is currently offline
4. Try enabling **External Player** in settings
5. Test your internet connection

If only specific channels fail, they may be geo-blocked or permanently offline.

---

### 13. How do I use an external player?

**Answer**:
1. Install VLC, MX Player, MPV, or Just Player from Play Store
2. Open TV Viewer → Menu → **Settings**
3. Enable "Use External Player"
4. Choose your preferred player
5. Tap any channel to launch in external app

**Benefits**: Better buffering, more playback controls, codec support.

---

### 14. Picture-in-Picture (PiP) not working

**Answer**: 
- **Check Android version**: Requires Android 8.0+
- **Enable in settings**: Android Settings → Apps → TV Viewer → Picture-in-Picture → Allow
- **Trigger PiP**: Press home button while video is playing, or tap PiP icon
- **Limitations**: Some channels/formats may not support PiP

---

### 15. Audio plays but no video / black screen

**Answer**: This indicates a codec issue:
- **Solution 1**: Enable external player (VLC has extensive codec support)
- **Solution 2**: Update your device software
- **Cause**: Some exotic video formats aren't supported by Android's native player

---

## Features & Usage

### 16. How do search and filters work together?

**Answer**: All filters are **cumulative** (AND logic):

- **Search alone**: Matches channel names
- **Filters alone**: Narrow by type/category/country/language
- **Search + Filters**: Both conditions must match

Example: Search "News" + Country "USA" = American channels with "News" in the name

**Clear all**: Tap "Clear Filters" button

---

### 17. What's the difference between scanning and loading?

**Answer**:
- **Loading**: Fetches channel list from repository (runs automatically)
- **Scanning**: Checks if each stream URL is accessible (manual, tap refresh icon)

Loading is fast (5-10 seconds). Scanning is slow (5-10 minutes for 5000 channels).

---

### 18. How do I export channels?

**Answer**:
1. Tap **three-dot menu** (⋮) in top-right
2. Select **"Export Channels"**
3. Choose export options
4. M3U file saved to **Downloads** folder
5. Share or import into other apps (VLC, Kodi)

---

### 19. Can I cast to Chromecast or smart TV?

**Answer**: Direct casting is not currently supported. Workarounds:
- Use **External Player** (VLC) and cast from there
- Enable PiP and screen mirror your entire phone
- Export M3U and import on smart TV apps

Native casting support is planned for future versions.

---

### 20. What do the stats numbers mean?

**Answer**: Stats bar shows:
- **X channels**: Total channels after filters applied
- **❤️ Y**: Number of favorited channels
- **✅ Z working**: Channels with green checkmark (verified streams)

---

## Technical Questions

### 21. Where do channels come from?

**Answer**: TV Viewer aggregates channels from:
- **iptv-org GitHub repository**: https://github.com/iptv-org/iptv
- Publicly available M3U playlists
- Open-source community contributions

The app does NOT host any content. All streams are external URLs.

---

### 22. Does the app use a lot of data?

**Answer**:
- **Loading channels**: 2-5 MB (one-time)
- **Scanning**: 50-100 MB (checks 5000 URLs)
- **Streaming video**:
  - SD quality: ~500 MB/hour
  - HD quality: ~1-2 GB/hour
  - 4K quality: 3-5 GB/hour

**Tip**: Use WiFi for scanning and streaming to avoid exceeding mobile data limits.

---

### 23. Is my viewing history tracked?

**Answer**: **NO**. TV Viewer:
- Does NOT log which channels you watch
- Does NOT track viewing duration
- Does NOT send analytics
- Does NOT collect personal information

Only locally stored data: favorites and app settings (via SharedPreferences).

---

### 24. Why does the app request internet permission?

**Answer**: Internet access is required to:
- Fetch channel lists from GitHub
- Stream video content
- Check stream availability during scans

The app does NOT:
- Upload personal data
- Track user behavior
- Display ads
- Make background requests

---

### 25. Can I use the app offline?

**Answer**: **No**. TV Viewer requires internet for:
- Loading channel lists
- Streaming video

However, the app caches the channel list locally, so browsing channels works without internet (but playback won't).

---

## Privacy & Legal

### 26. Is TV Viewer legal?

**Answer**: **Yes**, the app itself is legal. TV Viewer:
- Does NOT host or provide content
- Aggregates publicly available streams
- Acts as a directory/browser

**User responsibility**: Ensure compliance with local laws and copyright regulations in your country. Users are responsible for what they choose to stream.

---

### 27. Are the channels licensed?

**Answer**: TV Viewer does not control or manage channels. Streams are from:
- Official broadcaster websites
- Public IPTV lists
- Community-contributed sources

Some channels may be:
- ✅ Legal (official free streams)
- ⚠️ Unlicensed (user-uploaded)
- ❌ Copyrighted (check local laws)

Use at your own discretion.

---

### 28. Does the app show ads?

**Answer**: **NO**. TV Viewer is:
- 100% free
- No ads
- No in-app purchases
- No subscriptions
- Open-source

Supported by community contributions and donations (if applicable).

---

### 29. How do I report illegal content?

**Answer**: If you find a channel with illegal or inappropriate content:
1. **DO NOT** watch it
2. Note the channel name and URL
3. Report to the original source (iptv-org repository)
4. Email us at support@tvviewer.app

We will investigate and remove from aggregated lists if necessary.

---

### 30. Can I contribute to the project?

**Answer**: **Yes!** TV Viewer is open-source:
- **GitHub**: [github.com/tvviewer](https://github.com/tvviewer)
- **Report bugs**: Open an issue
- **Suggest features**: Open a feature request
- **Submit code**: Fork and create pull request
- **Translate**: Help localize the app
- **Donate**: Support development (link in About section)

---

## Still Have Questions?

### Contact Support

- **Email**: support@tvviewer.app
- **GitHub Issues**: [github.com/tvviewer/issues](https://github.com/tvviewer/issues)
- **In-App**: Menu → Help & Support

### Before Contacting Support

Please include:
1. App version (Menu → About)
2. Device model and Android version
3. Description of issue
4. Steps to reproduce
5. Screenshots (if applicable)

---

**Last Updated**: January 2025  
**App Version**: 1.5.0

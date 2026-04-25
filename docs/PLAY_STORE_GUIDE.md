# Publishing TV Viewer to Google Play Store

## Prerequisites

| Requirement | Status | Notes |
|------------|--------|-------|
| Google Play Developer Account | ❌ Needed | One-time $25 fee at [play.google.com/console](https://play.google.com/console) |
| Signed APK / AAB | ✅ CI builds APK | Need to switch to AAB (Android App Bundle) for Play Store |
| Privacy Policy URL | ⚠️ Need public URL | `docs/index.html#privacy` — requires public repo or separate hosting |
| App Icon (512x512) | ⚠️ Need hi-res | Current icon is `.ico` format; need PNG |
| Feature Graphic (1024x500) | ❌ Needed | Promotional banner for Play Store listing |
| Screenshots (min 2) | ❌ Needed | Phone screenshots of the app in action |

---

## Step 1: Create Google Play Developer Account

1. Go to [play.google.com/console](https://play.google.com/console)
2. Sign in with your Google account
3. Pay the **one-time $25 registration fee**
4. Complete identity verification (takes 1-2 days)
5. Accept the Developer Distribution Agreement

---

## Step 2: Generate a Signed Release Build

### Option A: App Signing by Google Play (Recommended)

Google manages the signing key. You upload an **upload key** signed AAB.

1. **Generate an upload keystore:**
   ```bash
   keytool -genkey -v -keystore upload-keystore.jks \
     -keyalg RSA -keysize 2048 -validity 10000 \
     -alias upload -storepass YOUR_PASSWORD
   ```

2. **Configure signing in `flutter_app/android/key.properties`:**
   ```properties
   storePassword=YOUR_PASSWORD
   keyPassword=YOUR_PASSWORD
   keyAlias=upload
   storeFile=../upload-keystore.jks
   ```

3. **Update `flutter_app/android/app/build.gradle`:**
   ```groovy
   def keystoreProperties = new Properties()
   def keystorePropertiesFile = rootProject.file('key.properties')
   if (keystorePropertiesFile.exists()) {
       keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
   }

   android {
       ...
       signingConfigs {
           release {
               keyAlias keystoreProperties['keyAlias']
               keyPassword keystoreProperties['keyPassword']
               storeFile keystoreProperties['storeFile'] ? file(keystoreProperties['storeFile']) : null
               storePassword keystoreProperties['storePassword']
           }
       }
       buildTypes {
           release {
               signingConfig signingConfigs.release
               minifyEnabled true
               shrinkResources true
               proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
           }
       }
   }
   ```

4. **Build AAB (not APK) for Play Store:**
   ```bash
   cd flutter_app
   flutter build appbundle --release
   ```
   Output: `build/app/outputs/bundle/release/app-release.aab`

### Option B: Update CI Workflow

Add to `.github/workflows/build-apk.yml`:
```yaml
- name: Build AAB for Play Store
  run: flutter build appbundle --release
  working-directory: flutter_app

- name: Upload AAB artifact
  uses: actions/upload-artifact@v4
  with:
    name: play-store-aab
    path: flutter_app/build/app/outputs/bundle/release/app-release.aab
```

> ⚠️ **NEVER commit `upload-keystore.jks` or `key.properties` to git!**
> Add them to `.gitignore` and store the keystore as a GitHub Actions secret.

---

## Step 3: Prepare Store Listing Assets

### App Icon (512 × 512 PNG, 32-bit, no alpha)
- Export the current tv_viewer icon as 512x512 PNG
- Must be PNG, no transparency, no rounded corners (Google adds those)

### Feature Graphic (1024 × 500 PNG)
- Promotional banner shown at top of listing
- Include app name, a tagline, and a screenshot/illustration
- Keep text minimal, large and readable

### Screenshots (minimum 2 per device type)
Take screenshots of these key screens:
1. **Channel list** — showing categories and channel count
2. **Player screen** — video playing with controls visible
3. **World map view** — interactive map with channel markers
4. **Search/filter** — showing search results
5. **Settings** — showing parental controls and privacy toggle

**Phone:** 1080×1920 or 1440×2560 PNG  
**Tablet (optional):** 1200×1920 or similar

---

## Step 4: Create App on Google Play Console

1. Go to **Play Console → Create app**
2. Fill in:
   - **App name:** TV Viewer — IPTV Player
   - **Default language:** English (US)
   - **App type:** Application
   - **Free or paid:** Free
   - **Declarations:** Accept all

---

## Step 5: Store Listing

### Short description (80 chars max):
```
Free IPTV player. Watch 5000+ live TV channels from around the world.
```

### Full description (4000 chars max):
```
TV Viewer is a free, open-source IPTV player that lets you watch thousands of live TV channels from around the world — completely free, with no account required.

🌍 5000+ CHANNELS
Automatically fetches channels from multiple IPTV repositories worldwide. News, sports, entertainment, music, kids, documentaries, and more — from over 100 countries.

🔍 SMART SEARCH & FILTERS
• Filter by country, category, or media type
• Search channels by name
• Group channels by country, category, or status
• Sort by name, country, or quality

🗺️ WORLD MAP VIEW
Browse channels on an interactive world map. Tap any country to see its available channels. Discover TV from places you never knew had live streams.

⭐ FAVORITES & HISTORY
Save your favorite channels for instant access. Recently watched history lets you jump back to what you were watching.

📡 AUTO CHANNEL SCANNING
Built-in stream checker validates channels in the background. Dead or broken channels are automatically hidden. Only working streams are shown.

🔒 PRIVACY FIRST
• No account or sign-up required
• No ads — ever
• Optional anonymous analytics (off by default)
• No channel names or URLs are collected
• Parental controls with PIN lock
• Open source — inspect every line of code on GitHub

📺 SUPPORTED FORMATS
• HLS (.m3u8)
• MPEG-TS
• HTTP/HTTPS streams
• Custom M3U playlists

TV Viewer is and always will be free. It is not affiliated with any TV network or content provider. All streams are sourced from publicly available IPTV repositories.
```

### Category: **Entertainment** → **Video Players & Editors**

### Content Rating: Fill out the **IARC questionnaire** honestly:
- Violence: None
- Sexual content: Some channels may contain adult content (parental controls available)
- User-generated content: No (channels are from public repositories)

### Privacy Policy URL:
- If repo is public: `https://tv-viewer-app.github.io/tv_viewer/#privacy`
- Alternative: Host a simple privacy page on any free hosting

---

## Step 6: App Content & Compliance

### Data Safety Form
Required for all apps. Based on our implementation:

| Question | Answer |
|----------|--------|
| Does your app collect or share user data? | Yes (optional analytics) |
| Is data collection optional? | **Yes** — user must opt in |
| Data types collected | App activity (features used), crash logs, app info (version) |
| Is data encrypted in transit? | **Yes** (HTTPS/TLS to Supabase) |
| Can users request data deletion? | Yes (uninstall removes all local data; analytics is anonymous) |
| Is data shared with third parties? | **No** |

### Ads Declaration
- **Does your app contain ads?** No

### App Access
- **Does your app require login?** No — unrestricted access

---

## Step 7: Release Management

### Internal Testing (recommended first)
1. Go to **Release → Testing → Internal testing**
2. Create a new release
3. Upload the `.aab` file
4. Add testers (your own email at minimum)
5. Review and roll out

### Production Release
1. Go to **Release → Production**
2. Create a new release
3. Upload the `.aab` file
4. Add release notes:
   ```
   What's new in v2.6.1:
   • Privacy-first: Analytics off by default, consent dialog on first launch
   • Security hardening: SSL verification, atomic file operations
   • Improved stability: Refactored player and settings modules
   • Better test coverage: 279 automated tests
   • 128 issues fixed since v1.0
   ```
5. Review and roll out to **100%** (or staged: 10% → 50% → 100%)

---

## Step 8: Ongoing Maintenance

### Automated Releases (CI/CD)
Consider using [r0adkll/upload-google-play](https://github.com/r0adkll/upload-google-play) GitHub Action:
```yaml
- name: Upload to Play Store
  uses: r0adkll/upload-google-play@v1
  with:
    serviceAccountJsonPlainText: ${{ secrets.PLAY_STORE_SERVICE_ACCOUNT }}
    packageName: com.tvviewer.app
    releaseFiles: flutter_app/build/app/outputs/bundle/release/app-release.aab
    track: internal
    status: completed
```

### Version Updates
When releasing a new version:
1. Bump version in all files (config.py, constants.dart, pubspec.yaml, help_screen.dart, README.md)
2. Update CHANGELOG.md
3. Tag and push → CI builds APK
4. Build AAB locally or via CI → Upload to Play Console

---

## Checklist

- [ ] Create Google Play Developer account ($25)
- [ ] Generate upload keystore (keep safe — NEVER lose this!)
- [ ] Create 512x512 app icon PNG
- [ ] Create 1024x500 feature graphic
- [ ] Take 4-6 screenshots on phone
- [ ] Build signed AAB
- [ ] Create app listing in Play Console
- [ ] Fill out Data Safety form
- [ ] Complete IARC content rating
- [ ] Set up privacy policy URL
- [ ] Upload AAB to Internal Testing track
- [ ] Test install from Play Store
- [ ] Promote to Production
- [ ] (Optional) Set up CI/CD for automated Play Store uploads

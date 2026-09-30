# LG Seller Lounge submission

## Product metadata

| Field | Value |
|---|---|
| App name | TV Viewer |
| App ID | `app.tvviewer.webos` |
| Version | 2.25.0 |
| Category | Entertainment |
| Supported UI resolutions | 1920x1080 and 1280x720 |
| Minimum planned platform | webOS TV 5.0 |
| Privacy policy | `https://github.com/tv-viewer-app/tv_viewer/blob/master/PRIVACY_POLICY.md` |
| Support | `https://github.com/tv-viewer-app/tv_viewer/issues` |

## Short description

Browse and play community-maintained live TV and radio streams with a
remote-first interface, search, filters, multi-source failover, and local
favorites.

## Full description

TV Viewer is a free and open-source IPTV player designed for the living room.
Browse the public community channel catalog by name, category, and media type,
then play compatible streams directly on your LG television.

For LG Content Store distribution, discovery is limited to public-interest
categories: news, education, documentary, culture, business, science, weather,
and legislative channels. Explicit-name filtering is applied before display.

The TV interface supports directional-pad navigation, Magic Remote pointer
input, Back, Play/Pause, source switching, pagination, and favorites stored
locally on the television. No account is required and the webOS edition does
not collect analytics.

Channel availability, regional access, and content rights are determined by
independent stream providers. TV Viewer does not host video content. Users must
only access content they are permitted to watch.

## Submission checklist

- [x] 80x80 runtime icon in `webos_app/icon.png`
- [x] 130x130 runtime icon in `webos_app/largeIcon.png`
- [x] 400x400 Seller Lounge icon in `store-listings/lg-webos/icon-400.png`
- [x] Required 1920x1080 splash screen in `webos_app/splash.png`
- [x] Launcher tile color and secondary description in `appinfo.json`
- [x] 1920x1080 IPK build
- [x] 1280x720 IPK build
- [x] Empty `requiredACG` declaration because no Luna APIs are called
- [x] First-run content and privacy notice before network access
- [x] No login, payment, advertising, analytics, or device identifier access
- [x] Four 1920x1080 Seller Lounge screenshots generated
- [x] LG UX scenario document generated
- [x] Evidence-backed App Self Checklist draft generated
- [x] Reproducible submission archive and SHA-256 manifest tooling
- [ ] Confirm generated Seller Lounge screenshots on a physical TV or official simulator
- [ ] Complete LG age-rating questionnaire
- [ ] Select distribution territories after content-rights review
- [ ] Run playback and remote tests on at least one physical LG TV
- [ ] Upload both resolution packages and submit the App Self Checklist

## Upload-ready Seller Lounge folder

Generate one flat folder containing every file needed during Seller Lounge
registration:

```powershell
python store-listings\lg-webos\tools\assemble_submission.py
```

Use:

```text
store-listings\lg-webos\upload-ready\
```

`SELLER_LOUNGE_FILE_MAP.txt` maps every Seller Lounge field to the exact file
to upload. The folder includes both IPKs, the 400x400 app icon, the 1920x1080
launcher background, screenshots, QA documents, privacy policy, and store
listing copy.

## Certification notes

- The application reads the public TV Viewer catalog through Supabase using a
  publishable RLS-restricted client key.
- The LG edition limits discovery to public-interest categories and blocks
  explicit channel names before rendering.
- Only HTTP and HTTPS media URLs are accepted by the client.
- Favorites and first-run acknowledgement remain in local storage.
- The app calls no Luna Bus APIs and declares `"requiredACG": []`.
- Store screenshots should demonstrate catalog browsing, visible D-pad focus,
  playback controls, filters, and favorites.

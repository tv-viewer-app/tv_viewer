# Privacy Policy

**Effective date:** 2 May 2026
**Last updated:** 2 May 2026
**Applies to:** TV Viewer Android app (`app.tvviewer.player`) and TV Viewer Windows desktop app

TV Viewer ("the app", "we", "our") is a free, open-source IPTV player developed by the TV Viewer community on GitHub. We respect your privacy and are committed to keeping data collection to the absolute minimum required to make the app work.

## TL;DR

- **No accounts.** You don't sign up, you don't sign in.
- **No advertising.** No ads, no ad SDKs, no ad IDs.
- **No tracking across apps or websites.**
- **No selling or sharing of personal data with third parties for marketing.**
- **Analytics are strictly opt-in** and contain no personal data.
- **The app is open source** — anyone can audit exactly what it does at https://github.com/tv-viewer-app/tv_viewer.

---

## 1. Information We Collect

### 1.1 Information collected automatically (always)

| Data | Why | Where it goes |
|------|-----|---------------|
| IPTV stream URLs you play | Required to load the video stream you selected | Sent only to the IPTV server hosting the stream (third party — see §3) |
| HTTP requests to M3U playlist sources | Required to fetch the channel list | Sent only to the configured playlist URLs (third party — see §3) |
| HTTP requests to GitHub Releases API | Used by the in-app update checker to detect new versions | Sent only to `api.github.com` |

These requests are **standard network calls** required for the app to function. We do not log them on any server we control.

### 1.2 Information you can choose to share (opt-in only)

The first time you launch the Windows desktop app, a consent dialog asks whether you want to enable **anonymous usage analytics**. The Android app does **not** collect analytics by default.

If — and only if — you opt in, we collect the following events. Each event includes the **anonymous device identifier** and **approximate location** described in the Play Store data-safety table at §1.4 below.

| Event | Triggered when | Properties sent |
|---|---|---|
| `app_launch` / `app_start` | App opens | platform, app version, timestamp |
| `channel_play` | You start a channel | category, country code of the channel, **SHA-256 hash of the URL** (no plaintext URL or channel name) |
| `channel_fail` | A channel fails to play | category, country code, URL hash, error type |
| `favorite` | You add or remove a favourite | category, country code, URL hash, action (`add`/`remove`) |
| `feature_use` | You open a major feature | feature name (e.g. `map_open`, `search`, `fullscreen`) — **no search query text** |
| `filter_used` (Android only) | You apply a filter | filter type (e.g. `country`) — **no filter values** |
| `scan_complete` | A health scan finishes | total channels, working count, duration in seconds |
| `session_end` | App closes | session duration, channels played, channels favourited |
| `app_crash` | An uncaught exception occurs | exception class, message (truncated to 200 chars), first stack-trace line, app version |

We do **not** collect: your name, email, phone number, precise location, IP address (Supabase logs the connection IP for ≤ 30 days at the network layer but we do not retain or analyse it), the names or URLs of channels you watch, your search queries, your watch history, your favourites list, or the list of other apps installed on your device.

You can disable analytics at any time:
- **Windows:** Settings → Privacy → Disable analytics
- **Android:** Settings → Privacy controls → Analytics off

### 1.4 Play Store data-safety mapping (Android)

This is the same information formatted to match the categories in the Google Play Store **Data safety** form so you can verify exactly what we declared:

| Play Store category | Subtype | Collected? | Shared? | Optional? | Purpose | What it is in our code |
|---|---|---|---|---|---|---|
| **Location** | Approximate location | ✅ Yes | ❌ No | ✅ Yes (opt-in) | Analytics | Two-letter country code derived from your **system locale only** — never from IP geolocation or GPS |
| **App info & performance** | Crash logs | ✅ Yes | ❌ No | ✅ Yes (opt-in) | App functionality, Analytics | Exception class, truncated message, first stack-trace line — no user data |
| **App info & performance** | Diagnostics | ✅ Yes | ❌ No | ✅ Yes (opt-in) | Analytics | Session duration, scan results, app version, platform |
| **App info & performance** | Other app performance data | ✅ Yes | ❌ No | ✅ Yes (opt-in) | Analytics | Channel play / fail counters used to compute aggregate channel-health stats |
| **App activity** | App interactions | ✅ Yes | ❌ No | ✅ Yes (opt-in) | Analytics | `feature_use`, `favorite`, `channel_play` events — names of features used, never of channels watched |
| **App activity** | Other user-generated content | ✅ Yes | ❌ No | ✅ Yes (opt-in) | App functionality | Channel name + URL + category + country you submit through the in-app **Submit channel** dialog; freeform text + rating you submit through the **Send feedback** dialog |
| **Device or other IDs** | Device or other IDs | ✅ Yes | ❌ No | ✅ Yes (opt-in) | Analytics | A **per-install random UUID v4** generated by the app and stored locally with file mode `0o600`. It is not the Android Advertising ID, the Android ID, the IMEI, or any hardware identifier. Uninstalling the app erases it. |

Categories we **do not** collect (do not check on the Play Console form):

| Play Store category | Why not |
|---|---|
| Personal info (name, email, address, race, religion, sexual orientation, etc.) | Never collected |
| Financial info | App is free; no payments |
| Health & fitness | Not collected |
| Messages, photos, audio, files | Not collected |
| Calendar, contacts | Not collected |
| Web browsing history | Not collected |
| **App activity → Installed apps** | We do not declare `QUERY_ALL_PACKAGES` and never call `getInstalledApplications()` |
| **App activity → In-app search history** | Search queries you type are processed locally and **never sent**. Only the *fact* that the search feature was opened is logged (under "App interactions") |
| **Location → Precise location** | Never collected — we have no `ACCESS_FINE_LOCATION` or `ACCESS_COARSE_LOCATION` permission |

### 1.3 Information stored only on your device

The following is saved locally on your device and **never transmitted to us**:

- Favourite channels, recently watched channels, watch history
- Repository / playlist URLs you've added
- App preferences (theme, sort order, filters)
- Channel logo cache (`~/.tv_viewer/logos/` on Windows, app cache on Android)

You can erase all of this by uninstalling the app or clearing app data in your OS settings.

## 2. Permissions We Request

### Android

| Permission | Purpose |
|------------|---------|
| `INTERNET` | Required to fetch channel lists and play streams |
| `ACCESS_NETWORK_STATE` | Detect Wi-Fi vs mobile to warn before large downloads |
| `WAKE_LOCK` | Keep the screen on while a video is playing |

The Android app does **not** request location, contacts, camera, microphone, SMS, call log, storage outside its own sandbox, or any other sensitive permission.

### Windows

The desktop app uses standard network and file-system access only within your user profile directory.

## 3. Third-Party Services

TV Viewer connects to several third-party services to deliver its functionality. **We do not control these services.** Their own privacy policies apply when the app talks to them:

| Service | Purpose | Privacy policy |
|---------|---------|----------------|
| GitHub (`api.github.com`, `github.com`) | Update checks, release downloads | https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement |
| Public M3U playlist hosts (e.g., iptv-org) | Channel list source | Varies by host — see the source list in app Settings |
| IPTV stream providers | The actual video streams you play | Varies by provider — TV Viewer is a player, not a stream host |
| Google Play Integrity API | Verifies the app installation is genuine on Android | https://policies.google.com/privacy |
| Supabase (analytics back-end, opt-in only) | Receives anonymous opt-in analytics from Windows | https://supabase.com/privacy |

When you play a stream, the IPTV provider hosting that stream necessarily sees your IP address — this is a fundamental requirement of internet streaming and is true of every video player. TV Viewer does not add any additional disclosure beyond what your video player would normally make.

## 4. How We Use Information

We use the limited data described above only to:

1. Deliver the channel list and play the streams you select
2. Notify you when an update is available
3. Diagnose crashes and improve the app (only if you opted in)

We do **not** use any data for advertising, profiling, scoring, or selling to third parties.

## 5. Data Retention

- **On-device data:** retained until you uninstall the app or clear app data.
- **Opt-in analytics:** retained for up to 12 months in aggregated form, then deleted.
- **Crash reports:** retained for up to 12 months for debugging, then deleted.
- We do not retain backups of personal data because we do not collect personal data.

## 6. Your Rights

Even though we collect very little data, you have full control:

- **Opt out of analytics** at any time in app Settings.
- **Erase all on-device data** by uninstalling the app or using your OS "Clear app data" option.
- **Request deletion** of any opt-in analytics tied to your install by contacting us (see §10). Because the analytics are anonymous, we may need details such as your install date and approximate region to locate the records.
- **Access / portability:** Because we do not store personal data tied to identifiable individuals, there is normally nothing personal to export. If you believe you have personal data with us, contact us and we will assist.

If you are in the EU/UK, you have rights under GDPR/UK-GDPR (access, rectification, erasure, restriction, objection, portability, and to lodge a complaint with your supervisory authority).
If you are in California, you have rights under CCPA/CPRA. We do **not** sell or share personal information.

## 7. Children's Privacy

TV Viewer is **not directed at children under 13**. The app contains community-curated streams and may surface content not appropriate for children. We do not knowingly collect personal information from children. If you believe a child has provided us with information, contact us and we will delete it.

## 8. Security

- The app is open source — its source code is publicly auditable.
- Network calls use HTTPS where the upstream service supports it.
- The Android app is signed with our official upload key (SHA-1 `56:21:F2:7C:DA:DC:12:C3:22:A4:00:BD:74:28:27:97:EA:97:6B:E4`); installs from sources other than Google Play that don't match this fingerprint may be tampered with.
- We follow the principle of minimum data collection: the strongest security posture is to not have the data in the first place.

## 9. International Transfers

If you opt in to analytics, the anonymous data is transmitted to Supabase, whose servers may be located outside your country (typically the EU or US). By opting in, you consent to this transfer. You can opt out at any time.

## 10. Contact

TV Viewer is a community open-source project, not a company — we do not run a customer-support inbox. All privacy questions, deletion requests, and concerns are handled through our public GitHub repository, which gives every request a permanent, auditable record:

- **General privacy questions or deletion requests (public):** open an issue at https://github.com/tv-viewer-app/tv_viewer/issues using the "Privacy request" template, or label your issue `privacy`. A maintainer will respond in the issue thread.
- **Confidential or security-sensitive disclosures (private):** open a private vulnerability report via GitHub Security Advisories at https://github.com/tv-viewer-app/tv_viewer/security/advisories/new — only repository maintainers can read it. See also [`SECURITY.md`](https://github.com/tv-viewer-app/tv_viewer/blob/master/SECURITY.md).

A free GitHub account is required to use either channel. If you cannot use GitHub for accessibility or other reasons, please indicate this in your initial message and we will arrange an alternative.

## 11. Changes to This Policy

We may update this policy from time to time. The "Last updated" date at the top reflects the most recent change. Material changes will be announced in the app's release notes and in the GitHub repository. Continued use of the app after a change means you accept the updated policy.

## 12. Open Source & Transparency

TV Viewer is licensed under the MIT License and developed in the open. You can review every line of code that handles your data:

- **Repository:** https://github.com/tv-viewer-app/tv_viewer
- **Analytics implementation (Windows):** [`analytics/`](https://github.com/tv-viewer-app/tv_viewer/tree/master/analytics)
- **Network layer (Android):** [`flutter_app/lib/services/`](https://github.com/tv-viewer-app/tv_viewer/tree/master/flutter_app/lib/services)

If you find anything in the code that contradicts this policy, please open an issue — we will fix the code or fix the policy.

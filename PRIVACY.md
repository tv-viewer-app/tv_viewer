# Privacy Policy

**Effective date:** 2 May 2026
**Last updated:** 14 October 2026
**Applies to:** TV Viewer Android app (`app.tvviewer.player`) and TV Viewer Windows desktop app

TV Viewer ("the app", "we", "our") is a free, open-source IPTV player developed by the TV Viewer community on GitHub. We respect your privacy and are committed to keeping data collection to the absolute minimum required to make the app work.

## TL;DR

- **No accounts.** You don't sign up, you don't sign in.
- **No advertising.** No ads, no ad SDKs, no ad IDs.
- **No ads or advertising SDKs.** Optional analytics and community sharing are
  separate from advertising and controlled in the app.
- **No sale of data for advertising.** Data needed for the public catalog,
  optional community sharing, and optional analytics is sent to Supabase as
  described below.
- **Analytics and community health sharing are optional and separate.** Their
  payloads include pseudonymous data such as channel names, URL hashes, and
  (for analytics) a random install identifier. URL hashes may be matched to
  known public streams.
- **The app is open source** — anyone can audit exactly what it does at https://github.com/tv-viewer-app/tv_viewer.

---

## 1. Information We Collect

### 1.1 Information collected automatically (always)

| Data | Why | Where it goes |
|------|-----|---------------|
| IPTV stream URLs you play | Required to load the video stream you selected | Sent only to the IPTV server hosting the stream (third party — see §3) |
| HTTP requests to M3U playlist sources | Required to fetch the channel list | Sent only to the configured playlist URLs (third party — see §3) |
| HTTP requests to GitHub Releases API | Used by the in-app update checker to detect new versions | Sent only to `api.github.com` |
| Supabase channel catalog and health data | Supplies the public channel catalog. On Android, community-health data is fetched only when **Share community channel data** is enabled. | Sent to Supabase. Catalog access remains available when community sharing is off. |

The app also connects to selected stream and playlist providers to play streams
and load channel lists. As with other network services, providers may process
connection metadata such as IP addresses under their own privacy policies.

### 1.2 Crowdsourced channel catalog (how the app stays up to date)

The app's channel catalog is **collaboratively maintained by all users**. Two data flows feed it:

| Flow | What is sent | Tied to your identity? | Visible to other users? |
|------|--------------|------------------------|--------------------------|
| **Channel submissions** (you tap **Submit channel** and fill in the form) | The channel name, stream URL, category and country **you typed** | No account or app-generated device ID is attached; network providers may process connection metadata | Yes — accepted submissions appear in the public catalog that every other app user fetches |
| **In-app feedback** (you tap **Send**) | Feedback text, rating, category, and a submission timestamp are prefilled in a GitHub issue form; analytics records only category, rating, message presence, and length when analytics is enabled | GitHub receives the form request when opened; the user must submit the issue | The issue is public if submitted |
| **Community health sharing** (optional on Android) | SHA-256 hash of a stream URL, health status, check time, and response time; the hash may be matched to a known public URL | No account or app-generated device ID is attached; network providers may process connection metadata | Health feedback is used in the shared channel experience. On Android, this data is fetched only when community sharing is enabled. |
| **Automatic playlist contributions** (optional on Android) | May include channel names, stream URLs, categories, countries, and logos | No account or app-generated device ID is attached; network providers may process connection metadata | Submitted channel details may appear in the shared catalog. |

**M3U / repository URLs you add manually in Settings → Repositories are stored only on your device.** They are not uploaded as repository URLs. On Android, if community sharing is enabled, newly discovered channel details may be contributed to the shared catalog; explicit submissions are also published there.

### 1.3 Information you can choose to share (opt-in only)

Analytics is off by default and requires opt-in. The Android first-use dialog
and Settings provide separate controls for analytics and community channel
sharing. Windows has its own privacy controls; the exact options differ by
client.

If — and only if — you opt in to analytics, events may include a random
per-install identifier, app/platform details, country derived from device
locale, feature usage, crash diagnostics, and playback-related data such as
channel names or URL hashes. URL hashes are not anonymous: they can be matched
against known stream URLs. See the app settings and source code for current
event fields.

| Event | Triggered when | Properties sent |
|---|---|---|
| `app_launch` / `app_start` | App opens | platform, app version, timestamp |
| `channel_play` | You start a channel | channel name, category, channel country, source, and URL hash; no plaintext stream URL |
| `channel_fail` | A channel fails to play | channel name, category, channel country, source, URL hash, failure type, and available error details |
| `favorite` | You add or remove a favourite | channel metadata including name, category, country, source, and URL hash, plus action (`add`/`remove`) |
| `feature_use` | You open a major feature | feature name (e.g. `map_open`, `search`, `fullscreen`) — **no search query text** |
| `filter_used` (Android only) | You apply a filter | filter type (e.g. `country`) — **no filter values** |
| `scan_complete` | A health scan finishes | total channels, working count, duration in seconds |
| `session_end` | App closes | session duration, channels played, channels favourited |
| `app_crash` | An uncaught exception occurs | exception class, message (truncated to 200 chars), first stack-trace line, app version |
| `feedback_submitted` | You open the in-app feedback form | feedback category, rating, whether text was entered, text length, and timestamp; the feedback text itself is prefilled in a GitHub issue form, not sent in this analytics event |

The app does not ask for your name, email, or phone number. Search text,
watch-history lists, favorites, and installed-app lists are not sent as
analytics fields. Channel names and URL hashes can still reveal channel
activity, and service providers may process connection metadata such as IP
addresses.

You can disable analytics at any time:
- **Windows:** Settings → Privacy
- **Android:** Settings → Analytics & Telemetry

On Android, **Share community channel data** is separate from analytics. When
off, the app does not send health reports or fetch shared health feedback.
Channels without a local health check show **Unknown**; local checks and the
public channel catalog remain available. When on, the app sends URL-hashed
health reports and fetches shared feedback. New playlist-channel contributions
may include stream URLs. You can change either setting in Android Settings.

### 1.4 Play Store data-safety mapping (Android)

This is a working mapping to Google Play **Data safety** categories, not a
substitute for checking the current Play Console declaration. Re-verify every
row against the exact submitted build and Play Console form before release:

| Play Store category | Subtype | Collected? | Shared? | Optional? | Purpose | What it is in our code |
|---|---|---|---|---|---|---|
| **Location** | Approximate location | ✅ Yes | ❌ No | ✅ Yes (opt-in) | Analytics | Android estimates country from the device timezone, with locale as a fallback; Windows uses system locale. No GPS or IP geolocation. Channel-country fields in playback events describe the channel, not the user's location. |
| **App info & performance** | Crash logs | ✅ Yes | ❌ No | ✅ Yes (opt-in) | Analytics | Exception class, sanitized/truncated message, and first stack-trace line |
| **App info & performance** | Diagnostics | ✅ Yes | ❌ No | ✅ Yes (opt-in) | Analytics | Session duration, scan results, app version, platform |
| **App info & performance** | Other app performance data | ✅ Yes, if community sharing is enabled | ✅ Yes | ✅ Yes (Android opt-in) | App functionality | URL-hashed channel-health reports and shared health feedback. Hashes can be matched to known streams. |
| **App activity** | App interactions | ✅ Yes, with analytics enabled | Sent to Supabase with opt-in analytics | ✅ Yes (opt-in) | Analytics | Events may include feature names and playback/favorite channel names and URL hashes. Search query text is not sent. |
| **App activity** | Other user-generated content | ✅ Yes | ✅ **Yes — catalog submissions are public; feedback issues are public if submitted** | Yes—only when you submit; automatic contributions are controlled by community sharing | App functionality | Submitted channel details can become public. In-app feedback opens a GitHub issue form with the text prefilled; do not include private or sensitive information. |
| **Device or other IDs** | Device or other IDs | ✅ Yes, if analytics is enabled | Sent with opt-in analytics | ✅ Yes (opt-in) | Analytics | A random per-install identifier is used for analytics. It is not the Android Advertising ID or a hardware identifier. |

The app does not request or intentionally send the following data categories.
Verify this list against the current app bundle and Play Console declarations
before each submission:

| Play Store category | Why not |
|---|---|
| Personal info (name, email, address, race, religion, sexual orientation, etc.) | Not requested by the app; do not include personal information in submitted channel data or feedback |
| Financial info | App is free; no payments |
| Health & fitness | Not collected |
| Messages, photos, audio, files | Not collected |
| Calendar, contacts | Not collected |
| Web browsing history | Not collected |
| **App activity → Installed apps** | We do not declare `QUERY_ALL_PACKAGES` and never call `getInstalledApplications()` |
| **App activity → In-app search history** | Search queries you type are processed locally and **never sent**. Only the *fact* that the search feature was opened is logged (under "App interactions") |
| **Location → Precise location** | Never collected — we have no `ACCESS_FINE_LOCATION` or `ACCESS_COARSE_LOCATION` permission |

### 1.5 Information stored only on your device

The following is saved locally on your device:

- Favourite channels, recently watched channels, and watch history. The
  separate opt-in analytics service may send an individual favorite action
  with channel metadata; it does not upload the local favorites or history list.
- M3U / repository URLs you add manually in **Settings → Repositories**
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
| GitHub (`api.github.com`, `github.com`) | Update checks, release downloads, and user-initiated in-app feedback issue forms | https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement |
| Public M3U playlist hosts (e.g., iptv-org) | Channel list source | Varies by host — see the source list in app Settings |
| IPTV stream providers | The actual video streams you play | Varies by provider — TV Viewer is a player, not a stream host |
| Supabase | Public catalog, optional Android community health, and opt-in analytics | https://supabase.com/privacy |

When you play a stream, the IPTV provider hosting that stream receives the network request and may process connection metadata, including your IP address. This is required for streaming.

## 4. How We Use Information

We use the data described above to:

1. Deliver the channel list and play the streams you select
2. Notify you when an update is available
3. Handle channel submissions and optional community health sharing
4. Analyze optional usage events and diagnose crashes if you opt in

We do **not** use any data for advertising, profiling, scoring, or selling to third parties.

## 5. Data Retention

- **On-device data:** retained until you uninstall the app or clear app data.
- **Supabase-hosted catalog, health reports, and analytics:** retention depends
  on service configuration and operational practices; this policy does not
  promise a fixed deletion period.
- **Third-party providers:** retention is governed by the provider's own
  policies and settings.

## 6. Your Rights

Even though we collect very little data, you have full control:

- **Opt out of analytics** at any time in app Settings.
- **Disable community sharing on Android** at any time in Settings; health
  reports stop and shared health feedback is no longer fetched.
- **Erase all on-device data** by uninstalling the app or using your OS "Clear app data" option.
- **Request access or deletion:** contact us using the private contact method in
  §10. We will assess what data can be located and handled; URL hashes and
  other pseudonymous data are not necessarily anonymous.

If you are in the EU/UK, you have rights under GDPR/UK-GDPR (access, rectification, erasure, restriction, objection, portability, and to lodge a complaint with your supervisory authority).
If you are in California, contact us with privacy requests under applicable
CCPA/CPRA rules. We do not use data for cross-context behavioral advertising
or sell it.

## 7. Children's Privacy

TV Viewer is **not directed at children under 13**. The app contains community-curated streams and may surface content not appropriate for children. We do not knowingly collect personal information from children. If you believe a child has provided us with information, contact us and we will delete it.

## 8. Security

- The app is open source — its source code is publicly auditable.
- Network calls use HTTPS where the upstream service supports it.
- We follow the principle of minimum data collection: the strongest security posture is to not have the data in the first place.

## 9. International Transfers

Supabase and other providers may process data in locations outside your country.
Review their current privacy information for details. Analytics and Android
community sharing can be disabled in the app; public catalog access and
required network requests may still transmit connection metadata.

## 10. Contact

For privacy questions and data requests, contact the project privately at
**tvviewerapp@proton.me**. Do not post personal information or private stream
URLs in a public issue. For security-sensitive reports, use GitHub Security
Advisories:

- **Confidential or security-sensitive disclosures (private):** open a private vulnerability report via GitHub Security Advisories at https://github.com/tv-viewer-app/tv_viewer/security/advisories/new — only repository maintainers can read it. See also [`SECURITY.md`](https://github.com/tv-viewer-app/tv_viewer/blob/master/SECURITY.md).


## 11. Changes to This Policy

We may update this policy from time to time. The "Last updated" date at the top reflects the most recent change. Material changes will be announced in the app's release notes and in the GitHub repository. Review the policy periodically; continued use does not replace any consent required by applicable law.

## 12. Open Source & Transparency

TV Viewer is licensed under the MIT License and developed in the open. You can review every line of code that handles your data:

- **Repository:** https://github.com/tv-viewer-app/tv_viewer
- **Analytics implementation (Windows):** [`analytics/`](https://github.com/tv-viewer-app/tv_viewer/tree/master/analytics)
- **Network layer (Android):** [`flutter_app/lib/services/`](https://github.com/tv-viewer-app/tv_viewer/tree/master/flutter_app/lib/services)

If you find anything in the code that contradicts this policy, please open an issue — we will fix the code or fix the policy.

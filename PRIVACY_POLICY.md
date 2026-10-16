# Privacy Policy — TV Viewer

**Last Updated:** October 16, 2026

## Overview

TV Viewer is a free, open-source IPTV streaming application. We respect your privacy and are committed to protecting your personal data.

## Data We Collect

### LG webOS TV Edition

The LG webOS TV edition does not collect analytics, create a device identifier,
or send channel health reports. It reads the public channel catalog from
Supabase and connects directly to the stream selected by the user. Favorites
and the first-run notice acknowledgement are stored only in the television's
local application storage. Requests to Supabase and stream providers may expose
connection metadata, such as an IP address, to those services.

### With Your Consent (Optional Analytics)

If you opt in to analytics, we collect:

- **Random install identifier** — a pseudonymous identifier, not an account or hardware ID
- **App version and platform** (e.g., Android 14, Windows 11)
- **Country estimate** — inferred from the device timezone, with locale as a fallback
- **Feature usage** — which app features are used (e.g., search, map, filters)
- **Playback events** — channel names, stream URL hashes, playback outcomes,
  and performance. Hashes can be matched to known streams; individual events
  can reveal playback activity even though they are not a local watch-history
  list.
- **Crash reports** — technical error information to fix bugs
- **Session duration** — how long the app is used per session

Disabling analytics in Android Settings immediately stops new collection and
discards queued events. Requests already sent cannot be recalled.

### Optional Community Channel Sharing

On Android, the **Share community channel data** setting controls both sending
and receiving community health data. When off, the app does not send channel
health reports or fetch channel-health feedback from Supabase; the public
channel catalog remains available, and local channel checks continue to work.
When enabled, the app sends SHA-256 hashes of stream URLs with working/broken
status, check timestamps, and response times, and fetches shared health feedback
from Supabase. It may also send newly discovered channel names, stream URLs,
categories, countries, and logos.

URL hashes are not anonymous: a hash can be matched against a known public
stream URL, and health reports may reveal which streams were checked or played.
Usage analytics remains a separate, optional setting and is not required to
receive shared channel-health feedback. You can enable or disable this sharing
at any time in Settings. Submitting a channel through the explicit
“Contribute a Channel” action sends the channel details you enter. The in-app
feedback flow opens a GitHub issue form with your text, rating, and category
prefilled; analytics records only the category, rating, message presence, and
length when enabled. Do not include private or sensitive information, and
review the form before submitting it publicly.

### What We Do NOT Collect

- The app does not request your name, email, or phone number as standard
  fields; information you choose to include in a public GitHub feedback issue
  is sent to GitHub
- Raw channel URLs through health reports (health reports send SHA-256 URL hashes)
- Network connection metadata: the app does not intentionally send IP addresses
  as analytics fields, but service providers may process them when handling requests
- Your location (beyond the country from your locale setting)
- Your contacts, photos, files, or any other device data

## Android Permissions

TV Viewer requests only the minimum permissions needed to function:

| Permission | Why It's Needed |
|-----------|-----------------|
| `INTERNET` | Streaming live TV channels over the network |
| `ACCESS_NETWORK_STATE` | Detecting connectivity to enable offline mode gracefully |
| `WAKE_LOCK` | Preventing the screen from sleeping during video playback |

No camera, microphone, location, contacts, storage, or other sensitive permissions are requested.

## LG webOS TV Permissions

The webOS edition does not request Luna Bus access or sensitive device
permissions. It requires network access only to load the public catalog and
play user-selected streams.

## Data Storage

The public channel catalog, community health data, and opt-in analytics use
Supabase. Access controls are applied to the service, but channel names and
URL hashes can be matched to known streams and should not be treated as
anonymous. Data retention depends on service configuration; this policy does
not promise a fixed deletion period.

On Android, community sharing controls both sending channel-health reports and
fetching shared health feedback. When sharing is off, the public channel
catalog remains available and local checks continue to work; channels without
a local check show Unknown. When sharing is enabled, newly discovered playlist
channel details may be contributed to the shared catalog. Explicit channel
submissions are published when submitted.

## Your Rights

- **Opt out anytime**: Go to Settings → disable "Help improve TV Viewer"
- **Community sharing**: Go to Settings → disable "Share community channel data"
- **No account required**: Public catalog and streaming requests still connect
  to network services, which may process connection metadata.
- **Data requests**: Contact tvviewerapp@proton.me. Pseudonymous identifiers
  and URL hashes are not necessarily anonymous; we will assess what can be
  located and handled.

## Third-Party Services

- **Supabase** (public catalog, optional community health, and opt-in analytics): [supabase.com/privacy](https://supabase.com/privacy)
- **IPTV streams**: TV Viewer discovers publicly available streams from open repositories. We do not host, control, or moderate stream content.

## Content Disclaimer

The Android and desktop editions aggregate publicly available IPTV streams.
Some channels may contain mature content. Their first-run flow requires an
18+ confirmation; parental controls are available in Settings.

The LG webOS edition instead limits discovery to public-interest categories
and shows a content and privacy notice. It does not provide the Android
Settings controls or an age-verification service. Category and name filtering
cannot guarantee the suitability or distribution rights of every live stream.

## Children's Privacy

TV Viewer is not directed at children. The Android and desktop editions require
an 18+ confirmation. The LG edition's store age rating must be determined
through LG's questionnaire and review, not inferred from its catalog filters.
We do not knowingly collect data from minors.

## Changes to This Policy

We may update this policy with new app versions. Changes will be noted in the app changelog.

## Contact

For private privacy questions or data deletion requests, contact
tvviewerapp@proton.me. Do not include personal data in public GitHub issues.
For non-sensitive policy questions, use
[GitHub Issues](https://github.com/tv-viewer-app/tv_viewer/issues).

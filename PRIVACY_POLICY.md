# Privacy Policy — TV Viewer

**Last Updated:** April 2026

## Overview

TV Viewer is a free, open-source IPTV streaming application. We respect your privacy and are committed to protecting your personal data.

## Data We Collect

### With Your Consent (Optional Analytics)

If you opt in to anonymous analytics, we collect:

- **Anonymous device ID** — a randomly generated identifier, not linked to your identity
- **App version and platform** (e.g., Android 14, Windows 11)
- **Country** — derived from your system locale (e.g., "US", "IL")
- **Feature usage** — which app features are used (e.g., search, map, filters)
- **Crash reports** — technical error information to fix bugs
- **Session duration** — how long the app is used per session

### What We Do NOT Collect

- Your name, email, or any personal identifiers
- Channel URLs or names you watch (URLs are one-way hashed before any transmission)
- Your IP address (not stored by our analytics backend)
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

## Data Storage

Analytics data, when opted in, is stored in a Supabase database with:
- Row-Level Security (RLS) policies restricting access
- No personally identifiable information (PII)
- Automatic data retention policies

## Your Rights

- **Opt out anytime**: Go to Settings → disable "Help improve TV Viewer"
- **No account required**: The app works fully without any data collection
- **Data deletion**: Contact us to request deletion of your anonymous device ID

## Third-Party Services

- **Supabase** (analytics backend): [supabase.com/privacy](https://supabase.com/privacy)
- **IPTV streams**: TV Viewer discovers publicly available streams from open repositories. We do not host, control, or moderate stream content.

## Content Disclaimer

TV Viewer aggregates publicly available IPTV streams. Some channels may contain mature content. Users must confirm they are 18+ on first launch. Parental controls are available in Settings.

## Children's Privacy

This app is not intended for children under 18. We do not knowingly collect data from minors.

## Changes to This Policy

We may update this policy with new app versions. Changes will be noted in the app changelog.

## Contact

For privacy questions or data deletion requests:
- **GitHub Issues**: [github.com/tv-viewer-app/tv_viewer/issues](https://github.com/tv-viewer-app/tv_viewer/issues)
- **GitHub Issues**: [Report a privacy concern](https://github.com/tv-viewer-app/tv_viewer/issues)

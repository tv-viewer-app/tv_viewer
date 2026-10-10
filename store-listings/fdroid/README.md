# F-Droid Submission

## Status: Under review

Original MR: https://gitlab.com/fdroid/fdroiddata/-/merge_requests/39248
- Reopened after the initial inactivity closure
- DependencyInfoBlock and splitinstall fixes landed in v2.22.4
- Reproducible ABI-split builds being updated for v2.25.2

## Unified Android Distribution

1. **DependencyInfoBlock disabled** — `flutter_app/android/app/build.gradle` line 82
2. **Splitinstall ProGuard rules** — `flutter_app/android/app/proguard-rules.pro` (last 4 lines)
3. **Metadata follows `build-flutter.yml` template** — see `metadata/app.tvviewer.player.yml`
4. **Reproducible builds enabled** — developer-signed reference APKs plus signing-key pin
5. **ABI splits enabled** — armeabi-v7a, arm64-v8a, and x86_64 use version-code suffixes 1, 2, and 3
6. **One Android product build** — GitHub, Google Play, and F-Droid use the same source policy and feature set
7. **No in-app APK installer** — no package-install permission or update `FileProvider`; sideload users can open GitHub Releases in their browser or use Obtainium
8. **Accurate anti-feature disclosure** — `NonFreeNet` explains the community playlist hosts, FMStream, and shared Supabase service; `Tracking` explains the data sent and the opt-in controls for analytics and community sharing
9. **Supabase remains functional** — RLS enforces access; analytics and channel-health/automatic playlist sharing are independently opt-in and off by default
10. **No fabricated EPG** — simulated current/next schedules were removed
11. **Consent-first startup** — no playlist or service network request starts until the first-run notice is completed

## Resubmission Steps

### Option A: Reopen existing MR
Comment on !39248:
```
Hi @linsui, @mezinster, and @eyoussef1. The app is now updated to v2.25.2
with one Android product configuration for GitHub, Google Play, and F-Droid:
- DependencyInfoBlock disabled for APKs and bundles
- Play Core splitinstall and Flutter deferred-component references removed
- Reproducible developer-signed APKs enabled
- ABI splits configured with version codes 1421, 1422, and 1423
- Metadata aligned with templates/build-flutter.yml
- The in-app APK installer, REQUEST_INSTALL_PACKAGES, and FileProvider are
  removed from every Android build; Settings opens GitHub Releases externally
- GitHub publishes the same ABI APKs used for F-Droid reproducibility checks
- FMStream and the full community source set are consistently enabled and
  disclosed with NonFreeNet
- Supabase community statistics and catalog reads remain enabled and are
  disclosed with NonFreeNet
- Anonymous analytics and channel-health/automatic playlist sharing are
  separate opt-ins, both off by default; Tracking reasons disclose the data
  and hashes that may match known public stream URLs
- Simulated EPG schedules and invented program titles are removed
- The OpenStreetMap user agent now uses app.tvviewer.player
- Fastlane includes changelogs for version codes 1421, 1422, and 1423
- Startup still waits for first-run consent before network access

Could you please rerun the pipeline and review the updated APK comparison?
```

### Option B: New MR to fdroiddata
```bash
# Clone fdroiddata
git clone https://gitlab.com/fdroid/fdroiddata.git
cd fdroiddata

# Create branch
git checkout -b app.tvviewer.player

# Copy metadata
cp /path/to/store-listings/fdroid/metadata/app.tvviewer.player.yml metadata/app.tvviewer.player.yml

# Commit and push
git add metadata/app.tvviewer.player.yml
git commit -m "New app: TV Viewer (app.tvviewer.player)"
git push origin app.tvviewer.player

# Create MR on GitLab
```

## Key Details for Submission
- **App ID:** app.tvviewer.player
- **Source:** https://github.com/tv-viewer-app/tv_viewer
- **Flutter version:** 3.44.4
- **Subdir:** flutter_app
- **Current version:** 2.25.2+142
- **License:** MIT

## Supabase Behavior

All Android distributions use the same public Supabase publishable client
configuration. Supabase row-level security is the authorization boundary.
With explicit opt-in, `analytics_events` stores anonymous product events.
Shared catalog reads remain available. Channel health reports and automatic
contributions of newly found playlist channels are disabled by default and
require a separate opt-in. Health reports transmit URL hashes, which may be
matched to known streams. Explicit channel submissions send the details entered
by the user. The metadata explains both `NonFreeNet` and `Tracking`.

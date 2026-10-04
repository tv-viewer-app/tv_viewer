# F-Droid Submission

## Status: Under review

Original MR: https://gitlab.com/fdroid/fdroiddata/-/merge_requests/39248
- Reopened after the initial inactivity closure
- DependencyInfoBlock and splitinstall fixes landed in v2.22.4
- Reproducible ABI-split builds being updated for v2.25.1

## Unified Android Distribution

1. **DependencyInfoBlock disabled** — `flutter_app/android/app/build.gradle` line 82
2. **Splitinstall ProGuard rules** — `flutter_app/android/app/proguard-rules.pro` (last 4 lines)
3. **Metadata follows `build-flutter.yml` template** — see `metadata/app.tvviewer.player.yml`
4. **Reproducible builds enabled** — developer-signed reference APKs plus signing-key pin
5. **ABI splits enabled** — armeabi-v7a, arm64-v8a, and x86_64 use version-code suffixes 1, 2, and 3
6. **One Android product build** — GitHub, Google Play, and F-Droid use the same source policy and feature set
7. **No in-app APK installer** — no package-install permission or update `FileProvider`; sideload users can open GitHub Releases in their browser or use Obtainium
8. **Accurate anti-feature disclosure** — `NonFreeNet` covers community playlist hosts, FMStream, and Supabase; `Tracking` covers explicitly opt-in anonymous analytics
9. **Supabase remains functional** — the public publishable client value is embedded, while RLS enforces access; analytics remains off until the user opts in
10. **No fabricated EPG** — simulated current/next schedules were removed
11. **Consent-first startup** — no playlist or service network request starts until the first-run notice is completed

## Resubmission Steps

### Option A: Reopen existing MR
Comment on !39248:
```
Hi @linsui, @mezinster, and @eyoussef1. The app is now updated to v2.25.1
with one Android product configuration for GitHub, Google Play, and F-Droid:
- DependencyInfoBlock disabled for APKs and bundles
- Play Core splitinstall and Flutter deferred-component references removed
- Reproducible developer-signed APKs enabled
- ABI splits configured with version codes 1411, 1412, and 1413
- Metadata aligned with templates/build-flutter.yml
- The in-app APK installer, REQUEST_INSTALL_PACKAGES, and FileProvider are
  removed from every Android build; Settings opens GitHub Releases externally
- GitHub publishes the same ABI APKs used for F-Droid reproducibility checks
- FMStream and the full community source set are consistently enabled and
  disclosed with NonFreeNet
- Supabase community statistics, shared channel health, and explicitly opt-in
  analytics are consistently enabled and disclosed with NonFreeNet/Tracking
- Simulated EPG schedules and invented program titles are removed
- The OpenStreetMap user agent now uses app.tvviewer.player
- Fastlane includes the versionCode 141 changelog
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
- **Current version:** 2.25.1+141
- **License:** MIT

## Supabase Behavior

All Android distributions use the same public Supabase publishable client
configuration. Supabase row-level security is the authorization boundary.
With explicit user opt-in, `analytics_events` stores anonymous product events.
The shared service also reads the consolidated community catalog and exchanges
URL-hashed working/broken health reports. The metadata declares `NonFreeNet`
and `Tracking`; analytics is disabled by default until the user opts in.

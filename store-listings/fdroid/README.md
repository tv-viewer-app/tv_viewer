# F-Droid Submission

## Status: Under review

Original MR: https://gitlab.com/fdroid/fdroiddata/-/merge_requests/39248
- Reopened after the initial inactivity closure
- DependencyInfoBlock and splitinstall fixes landed in v2.22.4
- Reproducible ABI-split builds updated for v2.24.5

## Fixes Applied

1. **DependencyInfoBlock disabled** — `flutter_app/android/app/build.gradle` line 82
2. **Splitinstall ProGuard rules** — `flutter_app/android/app/proguard-rules.pro` (last 4 lines)
3. **Metadata follows `build-flutter.yml` template** — see `metadata/app.tvviewer.player.yml`
4. **Reproducible builds enabled** — developer-signed reference APKs plus signing-key pin
5. **ABI splits enabled** — armeabi-v7a, arm64-v8a, and x86_64 use version-code suffixes 1, 2, and 3
6. **Self-updater removed from F-Droid builds** — no GitHub update check, APK download UI, package-install permission, or update `FileProvider`
7. **F-Droid source policy added** — only the curated `iptv-org` index is enabled by default; bundled adult, direct, and unreviewed sources are disabled
8. **Supabase disabled in F-Droid builds** — no analytics, community catalog, statistics, or channel-health requests and no credentials compiled into the APK
9. **Consent-first startup** — no playlist or service network request starts until the first-run notice is completed
10. **No additional terms** — the F-Droid first-run notice is informational and does not require an age declaration

## Resubmission Steps

### Option A: Reopen existing MR
Comment on !39248:
```
Hi @linsui and @seekme-seekyou. The MR branch is now updated to v2.24.5 with
the requested policy fixes:
- DependencyInfoBlock disabled for APKs and bundles
- Play Core splitinstall and Flutter deferred-component references removed
- Reproducible developer-signed APKs enabled
- ABI splits configured with version codes 1391, 1392, and 1393
- Metadata aligned with templates/build-flutter.yml
- Self-updater and REQUEST_INSTALL_PACKAGES removed from the F-Droid build
- Only the curated iptv-org playlist is enabled by default
- Supabase analytics and shared channel services are compile-time disabled
- Startup waits for the first-run informational notice before network access

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
- **Current version:** 2.24.5+139
- **License:** MIT

## Supabase Behavior

Standard GitHub/Play builds can receive Supabase credentials at build time.
With explicit user opt-in, `analytics_events` stores anonymous product events.
Separately, the shared channel service can read a consolidated channel catalog
and exchange URL-hashed working/broken health reports. F-Droid builds force both
services off at compile time and are built without Supabase credentials.

# F-Droid Submission

## Status: Closed (needs resubmission)

Original MR: https://gitlab.com/fdroid/fdroiddata/-/merge_requests/39248
- Closed 2026-08-12 due to inactivity
- All requested fixes were implemented in v2.22.4

## Fixes Applied

1. **DependencyInfoBlock disabled** — `flutter_app/android/app/build.gradle` line 82
2. **Splitinstall ProGuard rules** — `flutter_app/android/app/proguard-rules.pro` (last 4 lines)
3. **Metadata follows `build-flutter.yml` template** — see `metadata/app.tvviewer.player.yml`

## Resubmission Steps

### Option A: Reopen existing MR
Comment on !39248:
```
Hi @linsui, apologies for the delay. Both requested fixes have been applied:
- DependencyInfoBlock disabled in build.gradle
- Splitinstall classes handled with proguard rules

The app is now at v2.23.0 (versionCode 133). I've also restructured the metadata
to follow the build-flutter.yml template. Could you please reopen this MR? Thanks!
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
- **Flutter version:** 3.32.0
- **Subdir:** flutter_app
- **Current version:** 2.23.0+133
- **License:** MIT

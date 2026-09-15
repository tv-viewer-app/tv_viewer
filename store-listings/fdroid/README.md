# F-Droid Submission

## Status: Under review

Original MR: https://gitlab.com/fdroid/fdroiddata/-/merge_requests/39248
- Reopened after the initial inactivity closure
- DependencyInfoBlock and splitinstall fixes landed in v2.22.4
- Reproducible ABI-split builds updated for v2.24.3

## Fixes Applied

1. **DependencyInfoBlock disabled** — `flutter_app/android/app/build.gradle` line 82
2. **Splitinstall ProGuard rules** — `flutter_app/android/app/proguard-rules.pro` (last 4 lines)
3. **Metadata follows `build-flutter.yml` template** — see `metadata/app.tvviewer.player.yml`
4. **Reproducible builds enabled** — developer-signed reference APKs plus signing-key pin
5. **ABI splits enabled** — armeabi-v7a, arm64-v8a, and x86_64 use version-code suffixes 1, 2, and 3

## Resubmission Steps

### Option A: Reopen existing MR
Comment on !39248:
```
Hi @linsui and @seekme-seekyou, apologies for the delay. The MR branch is now
updated to v2.24.3 with the requested fixes:
- DependencyInfoBlock disabled for APKs and bundles
- Play Core splitinstall and Flutter deferred-component references removed
- Reproducible developer-signed APKs enabled
- ABI splits configured with version codes 1371, 1372, and 1373
- Metadata aligned with templates/build-flutter.yml

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
- **Current version:** 2.24.3+137
- **License:** MIT

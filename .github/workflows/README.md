# GitHub Actions Workflows

This directory contains automated CI/CD workflows for the TV Viewer project.

## Workflows

### 1. `release.yml` - Automated Release Build
**Purpose:** Complete release automation with conventional commit parsing

**Triggers:**
- Push tags matching `v*` (e.g., `v1.9.0`, `v2.0.0`)
- Manual dispatch via Actions tab

**What it does:**
1. Parses conventional commits since last release
2. Generates categorized release notes
3. Builds Windows EXE (PyInstaller)
4. Builds Android APK (Flutter)
5. Creates GitHub release with all assets

**Duration:** ~7-8 minutes

**Artifacts:**
- `TV_Viewer_vX.Y.Z_Windows.exe` - Windows executable
- `TV_Viewer_vX.Y.Z_Android.apk` - Android APK
- `RELEASE_NOTES.md` - Markdown release notes

**Documentation:** See `../RELEASE_PROCESS.md`

**Usage:**
```bash
git tag v1.10.0
git push origin v1.10.0
```

---

### 2. `android-build.yml` - Android APK Build
**Purpose:** Continuous integration for Flutter Android app

**Triggers:**
- Push to `master` branch (only if `flutter_app/**` files changed)
- Manual dispatch via Actions tab

**What it does:**
1. Sets up Java 17 and Flutter 3.19.0
2. Gets Flutter dependencies
3. Builds release APK
4. Extracts version from `pubspec.yaml`
5. Copies APK to `dist/android/` with version name
6. Uploads artifact (30-day retention)
7. Commits APK to repository (with `[skip ci]`)

**Duration:** ~4 minutes

**Artifacts:**
- `tv-viewer-flutter-apk` - Build artifact (30 days)
- `dist/android/TV_Viewer_vX.Y.Z.apk` - Committed to repo

**Usage:** Automatically runs on push to master (if Flutter files changed)

---

## Workflow Comparison

| Feature | release.yml | android-build.yml |
|---------|-------------|-------------------|
| **Trigger** | Version tags | Push to master |
| **Windows Build** | ✅ Yes | ❌ No |
| **Android Build** | ✅ Yes | ✅ Yes |
| **Release Notes** | ✅ Generated | ❌ No |
| **GitHub Release** | ✅ Created | ❌ No |
| **Commit to Repo** | ❌ No | ✅ APK committed |
| **Purpose** | Production releases | Development CI |

## Maintenance

### Updating Python Version
Edit `release.yml`:
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'  # ← Change here
```

### Updating Flutter Version
Edit both workflow files:
```yaml
- name: Set up Flutter
  uses: subosito/flutter-action@v2
  with:
    flutter-version: '3.19.0'  # ← Change here
```

### Updating Java Version
Edit both workflow files:
```yaml
- name: Set up Java
  uses: actions/setup-java@v4
  with:
    java-version: '17'  # ← Change here
```

### Adding New Commit Types
Edit `release.yml` in the `generate-release-notes` step:
```bash
# Add new case
case "$MSG" in
  newtype:*|newtype\(*)
    NEWCATEGORY="${NEWCATEGORY}- ${MSG#*: }\n"
    ;;
  ...
esac

# Add to output
if [ -n "$NEWCATEGORY" ]; then
  NOTES="${NOTES}## 🆕 New Category\n\n${NEWCATEGORY}\n"
fi
```

### Changing Release Asset Names
Edit `release.yml` in respective build jobs:
```bash
# Windows job
Move-Item "dist\TV_Viewer.exe" "dist\YourNewName_${version}.exe"

# Android job
cp build/app/outputs/flutter-apk/app-release.apk "../dist/android/YourNewName_${VERSION}.apk"

# Also update in create-release job
files: |
  artifacts/windows-exe/YourNewName_${{ ... }}.exe
  artifacts/android-apk/YourNewName_${{ ... }}.apk
```

## Troubleshooting

### Workflow Not Triggering
- **Tags:** Check tag format matches `v*` (e.g., `v1.0.0` not `1.0.0`)
- **Master push:** Verify you pushed to `master` branch
- **Path filters:** For `android-build.yml`, ensure `flutter_app/**` files changed

### Build Failures
- **Dependencies:** Check if `requirements.txt` or `pubspec.yaml` changed
- **Python version:** Verify Python 3.11 compatible
- **Flutter version:** Check Flutter 3.19.0 compatibility
- **Disk space:** Large builds may run out of space (rare)

### Release Not Created
- **Permissions:** Verify `contents: write` permission in workflow
- **Token:** `GITHUB_TOKEN` should be automatic (no secrets needed)
- **Artifacts:** Check previous jobs uploaded artifacts successfully

### Commits Parsed Incorrectly
- **Format:** Verify commits follow conventional format: `type: description`
- **Previous tag:** Check if previous tag exists (first release special case)
- **History:** Ensure `fetch-depth: 0` for full history

## Testing Workflows

### Test Locally with act
```bash
# Install act
# brew install act  (macOS)
# choco install act (Windows)

# Test release workflow
act -W .github/workflows/release.yml --input version=v0.0.1-test

# Test android build
act -W .github/workflows/android-build.yml
```

### Test in GitHub (Safe)
```bash
# Create test tag
git tag v0.0.1-test
git push origin v0.0.1-test

# Check workflow runs
# Delete test release after verification
# gh release delete v0.0.1-test --yes
```

## Security

### Secrets
No secrets required for basic operation:
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions

Optional secrets for enhanced functionality:
- `ANDROID_SIGNING_KEY` - For Android APK signing
- `WINDOWS_SIGNING_CERT` - For Windows EXE code signing
- `SLACK_WEBHOOK` - For release notifications

### Permissions
Current permissions:
```yaml
permissions:
  contents: write  # Required to create releases and push commits
```

### Security Best Practices
- ✅ Workflows only trigger on specific events
- ✅ No third-party scripts (only official actions)
- ✅ Artifacts retained for limited time (7-30 days)
- ✅ Builds run in isolated runners
- ⚠️ Commits to repo should be reviewed (android-build.yml)

## Performance Optimization

### Caching
Both workflows use caching:
- Python: `cache: 'pip'` - Caches pip packages
- Flutter: `flutter-action` - Caches Flutter SDK

### Parallel Jobs
`release.yml` uses job dependencies:
```
generate-release-notes → build-windows ⎫
                       → build-android  ⎬→ create-release
                                        ⎭
```
Windows and Android builds run in parallel for speed.

### Artifact Retention
- `release.yml`: 7 days (short - only needed for release creation)
- `android-build.yml`: 30 days (longer - for QA testing)

## Monitoring

### Workflow Status
- Check Actions tab: https://github.com/user/repo/actions
- Subscribe to workflow notifications in GitHub settings
- Use GitHub CLI: `gh run list --workflow=release.yml`

### Build Logs
- View in Actions → Select workflow run → Select job
- Download logs: `gh run download <run-id>`
- Logs retained for 90 days

### Success Metrics
Monitor:
- Build success rate
- Build duration (should be ~7-8 min for release)
- Release asset sizes
- Workflow execution frequency

## Related Documentation

- `../RELEASE_PROCESS.md` - Complete release process guide
- `../CONVENTIONAL_COMMITS.md` - Commit format reference
- `../ISSUE_21_IMPLEMENTATION.md` - Implementation details
- GitHub Actions docs: https://docs.github.com/actions

## Support

For issues with workflows:
1. Check this README
2. Review workflow logs in Actions tab
3. Check related documentation
4. Create issue with `ci/cd` label
5. Include workflow run URL and relevant logs

## Version History

- **v1.0** (2024-01-15): Initial release workflow implementation
  - Conventional commit parsing
  - Multi-platform builds
  - Automated release creation

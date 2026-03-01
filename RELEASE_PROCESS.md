# Automated Release Process

This document explains how to use the automated release workflow for the TV Viewer project.

## Overview

The release workflow automatically:
1. ✅ Parses conventional commits since the last release
2. 📝 Generates categorized changelog/release notes
3. 🪟 Builds Windows EXE executable
4. 🤖 Builds Android APK
5. 🚀 Creates GitHub release with all assets attached

## Triggering a Release

### Method 1: Push a Version Tag (Recommended)

```bash
# Tag the current commit with version
git tag v1.9.0

# Push the tag to GitHub
git push origin v1.9.0
```

This automatically triggers the release workflow.

### Method 2: Manual Workflow Dispatch

1. Go to **Actions** tab in GitHub
2. Select **Release Build** workflow
3. Click **Run workflow**
4. Enter the version tag (e.g., `v1.9.0`)
5. Click **Run workflow**

## Conventional Commit Format

The workflow parses commits following the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Supported Types

| Type | Category | Description | Example |
|------|----------|-------------|---------|
| `feat` | ✨ New Features | New features | `feat: add dark mode toggle` |
| `fix` | 🐛 Bug Fixes | Bug fixes | `fix: resolve crash on startup` |
| `perf` | ⚡ Performance | Performance improvements | `perf: optimize video buffering` |
| `refactor` | ♻️ Refactoring | Code refactoring | `refactor: simplify channel loader` |
| `docs` | 📚 Documentation | Documentation changes | `docs: update installation guide` |
| `style` | 💄 Style | Code style/formatting | `style: format with black` |
| `test` | ✅ Tests | Test additions/updates | `test: add unit tests for player` |
| `build` | 🔧 Build System | Build system changes | `build: update PyInstaller config` |
| `ci` | 👷 CI/CD | CI/CD changes | `ci: add release workflow` |
| `chore` | 📦 Chores | Maintenance tasks | `chore: update dependencies` |

### Breaking Changes

To mark breaking changes:

```bash
# Using ! suffix
git commit -m "feat!: redesign settings API"

# Or in commit body
git commit -m "feat: redesign settings API

BREAKING CHANGE: Settings API changed from dict to class-based"
```

Breaking changes appear in a special section at the top of release notes.

### Commit Examples

```bash
# Feature with scope
git commit -m "feat(ui): add channel search functionality"

# Bug fix
git commit -m "fix: prevent duplicate channel entries"

# Performance improvement
git commit -m "perf(player): reduce memory usage by 30%"

# Documentation
git commit -m "docs: add troubleshooting section to README"

# Multiple changes
git commit -m "feat: add EPG support

- Fetch program guide from API
- Display current/next programs
- Add schedule view"
```

## Release Notes Structure

The generated release notes include:

```markdown
# 📺 TV Viewer v1.9.0

Release built on 2024-01-15

## ⚠️ Breaking Changes
(if any)

## ✨ New Features
- Feature 1
- Feature 2

## 🐛 Bug Fixes
- Fix 1
- Fix 2

## ⚡ Performance Improvements
...

## ♻️ Code Refactoring
...

## 📚 Documentation
...

## 🔧 Build System
...

## 👷 CI/CD
...

## ✅ Tests
...

## 📦 Other Changes
(non-conventional commits)

---

## 📥 Installation

### Windows
1. Download TV_Viewer_v1.9.0_Windows.exe
2. Install VLC Media Player
3. Run the executable

### Android
1. Download TV_Viewer_v1.9.0_Android.apk
2. Enable installation from unknown sources
3. Install the APK

## 📋 Requirements

**Windows:**
- Windows 10/11 (64-bit)
- VLC Media Player 3.0+

**Android:**
- Android 8.0 (API 26) or higher
```

## Workflow Jobs

### 1. Generate Release Notes
- Fetches full git history
- Parses commits since last tag
- Categorizes by conventional commit type
- Generates formatted release notes
- Outputs release notes for use by other jobs

### 2. Build Windows EXE
- Sets up Python 3.11
- Installs dependencies
- Runs PyInstaller build
- Verifies executable creation
- Renames with version
- Uploads as artifact

### 3. Build Android APK
- Sets up Java 17 and Flutter 3.19.0
- Gets Flutter dependencies
- Builds release APK
- Verifies APK creation
- Renames with version
- Uploads as artifact

### 4. Create GitHub Release
- Downloads all artifacts
- Creates GitHub release
- Attaches all assets:
  - Windows EXE
  - Android APK
  - Release notes (RELEASE_NOTES.md)
- Publishes release (not draft)

## Release Assets

Each release includes:

| Asset | Description |
|-------|-------------|
| `TV_Viewer_vX.Y.Z_Windows.exe` | Windows executable (standalone) |
| `TV_Viewer_vX.Y.Z_Android.apk` | Android APK (signed release) |
| `RELEASE_NOTES.md` | Detailed release notes (markdown) |

## Versioning Strategy

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (v2.0.0): Breaking changes
- **MINOR** (v1.9.0): New features (backward compatible)
- **PATCH** (v1.9.1): Bug fixes (backward compatible)

### Version Bumping

Before creating a release, update version in:

1. **Python app**: `config.py`
   ```python
   APP_VERSION = "1.9.0"
   ```

2. **Flutter app**: `flutter_app/pubspec.yaml`
   ```yaml
   version: 1.9.0+19
   ```

Note: The workflow reads version from the git tag, not from files.

## Best Practices

### 1. Commit Frequently with Conventional Commits
```bash
# Do this
git commit -m "feat: add channel favorites"
git commit -m "fix: resolve video stuttering"
git commit -m "docs: update README"

# Not this
git commit -m "made changes"
git commit -m "work in progress"
```

### 2. Create Descriptive Release Tags
```bash
# Good tags
v1.9.0    # New minor version
v1.9.1    # Patch release
v2.0.0    # Major version

# Avoid
release-1
version_1.9.0
```

### 3. Test Before Releasing
```bash
# Run tests locally
pytest tests/

# Build locally to verify
python build.py
cd flutter_app && flutter build apk --release
```

### 4. Review Generated Release Notes
After workflow completes:
1. Check the GitHub release page
2. Review the generated notes
3. Edit if needed to add context
4. Verify all assets are attached

## Troubleshooting

### Build Fails - Windows
- Check Python version (3.11 required)
- Verify all dependencies install correctly
- Check PyInstaller compatibility
- Review build logs in Actions

### Build Fails - Android
- Check Flutter version (3.19.0)
- Verify Java 17 is installed
- Check Gradle configuration
- Review signing configuration

### Release Notes Empty
- Ensure commits follow conventional format
- Check that previous tag exists
- Verify git history is fetched (`fetch-depth: 0`)

### Assets Not Attached
- Check artifact upload succeeded
- Verify artifact download paths
- Review file naming matches pattern

## Manual Release Edits

After automatic release creation, you can:

1. Go to the release page
2. Click **Edit release**
3. Modify description
4. Add additional context
5. Upload extra assets
6. Save changes

## Security Notes

- Workflow uses `GITHUB_TOKEN` (automatic, no setup needed)
- Windows EXE is unsigned (users may see security warnings)
- Android APK is signed (requires signing key in repo secrets)
- All builds run in isolated GitHub Actions runners

## Example Workflow Run

```
1. Developer pushes tag: git push origin v1.9.0
2. Workflow triggers automatically
3. Job 1: Generate release notes (30s)
   - Parses 15 commits since v1.8.0
   - Categories: 5 features, 3 fixes, 2 docs
4. Job 2: Build Windows EXE (3min)
   - Installs dependencies
   - PyInstaller build succeeds
   - Uploads TV_Viewer_v1.9.0_Windows.exe
5. Job 3: Build Android APK (4min)
   - Sets up Flutter
   - Gradle build succeeds
   - Uploads TV_Viewer_v1.9.0_Android.apk
6. Job 4: Create release (15s)
   - Downloads all artifacts
   - Creates GitHub release
   - Attaches 3 assets
   - Release published: https://github.com/user/repo/releases/tag/v1.9.0
```

Total time: ~7-8 minutes

## Related Files

- `.github/workflows/release.yml` - Main release workflow
- `.github/workflows/android-build.yml` - Android build workflow (separate)
- `build.py` - Python build script
- `requirements.txt` - Python dependencies
- `flutter_app/pubspec.yaml` - Flutter configuration

## Support

For issues with the release process:
1. Check workflow logs in Actions tab
2. Review this documentation
3. Create an issue with logs attached
4. Tag with `ci/cd` label

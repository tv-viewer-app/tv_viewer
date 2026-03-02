# TV Viewer — CI/CD Workflows

## Overview

| Workflow | File | Trigger | Purpose | Blocking? |
|----------|------|---------|---------|-----------|
| **CI** | `ci.yml` | Push, PR, manual | Lint, test, security scan, Flutter analyze | **Yes** |
| **Build** | `build.yml` | Push (source), manual, called by release | Windows EXE + Android APK | No |
| **Release** | `release.yml` | Tag push (v*), manual | Cross-platform release with GitHub Release | No |
| **CVE Scanner** | `cve-scanner.yml` | Daily 6 AM UTC, manual | pip-audit + safety, creates issue on findings | No |

> **Deprecated workflows** (`test.yml`, `security-gate.yml`, `pr-validation.yml`, `code-review.yml`,
> `qa-validation.yml`, `build-windows.yml`, `build-ubuntu.yml`, `android-build.yml`,
> `build-release.yml`, `release-gate.yml`) are stubs that redirect to the new files.
> They will be removed in a future cleanup.

## Workflow Pipeline

```
Developer Push / PR to master
        │
        └──► ci.yml
              ├── Job 1: python-checks (flake8, bandit, shell=True, pytest)
              ├── Job 2: flutter-checks (flutter analyze — only if flutter_app/** changed)
              └── Job 3: security (pip-audit, secret detection — only if *.py or requirements.txt changed)
              │
              └── All 3 run in parallel, gated by dorny/paths-filter

Push to master (source files changed)
        │
        └──► build.yml
              ├── Job 1: build-windows (PyInstaller → TV_Viewer.exe)
              └── Job 2: build-android (Flutter → app-release.apk)
              │
              └── Both run in parallel, upload as artifacts (never committed to repo)

Tag Push (v*)
        │
        └──► release.yml
              ├── Job 1: build (calls build.yml via workflow_call)
              └── Job 2: release (downloads artifacts, extracts CHANGELOG, creates GitHub Release)

Daily (6 AM UTC)
        │
        └──► cve-scanner.yml → Creates issue if vulnerabilities found
```

## What Blocks a PR Merge

- ❌ Fatal Python errors (E9, F63, F7, F82)
- ❌ HIGH severity Bandit security issues
- ❌ `shell=True` in production code
- ❌ Failing pytest tests

## Caching Strategy

| Cache | Keyed On | Used By |
|-------|----------|---------|
| **pip** | `requirements.txt` hash | ci.yml, build.yml (Windows) |
| **Flutter SDK** | Flutter version | ci.yml, build.yml (Android) |
| **pub packages** | `pubspec.lock` hash | ci.yml, build.yml (Android) |
| **Gradle** | `*.gradle*` + `pubspec.lock` hash | build.yml (Android) |

## Release Process

1. Update version in `config.py` (`APP_VERSION`) and `flutter_app/pubspec.yaml`
2. Update `CHANGELOG.md` with release notes under `## [X.Y.Z]`
3. Commit and push to master
4. Create tag: `git tag v2.0.3 && git push origin v2.0.3`
5. `release.yml` triggers automatically → calls `build.yml` → creates GitHub Release
6. Or manually: `gh workflow run release.yml -f version=v2.0.3`

## Manual Triggers

```bash
# Run CI checks
gh workflow run ci.yml

# Build artifacts
gh workflow run build.yml

# Create a release
gh workflow run release.yml -f version=v2.0.3

# Run CVE scan
gh workflow run cve-scanner.yml
```

## Secrets Required

| Secret | Used By | Purpose |
|--------|---------|---------|
| `SUPABASE_URL` | build.yml (Android) | Supabase backend URL via --dart-define |
| `SUPABASE_ANON_KEY` | build.yml (Android) | Supabase anonymous key via --dart-define |
| `GITHUB_TOKEN` | release.yml | Automatically provided, creates releases |

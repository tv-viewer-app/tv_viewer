# TV Viewer — CI/CD Workflows

## Overview

| Workflow | File | Trigger | Purpose | Blocking? |
|----------|------|---------|---------|-----------|
| **Tests** | `test.yml` | Push, PR, manual | Multi-platform test matrix (Ubuntu 22.04/24.04 × Python 3.10/3.11/3.12) | No |
| **PR Validation** | `pr-validation.yml` | PR to master | Lint + security + tests + version sync | **Yes** |
| **Code Review** | `code-review.yml` | PR (Python files) | Flake8, Radon complexity, threading safety | No |
| **Security Gate** | `security-gate.yml` | Tags, PR, manual | Bandit, pip-audit, secret detection, shell=True check | **Yes** (HIGH blocks) |
| **CVE Scanner** | `cve-scanner.yml` | Daily 6 AM UTC, manual | pip-audit + safety, creates issue on findings | No |
| **QA Validation** | `qa-validation.yml` | PR (Python files) | Placeholder test detection, coverage, naming | No |
| **Build Ubuntu** | `build-ubuntu.yml` | Push (Python), manual | PyInstaller binary for Ubuntu 22.04/24.04 | No |
| **Build Windows** | `build-windows.yml` | Push (Python), manual | PyInstaller .exe for Windows | No |
| **Build Android** | `android-build.yml` | Push (flutter_app/), manual | Flutter APK | No |
| **Release Gate** | `release-gate.yml` | Tags (v*), manual | 5-stage gate: test, security, quality, docs, build | **Yes** |
| **Build Release** | `build-release.yml` | After Release Gate, manual | Build all 3 platforms + create GitHub Release | No |

## Workflow Pipeline

```
Developer Push/PR
        │
        ├──► test.yml (matrix)
        ├──► pr-validation.yml (blocking gate)
        ├──► code-review.yml (annotations)
        ├──► security-gate.yml (blocking on HIGH)
        └──► qa-validation.yml (quality check)

Tag Push (v*)
        │
        └──► release-gate.yml
              ├── Gate 1: Test (6 matrix combos)
              ├── Gate 2: Security (bandit + audit)
              ├── Gate 3: Quality (complexity + lint)
              ├── Gate 4: Docs (CHANGELOG + README)
              └── Gate 5: Build (Ubuntu + Windows + Android)
                    │
                    └──► build-release.yml
                          ├── Build Ubuntu (22.04 + 24.04)
                          ├── Build Windows (.exe)
                          ├── Build Android (.apk)
                          └── Create GitHub Release with all artifacts

Daily (6 AM UTC)
        │
        └──► cve-scanner.yml → Creates issue if vulnerabilities found
```

## What Blocks a PR Merge

- ❌ Fatal Python errors (E9, F63, F7, F82)
- ❌ HIGH severity Bandit security issues
- ❌ `shell=True` in production code
- ❌ Failing tests

## What Blocks a Release

- ❌ Any test gate failure (6 matrix combinations)
- ❌ HIGH severity security issues
- ❌ More than 5 very-high-complexity functions
- ❌ Missing README.md or CHANGELOG.md
- ❌ Version not documented in CHANGELOG.md
- ❌ Any platform build failure (Ubuntu/Windows/Android)

## Release Process

1. Update version in `config.py` (`APP_VERSION`) and `flutter_app/pubspec.yaml`
2. Update `CHANGELOG.md` with release notes
3. Commit and push to master
4. Create tag: `git tag v1.9.0 && git push origin v1.9.0`
5. Release Gate runs automatically (5 gates)
6. Build Release creates GitHub Release with all platform artifacts
7. Or manually: `gh workflow run build-release.yml -f version=1.9.0`

## Manual Triggers

All workflows support manual dispatch via GitHub Actions UI or CLI:

```bash
# Run tests
gh workflow run test.yml

# Run security scan
gh workflow run security-gate.yml

# Build for specific platform
gh workflow run build-ubuntu.yml
gh workflow run build-windows.yml

# Trigger full release
gh workflow run release-gate.yml -f version=1.9.0
gh workflow run build-release.yml -f version=1.9.0
```

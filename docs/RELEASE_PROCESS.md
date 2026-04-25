# TV Viewer — Release Process

**Copilot and developer checklist for every release.**
Every step is mandatory. Do not skip phases or reorder gates.

---

## Phase 0: Pre-Flight (Before Any Code Changes)

| # | Step | Tool / Command | Gate |
|---|------|---------------|------|
| 0.1 | **Verify master is clean** | `git status` — no uncommitted changes | ✅ Clean working tree |
| 0.2 | **Pull latest** | `git pull origin master` | ✅ Up to date |
| 0.3 | **Check CI is green** | GitHub API: `list_workflow_runs` for ci.yml, confirm latest `conclusion: success` | ✅ CI passing |
| 0.4 | **Review open GitHub Issues** | `list_issues` state=OPEN — note which are fixed in this release | List captured |

---

## Phase 1: Security Review

| # | Step | Tool / Command | Gate |
|---|------|---------------|------|
| 1.1 | **Python dependency audit** | `pip-audit -r requirements.txt` | ✅ No known CVEs |
| 1.2 | **Secret detection** | `grep -rn` for API keys, tokens, passwords in tracked files | ✅ No secrets in code |
| 1.3 | **Bandit security scan** | `bandit -r core/ ui/ utils/ -ll` | ✅ No HIGH/CRITICAL findings |
| 1.4 | **Flutter analyze** | `cd flutter_app && flutter analyze --no-fatal-infos` | ✅ 0 errors, 0 warnings |
| 1.5 | **Review Supabase RLS** | Verify anon key can only INSERT (not read/update/delete sensitive data) | ✅ Policies unchanged |

---

## Phase 2: Code & Performance Review

| # | Step | Tool / Command | Gate |
|---|------|---------------|------|
| 2.1 | **Run Python tests** | `python -m pytest tests/ -v` | ✅ All tests pass |
| 2.2 | **Run build validation** | `python tests/validate_build.py` | ✅ Exit code 0 |
| 2.3 | **Flake8 lint** | `flake8 core/ ui/ utils/ --select=E9,F63,F7,F82` | ✅ No fatal errors |
| 2.4 | **Build Windows EXE** | `python build.py` | ✅ EXE created in dist/ |
| 2.5 | **Smoke test Windows app** | Launch EXE, verify channel list loads, play one stream | ✅ App functional |
| 2.6 | **Performance spot-check** | Scroll channel list (14k+ channels), verify responsive (5-line scroll) | ✅ No lag |
| 2.7 | **Code review (if changes > 100 lines)** | Launch `code-review` agent on staged changes | ✅ No blocking issues |

---

## Phase 3: Version Bump

**All version references must be updated atomically in a single commit.**

| # | File | Field | Example |
|---|------|-------|---------|
| 3.1 | `config.py` | `APP_VERSION` | `"2.1.7"` |
| 3.2 | `flutter_app/pubspec.yaml` | `version` | `2.1.7+17` |
| 3.3 | `flutter_app/android/local.properties` | `flutter.versionName` / `flutter.versionCode` | `2.1.7` / `17` |
| 3.4 | **7 Dart files** (hardcoded User-Agent) | `'TV Viewer/X.Y.Z'` | `'TV Viewer/2.1.7'` |
| 3.5 | `CHANGELOG.md` | Add `## [X.Y.Z] - YYYY-MM-DD` section under `[Unreleased]` | Follows Keep a Changelog |

### Dart files with hardcoded versions (update ALL):
```
flutter_app/lib/screens/diagnostics_screen.dart
flutter_app/lib/screens/help_screen.dart
flutter_app/lib/screens/home_screen.dart
flutter_app/lib/screens/player_screen.dart        (2 occurrences)
flutter_app/lib/services/firebase_services_examples.dart
flutter_app/lib/services/fmstream_service.dart     (2 occurrences)
flutter_app/lib/services/m3u_service.dart          (2 occurrences)
```

### Batch update command (PowerShell):
```powershell
# Replace OLD → NEW across all Dart files + pubspec + local.properties
$old = "2.1.6"; $new = "2.1.7"; $oldBuild = "16"; $newBuild = "17"
Get-ChildItem flutter_app -Recurse -Include *.dart,pubspec.yaml |
  ForEach-Object {
    (Get-Content $_.FullName -Raw) -replace [regex]::Escape($old), $new |
    Set-Content $_.FullName -NoNewline
  }
# local.properties separately
(Get-Content flutter_app/android/local.properties -Raw) `
  -replace "versionName=$old","versionName=$new" `
  -replace "versionCode=$oldBuild","versionCode=$newBuild" |
  Set-Content flutter_app/android/local.properties -NoNewline
```

---

## Phase 4: Issue Triage & Documentation

| # | Step | Tool / Command | Gate |
|---|------|---------------|------|
| 4.1 | **Close fixed issues** | For each issue fixed in this release: `close issue` via GitHub API with comment referencing the version | ✅ All resolved issues closed |
| 4.2 | **Update issue labels** | Add version label (e.g., `v2.1.7`) to closed issues if applicable | Done |
| 4.3 | **Review open issues** | Confirm no P0/blocking issues remain open that should block release | ✅ No blockers |
| 4.4 | **Update docs if needed** | If architecture/API/config changed: update ARCHITECTURE.md, API.md, SUPPORT_GUIDE.md, README.md | Docs current |
| 4.5 | **Verify CHANGELOG.md** | Confirm all user-facing changes are documented with correct date | ✅ Complete |

---

## Phase 5: Commit, Tag, Push

| # | Step | Command | Gate |
|---|------|---------|------|
| 5.1 | **Stage all changes** | `git add -A` | Staged |
| 5.2 | **Commit with conventional format** | `git commit -m "vX.Y.Z: <summary>\n\n<details>\n\nCo-authored-by: Copilot <...>"` | Committed |
| 5.3 | **Create annotated tag** | `git tag vX.Y.Z` | Tagged |
| 5.4 | **Push commit + tag** | `git push origin master && git push origin vX.Y.Z` | Pushed |

---

## Phase 6: Workflow Verification

| # | Step | Tool / Command | Gate |
|---|------|---------------|------|
| 6.1 | **Monitor CI workflow** | `list_workflow_runs` for ci.yml — wait for `conclusion: success` | ✅ CI green |
| 6.2 | **If CI fails** | `get_job_logs` → read errors → fix → commit → push → re-check | ✅ Fixed |
| 6.3 | **Monitor Release workflow** | `list_workflow_runs` for release.yml — wait for `conclusion: success` | ✅ Release green |
| 6.4 | **Verify both build jobs** | Check `Build Windows EXE` ✅ and `Build Android APK` ✅ | Both pass |
| 6.5 | **If Release fails** | Get logs, diagnose (usually Flutter compile error or artifact naming), fix, re-tag if needed | ✅ Fixed |

---

## Phase 7: Post-Release Verification

| # | Step | Tool / Command | Gate |
|---|------|---------------|------|
| 7.1 | **Verify GitHub Release exists** | Check releases page — title, tag, date correct | ✅ Release page live |
| 7.2 | **Verify Windows EXE attached** | `TV_Viewer_vX.Y.Z_Windows.exe` present in release assets | ✅ Binary attached |
| 7.3 | **Verify Android APK attached** | `TV_Viewer_vX.Y.Z_Android.apk` present in release assets | ✅ Binary attached |
| 7.4 | **Verify release notes** | CHANGELOG content extracted correctly into release body | ✅ Notes correct |
| 7.5 | **Update any remaining issues** | Add release version comment to related issues | Done |
| 7.6 | **Report to user** | Summary: version, what's included, links to release + binaries | ✅ Reported |

---

## Quick Reference: Semver Rules

| Change Type | Bump | Example |
|-------------|------|---------|
| Breaking API change | MAJOR | 2.0.0 → 3.0.0 |
| New feature (backward compatible) | MINOR | 2.1.6 → 2.2.0 |
| Bug fix (backward compatible) | PATCH | 2.1.6 → 2.1.7 |

---

## Conventional Commit Format

```
<type>[optional scope]: <description>

[optional body]

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

| Type | Category | Example |
|------|----------|---------|
| `feat` | ✨ New Features | `feat: add dark mode toggle` |
| `fix` | 🐛 Bug Fixes | `fix: resolve crash on startup` |
| `perf` | ⚡ Performance | `perf: optimize video buffering` |
| `security` | 🔒 Security | `security: tighten RLS policies` |
| `docs` | 📚 Documentation | `docs: update architecture guide` |
| `test` | ✅ Tests | `test: add Supabase contract tests` |
| `ci` | 👷 CI/CD | `ci: fix Flutter analyze step` |
| `refactor` | ♻️ Refactoring | `refactor: consolidate telemetry` |

---

## Workflow Architecture

```
git push origin master ──→ ci.yml (4 jobs)
                              ├── Detect changes (paths-filter)
                              ├── Python checks (flake8, bandit, pytest)
                              ├── Flutter checks (flutter analyze)
                              └── Dependency audit (pip-audit, secret scan)

git push origin vX.Y.Z ──→ release.yml
                              ├── build.yml (reusable, 2 parallel jobs)
                              │   ├── Build Windows EXE (PyInstaller)
                              │   └── Build Android APK (Flutter)
                              └── Create GitHub Release
                                  ├── Download artifacts
                                  ├── Rename with version
                                  ├── Extract CHANGELOG notes
                                  └── gh release create
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| CI Flutter analyze fails | Wrong package imports in test files | Fix `package:` imports to match `pubspec.yaml` name |
| CI Python checks fail | Flake8 or Bandit finding | Fix the code issue, not the linter config |
| Release APK build fails | Dart compile error or version mismatch | Check `flutter analyze` locally, fix Dart errors |
| Release EXE build fails | Missing hidden import | Add to `build.py` hidden_imports list |
| Release notes empty | Version not in CHANGELOG.md | Ensure `## [X.Y.Z]` header exists before tagging |
| Assets not attached | Artifact name mismatch | Check build.yml output names match release.yml download names |

---

## Related Files

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | CI pipeline (lint, test, analyze, audit) |
| `.github/workflows/build.yml` | Reusable build (Windows + Android) |
| `.github/workflows/release.yml` | Tag-triggered release creation |
| `build.py` | PyInstaller build script |
| `TV_Viewer.spec` | PyInstaller configuration |
| `tests/test_core.py` | Python unit tests (31 tests) |
| `tests/validate_build.py` | Post-build validation |
| `config.py` | App version + configuration |
| `flutter_app/pubspec.yaml` | Flutter version + dependencies |
| `CHANGELOG.md` | Release history |

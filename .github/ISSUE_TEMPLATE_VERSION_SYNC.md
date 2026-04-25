---
name: Version Sync Issue
about: Track version discrepancies across platforms
title: '[VERSION] Sync versions across platforms'
labels: documentation, maintenance
assignees: ''
---

## Version Discrepancy Detected

**Date:** 2026-01-29

### Current Versions

| Platform | Version | Location | Last Updated |
|----------|---------|----------|--------------|
| **Python Desktop** | 1.4.4 | config.py | Unknown |
| **Android Flutter** | 1.7.0 | flutter_app/pubspec.yaml | 2026-01-28 |
| **Planned** | 1.8.0 | Milestones | Future |

### Issue

The Python desktop application (config.py) shows version 1.4.4, while:
- Latest commit message mentions "v1.7.0"
- Android app is at version 1.7.0
- This creates confusion about which version is current

### Recommendation

1. **Decide version strategy:**
   - Option A: Keep separate versions per platform
   - Option B: Sync all platforms to same version number
   - Option C: Use semantic versioning with platform suffix (e.g., 1.7.0-android, 1.4.4-desktop)

2. **Update documentation:**
   - README.md should clearly show versions for each platform
   - CHANGELOG.md should track versions separately if needed

3. **Next release:**
   - If desktop app gets updates, bump to 1.5.0 or higher
   - If syncing versions, bump all to 1.8.0 or 2.0.0

### Files to Update

If syncing versions:
- [ ] config.py (Python desktop)
- [ ] flutter_app/pubspec.yaml (Android)
- [ ] README.md (documentation)
- [ ] CHANGELOG.md (version history)

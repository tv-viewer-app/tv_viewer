# Android Review - Quick Reference Card

## 🚨 CRITICAL ACTIONS (DO FIRST!)

### 1. Generate Release Keystore (ONE TIME - 30 min)
```bash
keytool -genkey -v -keystore C:\keys\tv-viewer-upload-keystore.jks \
  -keyalg RSA -keysize 2048 -validity 10000 -alias upload
```
**SAVE PASSWORD SECURELY!** You'll need it for every release.

### 2. Configure Signing (5 min)
```bash
cd android
copy key.properties.example key.properties
# Edit key.properties with your keystore details
```

### 3. Test Release Build (30 min)
```bash
flutter build apk --release
flutter install --release
# Test thoroughly!
```

---

## 📚 Documentation Quick Access

| Document | Purpose | Time to Read |
|----------|---------|--------------|
| **START_HERE.md** | Overview & next steps | 5 min |
| **ANDROID_REVIEW_SUMMARY.md** | Executive summary | 10 min |
| **QUICK_START_ANDROID_FIXES.md** | Implementation guide | 1-2 hours |
| **ANDROID_REVIEW_RECOMMENDATIONS.md** | Full technical details | Reference |
| **CHANGES.md** | What was changed | 10 min |

---

## ✅ What's Already Fixed

| Issue | Status | Notes |
|-------|--------|-------|
| ProGuard rules | ✅ FIXED | File created, no crashes |
| AndroidManifest config | ✅ FIXED | Wake lock, PiP, players added |
| Build optimizations | ✅ FIXED | Gradle performance improved |
| External player service | ✅ FIXED | 6+ players supported |
| minSdk compatibility | ✅ FIXED | Lowered to 21 (99%+ devices) |
| .gitignore | ✅ FIXED | Keys won't be committed |

---

## ⚠️ What You Need to Do

| Task | Priority | Time | Guide |
|------|----------|------|-------|
| Generate keystore | 🔴 CRITICAL | 30 min | START_HERE.md |
| Add wakelock_plus | 🟠 HIGH | 10 min | QUICK_START.md §3 |
| Update player code | 🟠 HIGH | 15 min | QUICK_START.md §4 |
| Add dependencies | 🟡 MEDIUM | 5 min | pubspec_RECOMMENDED.yaml |
| Test on devices | 🟡 MEDIUM | 2 hours | QUICK_START.md §Testing |

---

## 🔧 Build Commands Cheat Sheet

```bash
# Debug (development)
flutter build apk --debug

# Release (after keystore setup)
flutter build apk --release

# Release with obfuscation
flutter build apk --release --obfuscate --split-debug-info=build/debug-info

# App Bundle for Play Store
flutter build appbundle --release

# Split by ABI (smaller)
flutter build apk --release --split-per-abi
```

---

## 📦 Dependencies to Add

```yaml
dependencies:
  wakelock_plus: ^1.1.4          # Screen wake lock
  android_intent_plus: ^4.0.3    # External players
  cached_network_image: ^3.3.1   # Image caching
  connectivity_plus: ^5.0.2      # Network detection
```

Run: `flutter pub get`

---

## 🧪 Testing Checklist

### Release Build Tests
- [ ] App launches successfully
- [ ] Channels load
- [ ] Video plays
- [ ] Screen stays on during playback
- [ ] VLC/MX Player opens correctly
- [ ] Images load and cache
- [ ] No crashes
- [ ] APK size < 50 MB

### Device Tests
- [ ] Android 14 (API 34)
- [ ] Android 10 (API 29)
- [ ] Android 7 (API 24)
- [ ] Android 5/6 (API 21-23)

---

## 📊 Expected Results

### Before
- ❌ Debug keystore in release
- ❌ ProGuard crashes
- ❌ Screen turns off
- ⚠️ 2 external players
- ⚠️ minSdk 24 (95% devices)
- ⚠️ ~50 MB APK

### After
- ✅ Proper release signing
- ✅ ProGuard working
- ✅ Screen stays on
- ✅ 6+ external players
- ✅ minSdk 21 (99%+ devices)
- ✅ ~35-40 MB APK

---

## 🚨 Common Issues & Fixes

### Build fails with signing error
→ Check `android/key.properties` exists and paths are correct

### Release APK crashes
→ Check ProGuard rules (already fixed)

### External players don't open
→ Use new ExternalPlayerService (already created)

### Screen turns off during playback
→ Add wakelock_plus and implement (see QUICK_START.md §3)

---

## 📞 Get Help

1. Check **START_HERE.md** first
2. Implementation issues → **QUICK_START_ANDROID_FIXES.md**
3. Technical details → **ANDROID_REVIEW_RECOMMENDATIONS.md**
4. What changed → **CHANGES.md**

---

## ⏱️ Timeline

- **Critical fixes**: 1-2 hours
- **Full implementation**: 1-2 days  
- **Testing**: 1 day
- **Total**: 3-4 days

---

## 🎯 Success Criteria

✅ You're production-ready when:
- Release APK builds with proper signing
- All features work in release mode
- Screen stays on during playback
- External players work reliably
- Tested on multiple Android versions
- Keystore backed up securely

---

**Review Date**: 2024  
**Status**: ⚠️ Action Required - See START_HERE.md  
**Next Step**: Generate release keystore (30 min)

---

## 🚀 Quick Start (30 Seconds)

```bash
# 1. Open START_HERE.md
start START_HERE.md

# 2. Or jump straight to implementation
start QUICK_START_ANDROID_FIXES.md
```

**THE END - You're ready to start!** 🎉

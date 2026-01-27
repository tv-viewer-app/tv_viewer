[app]
# App name and metadata
title = TV Viewer
package.name = tvviewer
package.domain = com.tvviewer

# Source code
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

# Application requirements - simplified for compatibility
requirements = python3,kivy==2.2.1,aiohttp,certifi,charset-normalizer,idna,multidict,yarl,async-timeout,frozenlist,aiosignal

# Android SDK/NDK versions
android.api = 33
android.minapi = 26
android.ndk = 25b
android.sdk = 33

# Android architecture (arm64-v8a for Samsung Galaxy S24 Ultra)
android.archs = arm64-v8a

# Permissions
android.permissions = INTERNET, ACCESS_NETWORK_STATE

# App orientation
orientation = portrait

# Fullscreen
fullscreen = 0

# Version
version = 1.4.2

# Android specific
android.accept_sdk_license = True
android.enable_androidx = True

# Release configuration
android.release_artifact = apk

# Bootstrap - sdl2 is default for Kivy
p4a.bootstrap = sdl2

# Use specific p4a version for stability
p4a.branch = master

# Log level (2 = verbose for debugging)
log_level = 2

[buildozer]
# Build output directory
build_dir = ./.buildozer

# Log file
log_filename = buildozer.log

# Warn on root
warn_on_root = 1

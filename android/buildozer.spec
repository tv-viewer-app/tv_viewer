[app]
# App name and metadata
title = TV Viewer
package.name = tvviewer
package.domain = com.tvviewer

# Source code
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

# Application requirements
requirements = python3,kivy,aiohttp,certifi

# Android SDK/NDK versions
android.api = 33
android.minapi = 26
android.ndk = 25b
android.sdk = 33

# Android architecture (arm64-v8a for Samsung Galaxy S24 Ultra)
android.archs = arm64-v8a, armeabi-v7a

# Permissions
android.permissions = INTERNET, ACCESS_NETWORK_STATE, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# App orientation (landscape + portrait)
orientation = portrait

# Fullscreen
fullscreen = 0

# Version
version = 1.4.1

# Android specific
android.accept_sdk_license = True
android.enable_androidx = True

# Release configuration
android.release_artifact = apk

# Java heap size for building
android.gradle_dependencies =

# Optimization
android.allow_backup = True

# Bootstrap
p4a.bootstrap = sdl2

# Branch
p4a.branch = master

# Log level
log_level = 2

[buildozer]
# Build output directory
build_dir = ./.buildozer

# Log file
log_filename = buildozer.log

# Warn on root
warn_on_root = 1

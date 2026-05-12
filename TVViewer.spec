# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for TV Viewer Windows build.

Hardening (#190, #200, #201):
- Excludes AV-flagged libs (zeroconf, pychromecast, PIL._avif, PIL._webp).
- Bundles customtkinter theme JSONs (otherwise OSD invisibility bug v2.9.4).
- When BUNDLE_LIBVLC_DIR env var points at an extracted VLC install, ships
  libvlc.dll/libvlccore.dll + plugins/ inside the EXE so the app runs on a
  clean Windows install with NO VLC prerequisite.
- upx=False everywhere — UPX-compressed binaries are a strong AV trigger.
"""
import os
from PyInstaller.utils.hooks import collect_data_files

# -- Defender / dependency hardening -----------------------------------------
binaries = []
datas = [
    ('config.py', '.'),
    ('channels.json', '.'),
    ('tv_viewer.ico', '.'),
]
# customtkinter assets are not auto-collected — without these, theme JSONs
# are missing at runtime and the OSD widget renders invisible (#v2.9.4 bug).
datas += collect_data_files('customtkinter')

# -- Optional libvlc bundling (#200) -----------------------------------------
# CI sets BUNDLE_LIBVLC_DIR=$GITHUB_WORKSPACE\vlc-portable so the EXE is
# self-contained and works on a clean Windows install. Path layout expected:
#   <BUNDLE_LIBVLC_DIR>\libvlc.dll
#   <BUNDLE_LIBVLC_DIR>\libvlccore.dll
#   <BUNDLE_LIBVLC_DIR>\plugins\...
_libvlc_dir = os.environ.get('BUNDLE_LIBVLC_DIR', '').strip()
if _libvlc_dir and os.path.isdir(_libvlc_dir):
    for fname in ('libvlc.dll', 'libvlccore.dll'):
        fp = os.path.join(_libvlc_dir, fname)
        if os.path.isfile(fp):
            binaries.append((fp, '.'))
    plugins = os.path.join(_libvlc_dir, 'plugins')
    if os.path.isdir(plugins):
        datas.append((plugins, 'plugins'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        'vlc',
        'aiohttp',
        'asyncio',
        'tkinter',
        'tkinter.ttk',
        'customtkinter',
        'customtkinter.windows',
        'customtkinter.windows.widgets',
        'json',
        'threading',
        'queue',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL._tkinter_finder',
        'PIL._imagingtk',
        'ui.logo_manager',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Heavy data-science deadweight
        'matplotlib', 'numpy', 'pandas', 'scipy', 'cv2',
        'tensorflow', 'torch', 'sklearn', 'ttkbootstrap',
        # AV-flagged + optional features (cast/mDNS) — guarded by try/except
        # in ui/player_window.py so omitting them is safe (#190)
        'pychromecast', 'casttube', 'zeroconf',
        'google.protobuf', 'google',
        # Pillow plugins the app never uses; _avif.pyd is a known Defender
        # false-positive trigger (#190)
        'PIL._avif', 'PIL._webp', 'PIL._imagingcms',
        'PIL.ImageCms', 'PIL.AvifImagePlugin', 'PIL.WebPImagePlugin',
        # Stdlib test scaffolding
        'test', 'tests', 'unittest', 'pydoc_data',
        'distutils.tests', 'lib2to3', 'idlelib', 'turtle', 'turtledemo',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TVViewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                # NEVER enable — UPX-packed EXEs are AV-flagged
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='tv_viewer.ico',
    version='version_info.txt' if os.path.isfile('version_info.txt') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='TVViewer',
)

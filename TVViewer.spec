# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('config.py', '.'), ('channels.json', '.'), ('tv_viewer.ico', '.')],
    hiddenimports=['vlc', 'aiohttp', 'asyncio', 'tkinter', 'tkinter.ttk', 'json', 'threading', 'queue', 'pychromecast', 'zeroconf', 'PIL', 'PIL.Image', 'PIL.ImageTk', 'PIL._tkinter_finder', 'PIL._imagingtk', 'ui.logo_manager'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'cv2', 'tensorflow', 'torch', 'sklearn', 'ttkbootstrap'],
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
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='tv_viewer.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='TVViewer',
)

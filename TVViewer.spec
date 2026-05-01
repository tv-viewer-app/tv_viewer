# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('config.py', '.'), ('channels.json', '.'), ('tv_viewer.ico', '.')],
    hiddenimports=['vlc', 'aiohttp', 'asyncio', 'tkinter', 'tkinter.ttk', 'json', 'threading', 'queue', 'pychromecast', 'zeroconf', 'PIL', 'PIL.Image', 'PIL.ImageTk', 'PIL._tkinter_finder', 'PIL._imagingtk'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'cv2', 'tensorflow', 'torch', 'sklearn'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TVViewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['python312.dll', 'vcruntime140.dll', 'vcruntime140_1.dll'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

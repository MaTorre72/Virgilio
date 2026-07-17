# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


CONNECTOR_DIR = Path(SPECPATH).parent
PAYLOAD_DIR = CONNECTOR_DIR / "build-output" / "dist" / "Caronte"

a = Analysis(
    [str(CONNECTOR_DIR / "installer" / "caronte_installer.py")],
    pathex=[str(CONNECTOR_DIR / "installer")],
    binaries=[],
    datas=[(str(PAYLOAD_DIR), "payload/Caronte")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="CaronteSetup",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

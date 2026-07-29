# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path


CONNECTOR_DIR = Path(SPECPATH).parent
PAYLOAD_DIR = Path(os.environ.get("CARONTE_PAYLOAD_DIR", CONNECTOR_DIR / "build-output" / "dist" / "Caronte"))
INSTALLER_NAME = os.environ.get("CARONTE_INSTALLER_BASENAME", "CaronteSetup")
if not (PAYLOAD_DIR / "Caronte.exe").is_file():
    raise ValueError("CARONTE_PAYLOAD_DIR does not contain Caronte.exe")

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
    name=INSTALLER_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

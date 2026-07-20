# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path


PROJECT_DIR = Path(SPECPATH).parent
SOURCE_DIR = PROJECT_DIR / "src"
OAUTH_CLIENT_PATH = os.environ.get("CARONTE_GOOGLE_OAUTH_CLIENT_PATH", "").strip()
BUILD_MANIFEST_PATH = os.environ.get("CARONTE_BUILD_MANIFEST_PATH", "").strip()
if not BUILD_MANIFEST_PATH or not Path(BUILD_MANIFEST_PATH).is_file():
    raise ValueError("CARONTE_BUILD_MANIFEST_PATH must identify the generated manifest")
BUILD_DATAS = [(BUILD_MANIFEST_PATH, "resources")]
if OAUTH_CLIENT_PATH:
    oauth_client = Path(OAUTH_CLIENT_PATH)
    if not oauth_client.is_file() or oauth_client.name != "google_oauth_client.json":
        raise ValueError("Google OAuth input must be google_oauth_client.json")
    BUILD_DATAS.append((str(oauth_client), "resources"))

a = Analysis(
    [str(SOURCE_DIR / "virgilio_connector" / "build_entry.py")],
    pathex=[str(SOURCE_DIR)],
    binaries=[],
    datas=BUILD_DATAS,
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
    [],
    exclude_binaries=True,
    name="Caronte",
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Caronte",
)

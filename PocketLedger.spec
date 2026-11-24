# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller onedir spec for the Pocket Ledger Windows release."""

from pathlib import Path

ROOT = Path(SPECPATH).resolve()

datas = [
    (str(ROOT / "icons" / "PC.ico"), "icons"),
    (str(ROOT / "icons" / "PC.svg"), "icons"),
    (str(ROOT / "icons" / "Mobile.svg"), "icons"),
    (str(ROOT / "importers" / "rules.json"), "importers"),
]

hiddenimports = [
    "release_paths",
    "version",
    "database",
    "migrations",
    "importers",
    "importers.csv_parser",
    "importers.dedupe",
    "importers.service",
    "sync.identity",
    "sync.store",
    "ui.accounts",
    "ui.dashboard",
    "ui.import_csv",
    "ui.models",
    "ui.settings",
    "ui.theme",
    "ui.transactions",
    "ui.workers",
    "utils.calculations",
    "utils.currencies",
    "utils.formatting",
    "utils.money",
]

a = Analysis(
    [str(ROOT / "desktop_app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PocketLedger",
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
    icon=[str(ROOT / "icons" / "PC.ico")],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="PocketLedger",
)

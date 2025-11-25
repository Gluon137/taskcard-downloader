# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os

block_cipher = None

# Note: Chromium will be copied manually after build due to code signing issues
datas = []

a = Analysis(
    ['taskcard_downloader_gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'playwright',
        'playwright.async_api',
        'reportlab',
        'reportlab.pdfgen',
        'reportlab.lib.pagesizes',
        'reportlab.lib.styles',
        'reportlab.lib.units',
        'reportlab.platypus',
        'PyPDF2',
        'requests',
        'tkinter',
        'asyncio',
        'tempfile',
        'pathlib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TaskcardDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TaskcardDownloader',
)

app = BUNDLE(
    coll,
    name='TaskcardDownloader.app',
    icon=None,
    bundle_identifier='com.taskcard.downloader',
)

# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: one-file, windowed (no console) build of Fruit Box.
# Equivalent CLI:
#   pyinstaller --onefile --windowed --name FruitBox --icon assets/icon.ico ^
#               --add-data "assets;assets" main.py

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],   # fonts + sounds + icon, unpacked to sys._MEIPASS/assets
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'numpy'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FruitBox',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,                  # --windowed
    icon='assets/icon.ico',
)

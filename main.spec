# -*- mode: python ; coding: utf-8 -*-


import os
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.building.build_main import Analysis, PYZ, EXE

from config import config

plotly_datas = collect_data_files('plotly', include_py_files=False)

name_of_exe = config.get("exe",{}).get("name_of_python_exe_setup","server_dashboard-x86_64-pc-windows-msvc.exe")

a = Analysis(
    ['dashboard\\root.py'],
    pathex=[],
    binaries=[],
    datas=plotly_datas ,    
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
    name=name_of_exe,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

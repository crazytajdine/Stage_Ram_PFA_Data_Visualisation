import os
import platform
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.building.build_main import Analysis, PYZ, EXE

from config import config

# ---------------------------------------------------------------------------
# Generic settings
# ---------------------------------------------------------------------------
ROOT_SCRIPT = os.path.join("dashboard", "root.py")
PLOTLY_DATAS = collect_data_files("plotly", include_py_files=False)
SYSTEM = platform.system().lower()  # 'windows', 'darwin', 'linux', etc.

# Default executable names per platform. You can override them in config.py
# via config['exe']['name_windows' | 'name_macos' | 'name_linux']
DEFAULT_EXE_NAMES = {
    "windows": "-x86_64-pc-windows-msvc",
    "darwin": "-universal2-macos",
    "linux": "-x86_64-linux",
}

NAME_OF_EXE = config.get("exe", {}).get(
    "name_of_python_exe", "server_dashboard"
) + DEFAULT_EXE_NAMES.get(SYSTEM, "")

# Fallback to empty string if not found
# ---------------------------------------------------------------------------
# PyInstaller build blocks
# ---------------------------------------------------------------------------

a = Analysis(
    [ROOT_SCRIPT],
    pathex=[],
    binaries=[],
    datas=PLOTLY_DATAS,
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
    [],  # icon resources go here (same as your original spec)
    name=NAME_OF_EXE,
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

import os
import platform
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE


from dashboard.configurations.config import get_base_config, config_path

# ---------------------------------------------------------------------------
# Generic settings
# ---------------------------------------------------------------------------
config = get_base_config()
ROOT_SCRIPT = os.path.join("dashboard", "root.py")
PLOTLY_DATAS = collect_data_files("plotly", include_py_files=False)
FASTEXCEL_DATAS = collect_data_files("fastexcel", include_py_files=False)
hiddenimports = [*collect_submodules("fastexcel")]


SYSTEM = platform.system().lower()  # 'windows', 'darwin', 'linux', etc.


NAME_OF_EXE = config.get("exe", {}).get("name_of_python_exe", "server_dashboard")

datas = PLOTLY_DATAS + FASTEXCEL_DATAS + [(config_path, "configurations/")]


# Fallback to empty string if not found
# ---------------------------------------------------------------------------
# PyInstaller build blocks
# ---------------------------------------------------------------------------


a = Analysis(
    [ROOT_SCRIPT],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=2, 
)

pyz = PYZ(a.pure,optimize=2)

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

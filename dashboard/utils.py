# dashboard/utils.py
import os
from typing import Optional
from config import get_config_dir, config, load_config, save_config

# Global configuration management
name_config = config.get("config", {}).get("config_data_name", "config_data.toml")
dir_main_config = get_config_dir()
path_config = os.path.join(dir_main_config, name_config)
config_data = load_config(path_config)

# Global variables for configuration state
path_to_excel = config_data.get("path_to_excel", "")
auto_refresh = config_data.get("auto_refresh", True)
modification_date = config_data.get("modification_date", None)

def get_path_to_excel():
    return path_to_excel

def is_auto_refresh_enabled():
    return auto_refresh

def update_path_to_excel(new_path: str) -> tuple[bool, str]:
    global config_data, path_to_excel
    
    if not new_path:
        return False, "Path cannot be empty."
    
    if not os.path.exists(new_path):
        return False, "The excel file doesn't exists."
    
    if not os.path.isfile(new_path):
        return False, "The Path you provided is not for a file make sure it ends with '.excel' or any other valid format for excel."
    
    # Update global state
    path_to_excel = new_path
    config_data["path_to_excel"] = new_path
    save_config(path_config, config_data)
    
    return True, "Loaded The File successfully."

def toggle_auto_refresh() -> bool:
    global config_data, auto_refresh
    
    auto_refresh = not auto_refresh
    config_data["auto_refresh"] = auto_refresh
    save_config(path_config, config_data)
    
    print(f"Auto refresh set to: {auto_refresh}")
    return auto_refresh

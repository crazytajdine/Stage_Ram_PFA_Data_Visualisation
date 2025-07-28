import os
from typing import Any
from platformdirs import user_config_dir
import toml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(BASE_DIR, "config.toml")


def save_config(path: str, config: dict[str, Any]):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w") as f:
        toml.dump(config, f)


def load_config(path: str) -> dict[str, Any]:

    print(f"Loading config from: {path}")

    if os.path.exists(path):
        with open(path, "r") as f:
            config = toml.load(f)
    else:
        config = {}
        print(f"Creating config in : {path}")
        with open(path, "w"):
            pass

    return config


config = load_config(config_path)

app_name = config.get("app", {}).get("app_name", "DashBoardRam")
auth = config.get("app", {}).get("auth", "StagePFA")


def get_config_dir():
    return user_config_dir(app_name, auth)


def get_page_visibility(page_key: str) -> bool:
    """Get visibility status for a specific page"""
    return config.get("pages", {}).get(page_key, True)


def set_page_visibility(page_key: str, visible: bool):
    """Set visibility status for a specific page"""
    global config
    if "pages" not in config:
        config["pages"] = {}
    config["pages"][page_key] = visible
    save_config(config_path, config)


def get_all_page_visibility() -> dict[str, bool]:
    """Get visibility status for all pages"""
    default_pages = {
        "dashboard": True,
        "analytics": True,
        "weekly": True,
        "performance_metrics": True
    }
    return config.get("pages", default_pages)


def update_page_visibility(page_settings: dict[str, bool]):
    """Update visibility settings for multiple pages"""
    global config
    if "pages" not in config:
        config["pages"] = {}
    config["pages"].update(page_settings)
    save_config(config_path, config)


os.makedirs(get_config_dir(), exist_ok=True)

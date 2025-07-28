import os
from typing import Any
from platformdirs import user_config_dir
import toml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(BASE_DIR, "config.toml")


def save_config(path: str, config: dict[str, Any]):

    os.makedirs(os.path.dirname(path), exist_ok=True)

    old_config = load_config(path)

    new_config = {**old_config, **config}

    with open(path, "w") as f:
        toml.dump(new_config, f)


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


def get_base_config() -> dict:
    return load_config(config_path)


config = get_base_config()

app_name = config.get("app", {}).get("app_name", "DashBoardRam")
auth = config.get("app", {}).get("auth", "StagePFA")


def get_config_dir_sys():
    return user_config_dir(app_name, auth)


name_config = config.get("config", {}).get("config_data_name", "config_data.toml")

config_path_sys = os.path.join(get_config_dir_sys(), name_config)


def get_user_config() -> dict:
    os.makedirs(get_config_dir_sys(), exist_ok=True)

    return load_config(config_path_sys)


def save_config_sys(updated_config: dict[str, Any]):

    save_config(updated_config, config_path_sys)

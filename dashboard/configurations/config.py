import os
from typing import Any
from platformdirs import user_config_dir
import toml


def save_config(path: str, config: dict[str, Any]) -> dict[str, Any]:

    os.makedirs(os.path.dirname(path), exist_ok=True)

    old_config = load_config(path)

    new_config = {**old_config, **config}
    print("saving :", new_config, "to :", path)
    with open(path, "w") as f:
        toml.dump(new_config, f)
    return new_config


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
    global config_path
    return load_config(config_path)


def get_config_dir_sys():
    global app_name, auth
    return user_config_dir(app_name, auth)


def load_user_config() -> dict[str, Any]:
    global config_path_sys

    os.makedirs(get_config_dir_sys(), exist_ok=True)

    return load_config(config_path_sys)


def get_user_config() -> dict[str, Any]:
    global config_user

    if not config_user:
        config_user = load_user_config()

    return config_user


def save_config_sys(updated_config: dict[str, Any]) -> dict[str, Any]:
    global config_user

    config_user = save_config(config_path_sys, updated_config)
    return config_user


# ------------------


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(BASE_DIR, "config.toml")


config = get_base_config()

app_name = config.get("app", {}).get("app_name", "DashBoardRam")
auth = config.get("app", {}).get("auth", "StagePFA")


name_config = config.get("config", {}).get("config_data_name", "config_data.toml")

config_path_sys = os.path.join(get_config_dir_sys(), name_config)


config_user = load_user_config()
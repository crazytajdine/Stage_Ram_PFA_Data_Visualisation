import os
from platformdirs import user_config_dir
import toml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(BASE_DIR, "config.toml")


config = {}
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        config = toml.load(f)

app_name  =config.get("app",{}).get("app_name","DashBoardRam")
auth = config.get("app",{}).get("auth","StagePFA")

def get_config_dir():
    return user_config_dir(app_name,auth)




os.makedirs(get_config_dir(), exist_ok=True)

import os
from typing import Any
from platformdirs import user_config_dir
import toml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(BASE_DIR, "config.toml")

def save_config(path:str,config:dict[str, Any]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, "w") as f:
        toml.dump(config, f)



def load_config(path:str)->dict[str, Any]:
    

    
    if os.path.exists(path):
        with open(path, "r") as f:
            config = toml.load(f)
    else:
        config = {} 
        print(f"Creating config in : {path}")
        with open(path,"w"):
            pass    
        
    return config



config = load_config(config_path)

app_name  =config.get("app",{}).get("app_name","DashBoardRam")
auth = config.get("app",{}).get("auth","StagePFA")

def get_config_dir():
    return user_config_dir(app_name,auth)


os.makedirs(get_config_dir(), exist_ok=True)

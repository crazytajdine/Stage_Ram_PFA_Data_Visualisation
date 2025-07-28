# dashboard/utils_dashboard/utils_preference.py

from configurations.config import get_user_config, save_config_sys
from configurations.nav_config import NAV_CONFIG

# load the same config dict

config = get_user_config()


def get_nav_preferences() -> dict[str, bool]:

    pages_cfg = config.get("pages", {})
    return {
        item.name: pages_cfg.get(item.name, item.show)
        for item in NAV_CONFIG
        if item.preference_show
    }


def set_page_visibility(pages: dict[str, bool]):
    updates = {}
    updates["pages"] = {}
    for page_key, visible in pages.items():
        updates["pages"][page_key] = visible

    save_config_sys(updates)

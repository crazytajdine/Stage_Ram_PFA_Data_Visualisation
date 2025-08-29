# dashboard/utils_dashboard/utils_preference.py

import logging
from typing import List

from configurations.config import get_user_config, save_config_sys
from configurations.nav_config import NAV_CONFIG


def load_preference():
    logging.info("Loading preference module...")


# load the same config dict
config = get_user_config()


def get_disabled_preferences() -> List[str]:
    logging.info("Retrieving navigation preferences from config")
    pages_cfg: dict[str, bool] = config.get("pages", {})

    prefs = []
    for name, enabled in pages_cfg.items():
        if not enabled:
            prefs.append(name)

    logging.debug("Navigation preferences retrieved: %s", prefs)
    return prefs


def get_nav_preferences() -> dict[str, bool]:
    logging.info("Retrieving navigation preferences from config")
    pages_cfg = config.get("pages", {})
    prefs = {
        item.name: pages_cfg.get(item.name, True)
        for item in NAV_CONFIG
        if item.preference_show
    }
    logging.debug("Navigation preferences retrieved: %s", prefs)
    return prefs


def set_page_visibility(pages: dict[str, bool]):
    global config
    logging.info("Setting page visibility preferences: %s", pages)
    updates = {"pages": {}}
    for page_key, visible in pages.items():
        updates["pages"][page_key] = visible

    config = save_config_sys(updates)
    logging.info("Configuration saved successfully")

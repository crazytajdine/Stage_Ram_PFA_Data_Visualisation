from typing import List, Tuple

from configurations.nav_config import NAV_CONFIG
from utils_dashboard.utils_preference import (
    get_disabled_preferences,
    get_nav_preferences,
)

from schemas.navbarItem import DATA_PAGE_TYPE, NavItemMeta


def get_all_metadata_pages_dynamic() -> List[NavItemMeta]:
    return [nav for nav in NAV_CONFIG]


def fetch_allowed_page_for_user(path_exists) -> list[NavItemMeta]:

    nav_config = NAV_CONFIG

    allowed_data_page_types: Tuple[DATA_PAGE_TYPE] = (
        "both",
        "data" if path_exists else "nodata",
    )
    disabled_pages = get_disabled_preferences()

    meta_list: list[NavItemMeta] = [
        item
        for item in nav_config
        if (item.type_data in allowed_data_page_types)
        and (item.name not in disabled_pages)
    ]

    return meta_list

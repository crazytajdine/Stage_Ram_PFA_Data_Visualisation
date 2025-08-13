from typing import Optional, Tuple
from configurations.config import get_user_config
from schemas.navbarItem import NavItemMeta, DATA_PAGE_TYPE, USER_PAGE_TYPE


from pages.home.metadata import metadata as home_metadata
from pages.analytics.metadata import metadata as tech_metadata
from pages.weekly.metadata import metadata as weekly_metadata
from pages.performance_metrics.metadata import metadata as perf_metrics_metadata
from pages.settings.metadata import metadata as settings_metadata
from pages.undefined.metadata import metadata as undefined_metadata
from pages.admin.metadata import metadata as admin_metadata
from pages.login.metadata import metadata as login_metadata

NAV_CONFIG = [
    home_metadata,
    tech_metadata,
    weekly_metadata,
    perf_metrics_metadata,
    admin_metadata,
    settings_metadata,
    undefined_metadata,
    login_metadata,
]


def get_page_visibility(page_key: str) -> Optional[bool]:
    config = get_user_config()

    return config.get("pages", {}).get(page_key, None)


def build_nav_items_meta(path_exists: bool, is_login: bool) -> list[NavItemMeta]:

    allowed_data_page_types: Tuple[DATA_PAGE_TYPE] = (
        "both",
        "data" if path_exists else "nodata",
    )
    allowed_user_page_types: Tuple[USER_PAGE_TYPE] = (
        "both",
        "user" if is_login else "guest",
    )
    meta_list: list[NavItemMeta] = [
        item
        for item in NAV_CONFIG
        if (item.type_data in allowed_data_page_types)
        and (item.type_user in allowed_user_page_types)
    ]

    results = []
    for item in meta_list:
        is_visible_user = get_page_visibility(item.name)

        if is_visible_user is None:
            is_visible_user = True

        if not is_visible_user:
            continue

        results.append(item)

    return results

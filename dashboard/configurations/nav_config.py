from typing import Optional
from configurations.config import get_user_config
from schemas.navbarItem import NavItemMeta


from pages.home.metadata import metadata as home_metadata
from pages.tech.metadata import metadata as tech_metadata
from pages.weekly.metadata import metadata as weekly_metadata
from pages.performance_metrics.metadata import metadata as perf_metrics_metadata
from pages.settings.metadata import metadata as settings_metadata
from pages.verify.metadata import metadata as verify_metadata

NAV_CONFIG = [
    home_metadata,
    tech_metadata,
    weekly_metadata,
    perf_metrics_metadata,
    settings_metadata,
]

NAV_CONFIG_VERIFY = [verify_metadata]


def get_page_visibility(page_key: str) -> Optional[bool]:
    config = get_user_config()

    return config.get("pages", {}).get(page_key, None)


def build_nav_items_meta(path_exists: bool) -> list[NavItemMeta]:

    meta_list: list[NavItemMeta] = NAV_CONFIG if path_exists else NAV_CONFIG_VERIFY
    results = []
    for item in meta_list:
        is_visible_user = get_page_visibility(item.name)

        if is_visible_user is None:
            is_visible_user = item.show

        if not is_visible_user and path_exists:
            continue

        results.append(item)

    return results

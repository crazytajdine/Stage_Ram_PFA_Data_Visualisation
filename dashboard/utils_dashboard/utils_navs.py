# dashboard/utils_dashboard/utils_navs.py

from typing import Any, Optional
from configurations.config import get_user_config
from configurations.nav_config import (
    NAV_CONFIG,
    NAV_CONFIG_VERIFY,
    NavItemMeta,
    NavItem,
)

from pages.home import page as home
from pages.tech import page as tech
from pages.weekly import page as weekly
from pages.performance_metrics import page as performance_metrics
from pages.settings import page as settings
from pages.verify import page as verify

# Map each key to its layout callable
PAGE_MAP: dict[str, Any] = {
    "Dashboard": home.layout,
    "Analytics": tech.layout,
    "Weekly": weekly.layout,
    "Performance Metrics": performance_metrics.layout,
    "Settings": settings.layout,
    "Verify": verify.layout,
}


def get_page_visibility(page_key: str) -> Optional[bool]:
    config = get_user_config()

    return config.get("pages", {}).get(page_key, None)


def build_nav_items(path_exists: bool) -> list[NavItem]:

    meta_list: list[NavItemMeta] = NAV_CONFIG if path_exists else NAV_CONFIG_VERIFY
    results = []
    for item in meta_list:
        is_visible_user = get_page_visibility(item.name)
        if is_visible_user is None:
            is_visible_user = item.show

        print(item.name, is_visible_user)
        if not is_visible_user:
            continue

        nav_item = NavItem(
            **item.model_dump(),
            page=PAGE_MAP[item.name],
        )
        results.append(nav_item)

    return results

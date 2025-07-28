# dashboard/utils_dashboard/utils_navs.py

from configurations.config import get_user_config
from configurations.nav_config import (
    NAV_CONFIG,
    NAV_CONFIG_VERIFY,
    NavItemMeta,
    NavItem,
)

# Import all pages here for the PAGE_MAP
from pages.home import page as home
from pages.tech import page as tech
from pages.weekly import page as weekly
from pages.performance_metrics import page as performance_metrics
from pages.settings import page as settings
from pages.verify import page as verify

# Map each key to its layout callable
PAGE_MAP: dict[str, callable] = {
    "dashboard": home.layout,
    "analytics": tech.layout,
    "weekly": weekly.layout,
    "performance_metrics": performance_metrics.layout,
    "settings": settings.layout,
    "verify": verify.layout,
}

# load and watch user config
config = get_user_config()


def get_page_visibility(page_key: str) -> bool:
    return config.get("pages", {}).get(page_key, True)


def build_nav_items(path_exists: bool) -> list[NavItem]:

    meta_list: list[NavItemMeta] = NAV_CONFIG if path_exists else NAV_CONFIG_VERIFY

    return [
        NavItem(
            name=meta.name,
            href=meta.href,
            page=PAGE_MAP[meta.name.lower().replace(" ", "_")],
            show=get_page_visibility(meta.name.lower().replace(" ", "_")),
            preference_show=meta.preference_show,
            preference=meta.preference,
        )
        for meta in meta_list
    ]

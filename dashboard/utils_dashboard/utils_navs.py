# dashboard/utils_dashboard/utils_navs.py
import logging

logging.info("Loading nav file...")
from typing import Any
from configurations.nav_config import (
    NAV_CONFIG,
    NAV_CONFIG_VERIFY,
    build_nav_items_meta,
    get_page_visibility,
)

from schemas.navbarItem import NavItem, NavItemMeta
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


def build_nav_items(path_exists: bool) -> list[NavItem]:
    logging.info("Building navigation items; path_exists=%s", path_exists)


    pages_meta = build_nav_items_meta(path_exists)

    results = [
        NavItem(**item.model_dump(), page=PAGE_MAP[item.name]) for item in pages_meta
    ]
    logging.info("Built %d navigation items", len(results))

    return results

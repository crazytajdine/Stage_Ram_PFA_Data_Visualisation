# dashboard/utils_dashboard/utils_navs.py
import logging

logging.info("Loading nav file...")
from typing import Any
from configurations.nav_config import (
    build_nav_items_meta,
)

from schemas.navbarItem import NavItem, NavItemMeta
from pages.home import page as home
from pages.tech import page as tech
from pages.weekly import page as weekly
from pages.performance_metrics import page as performance_metrics
from pages.settings import page as settings
from pages.undefined import page as undefined


from pages.home.metadata import metadata as home_metadata
from pages.tech.metadata import metadata as tech_metadata
from pages.weekly.metadata import metadata as weekly_metadata
from pages.performance_metrics.metadata import metadata as perf_metrics_metadata
from pages.settings.metadata import metadata as settings_metadata
from pages.undefined.metadata import metadata as undefined_metadata


# Map each key to its layout callable
PAGE_MAP: dict[str, Any] = {
    home_metadata.name: home.layout,
    tech_metadata.name: tech.layout,
    weekly_metadata.name: weekly.layout,
    perf_metrics_metadata.name: performance_metrics.layout,
    settings_metadata.name: settings.layout,
    undefined_metadata.name: undefined.layout,
}


def build_nav_items(path_exists: bool) -> list[NavItem]:
    logging.info("Building navigation items; path_exists=%s", path_exists)

    pages_meta = build_nav_items_meta(path_exists)

    results = [
        NavItem(**item.model_dump(), page=PAGE_MAP[item.name]) for item in pages_meta
    ]
    logging.info("Built %d navigation items", len(results))

    return results

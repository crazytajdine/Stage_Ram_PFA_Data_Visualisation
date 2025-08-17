# dashboard/utils_dashboard/utils_navs.py
import logging
from typing import Any, Optional
from utils_dashboard.utils_page import (
    fetch_allowed_page_for_user,
)

from schemas.navbarItem import NavItem

from pages.home import page as home, metadata as home_metadata
from pages.analytics import page as tech, metadata as tech_metadata
from pages.weekly import page as weekly, metadata as weekly_metadata
from pages.performance_metrics import (
    page as performance_metrics,
    metadata as perf_metrics_metadata,
)
from pages.settings import page as settings, metadata as settings_metadata
from pages.undefined import page as undefined, metadata as undefined_metadata
from pages.admin import page as admin, metadata as admin_metadata
from pages.login import page as login, metadata as login_metadata

# Map each key to its layout callable
PAGE_MAP: dict[str, Any] = {
    home_metadata.metadata.name: home.layout,
    tech_metadata.metadata.name: tech.layout,
    weekly_metadata.metadata.name: weekly.layout,
    perf_metrics_metadata.metadata.name: performance_metrics.layout,
    settings_metadata.metadata.name: settings.layout,
    undefined_metadata.metadata.name: undefined.layout,
    admin_metadata.metadata.name: admin.layout,
    login_metadata.metadata.name: login.layout,
}


def build_nav_items(path_exists: bool, user_id: Optional[int]) -> list[NavItem]:
    logging.info("Building navigation items; path_exists=%s", path_exists)

    pages_meta = fetch_allowed_page_for_user(path_exists, user_id)

    results = [
        NavItem(**item.model_dump(), page=PAGE_MAP[item.name]) for item in pages_meta
    ]
    logging.info("Built %d navigation items", len(results))

    return results

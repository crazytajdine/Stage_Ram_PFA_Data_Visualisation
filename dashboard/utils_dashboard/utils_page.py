from typing import List, Optional

from sqlalchemy import Tuple
from configurations.nav_config import NAV_CONFIG
from configurations.config import get_user_config
from schemas.navbarItem import DATA_PAGE_TYPE, USER_PAGE_TYPE, NavItemMeta


def get_all_metadata_id_pages() -> List[int]:
    return [nav.id for nav in NAV_CONFIG]


def get_all_metadata_id_pages_dynamic() -> List[int]:
    return [nav.id for nav in NAV_CONFIG if nav.id is not None]


def get_page_visibility(page_key: str) -> Optional[bool]:
    config = get_user_config()

    return config.get("pages", {}).get(page_key, None)


def build_nav_items_meta(
    path_exists: bool, user_id: Optional[int]
) -> list[NavItemMeta]:
    nav_config = NAV_CONFIG
    if user_id is not None:
        from data_managers.database_manager import session_scope
        from services import user_service

        with session_scope(False) as session:
            pages = user_service.get_user_allowed_pages(user_id, session)
            id_pages = [page.id for page in pages]
            nav_config = [
                nav for nav in NAV_CONFIG if nav.id in id_pages or nav.id is None
            ]

    allowed_data_page_types: Tuple[DATA_PAGE_TYPE] = (
        "both",
        "data" if path_exists else "nodata",
    )
    allowed_user_page_types: Tuple[USER_PAGE_TYPE] = (
        "both",
        "user" if (user_id is not None) else "guest",
    )
    meta_list: list[NavItemMeta] = [
        item
        for item in nav_config
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

    print([meta.name for meta in meta_list])
    return results

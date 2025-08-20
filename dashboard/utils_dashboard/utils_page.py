from typing import List

from sqlalchemy import Tuple
from configurations.nav_config import NAV_CONFIG


from schemas.navbarItem import DATA_PAGE_TYPE, USER_PAGE_TYPE, NavItemMeta


def get_all_metadata_id_pages() -> List[int]:
    return [nav.id for nav in NAV_CONFIG]


def get_all_metadata_id_pages_dynamic(including_admin_pages: bool = True) -> List[int]:
    return [
        nav.id
        for nav in NAV_CONFIG
        if nav.id is not None
        if including_admin_pages or not nav.admin_page
    ]


def get_all_metadata_pages_dynamic() -> List[NavItemMeta]:
    return [nav for nav in NAV_CONFIG if nav.id is not None]


def fetch_allowed_page_for_user(path_exists, user_id) -> list[NavItemMeta]:

    nav_config = NAV_CONFIG

    if user_id is not None:

        from data_managers.database_manager import session_scope
        from services import page_service

        with session_scope(False) as session:
            role_pages = page_service.get_user_allowed_pages_with_preferences(
                user_id, session
            )

            id_pages = {role_page.page_id for role_page in role_pages}
            nav_config = [
                nav for nav in NAV_CONFIG if (nav.id in id_pages) or (nav.id is None)
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
    return meta_list


def get_allowed_pages_all(user_id: int):

    from data_managers.database_manager import session_scope
    from services import page_service

    with session_scope() as session:
        return page_service.get_user_allowed_pages_all(user_id, session)


def update_user_page_preferences(user_id: int, preferences: dict[int, bool]):
    """Update user page preferences. preferences should contain page IDs as keys and visibility as values (is enabled)."""
    from data_managers.database_manager import session_scope
    from services import page_service

    disabled_preferences = {
        page_id: not enabled for page_id, enabled in preferences.items()
    }

    with session_scope() as session:
        return page_service.update_user_page_preferences(
            user_id, disabled_preferences, session
        )

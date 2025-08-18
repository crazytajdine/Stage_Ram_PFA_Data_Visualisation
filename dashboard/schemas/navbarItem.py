from typing import Any, Literal, Optional
from pydantic import BaseModel

DATA_PAGE_TYPE = Literal["data", "nodata", "both"]
USER_PAGE_TYPE = Literal["guest", "user", "both"]


class NavItemMeta(BaseModel):
    id: Optional[int] = None
    name: str
    href: str
    title: Optional[str] = None
    show_navbar: bool = True
    show_filter: bool = True
    preference_show: bool = True
    update_on_data_change: bool = True
    admin_page: bool = False
    type_data: DATA_PAGE_TYPE = "both"
    type_user: USER_PAGE_TYPE = "both"


class NavItem(BaseModel):
    id: Optional[int] = None
    name: str
    href: str
    title: Optional[str] = None
    page: Any
    show_navbar: bool = True
    show_filter: bool = True
    preference_show: bool = True
    update_on_data_change: bool = True
    admin_page: bool = False
    data_exists: DATA_PAGE_TYPE = "both"
    user_login: USER_PAGE_TYPE = "both"

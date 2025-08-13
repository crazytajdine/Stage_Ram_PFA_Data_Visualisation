from typing import Any, Literal
from pydantic import BaseModel

DATA_PAGE_TYPE = Literal["data", "nodata", "both"]
USER_PAGE_TYPE = Literal["guest", "user", "both"]


class NavItemMeta(BaseModel):
    name: str
    href: str
    title: str
    show_navbar: bool = True
    show_filter: bool = True
    preference_show: bool = True
    type_data: DATA_PAGE_TYPE = "both"
    type_user: USER_PAGE_TYPE = "both"


class NavItem(BaseModel):
    name: str
    href: str
    title: str
    page: Any
    show_navbar: bool = True
    show_filter: bool = True
    preference_show: bool = True
    data_exists: DATA_PAGE_TYPE = "both"
    user_login: USER_PAGE_TYPE = "both"

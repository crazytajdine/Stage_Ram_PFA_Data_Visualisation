from typing import Any, Literal, Optional
from pydantic import BaseModel

DATA_PAGE_TYPE = Literal["data", "nodata", "both"]
USER_PAGE_TYPE = Literal["guest", "user", "both"]


class NavItemMeta(BaseModel):
    name: str
    href: str
    title: Optional[str] = None
    show_navbar: bool = True
    show_filter: bool = True
    preference_show: bool = True
    update_on_data_change: bool = True
    type_data: DATA_PAGE_TYPE = "both"


class NavItem(BaseModel):
    name: str
    href: str
    title: Optional[str] = None
    page: Any
    show_navbar: bool = True
    show_filter: bool = True
    preference_show: bool = True
    update_on_data_change: bool = True
    data_exists: DATA_PAGE_TYPE = "both"

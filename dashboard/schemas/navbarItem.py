from typing import Any
from pydantic import BaseModel


class NavItemMeta(BaseModel):
    name: str
    href: str
    title: str
    show: bool = True
    show_filter: bool = True
    preference_show: bool = True


class NavItem(BaseModel):
    name: str
    href: str
    title: str
    page: Any
    show: bool = True
    show_filter: bool = True
    preference_show: bool = True

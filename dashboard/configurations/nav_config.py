from pydantic import BaseModel
from typing import Any


class NavItemMeta(BaseModel):
    name: str
    href: str
    show: bool = True
    preference_show: bool = True
    preference: bool = True


class NavItem(BaseModel):
    name: str
    href: str
    page: Any
    show: bool = True
    preference_show: bool = True
    preference: bool = True


NAV_CONFIG = [
    NavItemMeta(
        name="Dashboard",
        href="/",
    ),
    NavItemMeta(name="Analytics", href="/analytics"),
    NavItemMeta(
        name="Weekly",
        href="/weekly",
    ),
    NavItemMeta(
        name="Performance Metrics",
        href="/Performance_Metrics",
    ),
    NavItemMeta(name="Settings", href="/settings", preference_show=False),
]
NAV_CONFIG_VERIFY = [
    NavItemMeta(name="Verify", href="/verify", preference_show=False),
]

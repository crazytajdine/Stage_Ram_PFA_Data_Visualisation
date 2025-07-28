from pydantic import BaseModel
from typing import Any


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


NAV_CONFIG = [
    NavItemMeta(name="Dashboard", href="/", title="Performance Metrics"),
    NavItemMeta(name="Analytics", href="/analytics", title="Performance Metrics"),
    NavItemMeta(name="Weekly", href="/weekly", title="Performance Metrics"),
    NavItemMeta(
        name="Performance Metrics",
        href="/Performance_Metrics",
        title="Performance Metrics",
    ),
    NavItemMeta(
        name="Settings",
        href="/settings",
        preference_show=False,
        show_filter=False,
        title="Performance Metrics",
    ),
]
NAV_CONFIG_VERIFY = [
    NavItemMeta(
        name="Verify",
        href="/verify",
        preference_show=False,
        title="Performance Metrics",
    ),
]

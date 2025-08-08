from dash import Input, Output, dcc, html
from configurations.nav_config import build_nav_items_meta
from components.title import ID_MAIN_TITLE
from excel_manager import ID_PATH_STORE, add_watcher_for_data_status, path_exists
from server_instance import get_app

from components.filter import ID_FILTER_CONTAINER

import dash_bootstrap_components as dbc
import logging

from dash import html


app = get_app()
# ← re-use the single app created earlier

navbar = dbc.Navbar(
    dbc.Container(
        [
            # ─── Left: Logo + Title ─────────────────────────────
            dbc.NavbarBrand(
                [
                    html.Img(
                        src=app.get_asset_url("logo_ram-2.png"),
                        id="ram-logo",
                        style={"height": "70px"},  # tweak as needed
                    ),
                    html.Span("Delay Dashboard", className="navbar-title"),
                ],
                className="d-flex align-items-center",
                href="/",
            ),
            # ─── Right: Settings button + User dropdown ──────────
            html.Div(
                [
                    dbc.Nav(
                        id="navbar",  # your @app.callback writes into here
                        navbar=True,
                        className="nav-tabs mx-auto",
                    ),
                    dbc.Button("Logout", color="secondary"),
                ],
                className="d-flex align-items-center",
            ),
        ],
        fluid=True,
    ),
    color="dark",
    dark=True,
    className="py-2",
)
# ---------- ROOT LAYOUT ----------
layout = dbc.Container([navbar], class_name="p-0", fluid=True)


def add_callback():

    @app.callback(
        Output("navbar", "children"),
        Output(ID_FILTER_CONTAINER, "style"),
        Output(ID_MAIN_TITLE, "children"),
        # inputs
        Input("url", "pathname"),
        add_watcher_for_data_status(),
    )
    def update_layout(pathname, _):
        does_path_exists = path_exists()
        nav_items = build_nav_items_meta(does_path_exists)

        logging.info("Nav items metadata: %s", [(i.name, i.show) for i in nav_items])

        navbar = []
        title = ""
        show_filter = False

        for nav_item in nav_items:
            is_selected = pathname == nav_item.href

            if is_selected:
                show_filter = nav_item.show_filter
                title = nav_item.title
            logging.debug(
                "Selected nav item: %s, show_filter: %s",
                nav_item.name,
                nav_item.show_filter,
            )
            if not nav_item.show:
                continue

            navbar.append(
                dbc.NavItem(
                    dbc.NavLink(
                        nav_item.name,
                        href=nav_item.href,
                        active=is_selected,
                    )
                )
            )

        show_filter = {} if show_filter else {"display": "none"}
        logging.info("Navbar updated with %d items", len(navbar))
        return navbar, show_filter, title

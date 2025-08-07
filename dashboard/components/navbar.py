from dash import Input, Output, dcc
from configurations.nav_config import build_nav_items_meta
from components.title import ID_MAIN_TITLE
from excel_manager import ID_PATH_STORE, add_watcher_for_data_status, path_exists
from server_instance import get_app

from components.filter import ID_FILTER_CONTAINER

import dash_bootstrap_components as dbc
from dash import html
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [INFO] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = get_app()

layout = html.Div(
    [
        dbc.Nav(
            className="justify-content-center nav-tabs",
            id="navbar",
        ),
        dcc.Location(id="url"),
    ]
)


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

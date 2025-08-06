from dash import Input, Output, dcc
from configurations.nav_config import build_nav_items_meta
from components.title import ID_FILTER_TITLE
from excel_manager import ID_PATH_STORE, path_exits
from server_instance import get_app

from pages.settings.page import ID_TRIGGER_PARAMS_CHANGE_NAVBAR
from components.filter import ID_FILTER_CONTAINER

import dash_bootstrap_components as dbc
from dash import html


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
        Output(ID_FILTER_TITLE, "children"),
        # input
        Input("url", "pathname"),
        Input(ID_PATH_STORE, "data"),
        Input(ID_TRIGGER_PARAMS_CHANGE_NAVBAR, "data", True),
    )
    def update_layout(pathname, _, n_clicks_settings):
        path_exists = path_exits()
        nav_items = build_nav_items_meta(path_exists)
        print("start navbar :", [(i.name, i.show) for i in nav_items])
        navbar = []
        title = ""
        show_filter = False

        for nav_item in nav_items:

            is_selected = pathname == nav_item.href

            if is_selected:
                show_filter = nav_item.show_filter
                title = nav_item.title

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
        return (navbar, show_filter, title)

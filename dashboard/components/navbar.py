from dash import Input, Output, dcc, html
from configurations.nav_config import build_nav_items_meta
from components.title import ID_FILTER_TITLE
from excel_manager import ID_PATH_STORE, path_exits
from server_instance import get_app

from pages.settings.page import ID_TRIGGER_PARAMS_CHANGE_NAVBAR
from components.filter import ID_FILTER_CONTAINER

import dash_bootstrap_components as dbc


app = get_app()
   # ← re-use the single app created earlier

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.Img(src=app.get_asset_url("logo_ram-2.png"),
                     id="ram-logo"),
            html.Span("Delay Dashboard",
                      className="navbar-title"),

            dbc.Nav(
                id="navbar",
                className="flex-grow-1 justify-content-center nav-tabs",
            ),

            # Icône utilisateur (on ajoute un menu au clic juste après)
            dbc.DropdownMenu(
                children=[
                    dbc.DropdownMenuItem("Profil", href="#"),
                    dbc.DropdownMenuItem("Déconnexion", href="#"),
                ],
                nav=True,
                in_navbar=True,
                label=html.I(className="bi bi-person-circle fs-3", id="user-icon"),
                toggle_style={"background": "transparent", "border": "none"},
                align_end=True, 
            ),
        ],
        fluid=True,
        className="align-items-center"
    ),
    color=None,              # enlève le fond noir opaque
    dark=True,
    fixed="top",
    className="shadow-sm glass-dark",   # <-- effet glass ici
)



# ---------- ROOT LAYOUT ----------
layout = html.Div(
    [
        navbar,
        dcc.Location(id="url"),      # keeps multipage routing
        html.Div(id="page-content"), # where page callbacks inject content
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

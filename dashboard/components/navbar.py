from dash import Input, Output, State, html, dcc
from server_instance import get_app


import dash_bootstrap_components as dbc

ID_STORE_LOADED_URL = "store_loaded_url"


app = get_app()


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
                    html.Span(
                        ["Delay", html.Br(), "Dashboard"], className="navbar-title"
                    ),
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
                        className="nav-tabs my-auto",
                    ),
                ],
                className="d-flex align-items-center ms-auto",
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


ID_URL = "url"
stores = [
    dcc.Store(ID_STORE_LOADED_URL),
    dcc.Location(id=ID_URL),
]


def add_output_url():
    return Output(ID_URL, "pathname")


def add_input_url():
    return Input(ID_URL, "pathname")


def add_state_url():
    return State(ID_URL, "pathname")


def add_output_loaded_url():
    return Output(ID_STORE_LOADED_URL, "data")


def add_input_loaded_url():
    return Input(ID_STORE_LOADED_URL, "data")


def add_state_loaded_url():
    return State(ID_STORE_LOADED_URL, "data")

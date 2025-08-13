from dash import html
from server_instance import get_app


import dash_bootstrap_components as dbc


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

import dash
from dash import html, dcc
from dash.dependencies import Input, Output

import dash_bootstrap_components as dbc

from server_instance import get_app

from excel_manager import path_to_excel


import dashboard.pages.home.page as home
import dashboard.pages.tech.page as tech
import dashboard.pages.verify.page as verify


app = get_app()


app.layout = html.Div(
    [
        # stores
        dcc.Store(id="path-store", data=path_to_excel),
        dcc.Store(id="data-store"),
        # Barre de navigation
        dbc.Nav(
            className="justify-content-center nav-tabs",
            id="navbar",
        ),
        # Contenu principal
        html.Div(id="page-content"),
        # Stockage pour suivre l'état du menu
        dcc.Location(id="url"),
    ]
)


def build_nav_items(path_exits: bool):
    if path_exits:

        nav_items = [
            {"name": "Dashboard", "href": "/", "page": home.layout},
            {"name": "Analytics", "href": "/analytics", "page": tech.layout},
            {"name": "Settings", "href": "/settings", "page": html.Div("Paramètres")},
        ]
    else:

        nav_items = [
            {
                "name": "verify",
                "href": "/",
                "page": verify.layout,
                "show": False,
            }
        ]

    return nav_items


@app.callback(
    Output("navbar", "children"),
    [Input("url", "pathname"), Input("path-store", "data")],
)
def update_navbar(pathname, path_exists):

    nav_items = build_nav_items(path_exists != "")

    return [
        dbc.NavItem(
            dbc.NavLink(
                nav_item["name"],
                href=nav_item["href"],
                active=pathname == nav_item["href"],
            )
        )
        for nav_item in nav_items
        if nav_item.get("show", True)
    ]


@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname"), Input("path-store", "data")],
)
def render_page(pathname, path_exists):

    nav_items = build_nav_items(path_exists != "")

    for nav_item in nav_items:
        if pathname == nav_item["href"]:
            return nav_item["page"]
    return html.Div("404: Page not found.")


if __name__ == "__main__":
    app.run(debug=True)

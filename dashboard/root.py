from dash import html, dcc
from dash.dependencies import Input, Output

import dash_bootstrap_components as dbc

from excel_manager import hookers as excel_hookers, add_callbacks
from server_instance import get_app


import pages.tech.page as tech
import pages.verify.page as verify
import pages.home.page as home
import pages.temporal.page as temporal
import pages.settings.page as settings
import pages.performance_metrics.page as performance_metrics

app = get_app()


app.layout = html.Div(
    [
        # hookers
        *excel_hookers,
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
            {"name": "Temporal", "href": "/temporal", "page": temporal.layout},
            {
                "name": "Performance Metrics",
                "href": "/Performance_Metrics",
                "page": performance_metrics.layout,
            },
            {"name": "Settings", "href": "/settings", "page": settings.layout},
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
    Output("page-content", "children"),
    [Input("url", "pathname"), Input("is-path-store", "data")],
)
def update_layout(pathname, path_exists):
    print(f"path_exists: {path_exists}")
    nav_items = build_nav_items(path_exists)
    print([i["name"] for i in nav_items])

    navbar = [
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

    page = html.Div("404: Page not found.")
    for nav_item in nav_items:
        if pathname == nav_item["href"]:
            page = nav_item["page"]
            break

    return navbar, page


add_callbacks()


if __name__ == "__main__":
    print("🔁 Launching Dash app...")

    app.run(debug=True, use_reloader=True)

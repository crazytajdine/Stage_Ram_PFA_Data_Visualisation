from dash import html, dcc
from dash.dependencies import Input, Output

import dash_bootstrap_components as dbc

from excel_manager import hookers as excel_hookers, add_callbacks, path_exits
from server_instance import get_app


from pages.tech import page as tech
from pages.verify import page as verify
from pages.home import page as home
from pages.weekly import page as weekly
from pages.settings import page as settings
from pages.performance_metrics import page as performance_metrics


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
            {"name": "Weekly", "href": "/weekly", "page": weekly.layout},
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
def update_layout(pathname, _):

    path_exists = path_exits()
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


def start_server():
    print("🔁 Starting Dash server…")
    app.run(debug=True, use_reloader=False, port=8050)


if __name__ == "__main__":
    print("🔁 Launching Dash app...")
    start_server()

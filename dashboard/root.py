import dash
from dash import html, dcc
from dash.dependencies import Input, Output

import dash_bootstrap_components as dbc

from dashboard.server_instance import get_app

from excel_manager import get_df, path_exits

app = get_app()


# Données pour les éléments de navigation
if path_exits():
    import dashboard.pages.home.page as home
    import dashboard.pages.tech.page as tech
    nav_items = [
        {"name": "Dashboard", "icon": "fas fa-home", "href": "/", "page": home.layout},
        {"name": "Analytics", "icon": "fas fa-chart-line", "href": "/analytics", "page": tech.layout},
        {"name": "Settings", "icon": "fas fa-cog", "href": "/settings", "page": html.Div("Paramètres")},
    ]
else:
    import dashboard.pages.verify.page as verify

    nav_items = [
        {
            "name": "verify",
            "icon": "fas fa-home",
            "href": "/",
            "page": verify.layout,
            "show": False,
        }
    ]

navbar = dbc.Nav(
    children=[
        dbc.NavItem(dbc.NavLink(nav_item["name"], href=nav_item["href"]))
        for nav_item in nav_items
        if nav_item.get("show", True)
    ],
    className="justify-content-center nav-tabs",
    id="navbar",
)


app.layout = html.Div(
    [
        # Barre de navigation
        navbar,
        # Contenu principal
        html.Div(id="page-content"),
        # Stockage pour suivre l'état du menu
        dcc.Location(id="url"),
    ]
)


@app.callback(Output("navbar", "children"), Input("url", "pathname"))
def update_navbar(pathname):

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


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page(pathname):
    for nav_item in nav_items:
        if pathname == nav_item["href"] :
            return nav_item["page"]


if __name__ == '__main__':
    app.run(debug=True)

from dash import html, dcc, callback, Output, Input, State
from dash.dependencies import Input, Output
import plotly.io as pio
import dash

import dash_bootstrap_components as dbc

from utils_dashboard.utils_navs import build_nav_items
from server_instance import get_app

from excel_manager import hookers as excel_hookers, add_callbacks, path_exits
from components.filter import layout as filter


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
        # Filters
        filter,
        # Contenu principal
        html.Div(id="page-content"),
        # Stockage pour suivre l'état du menu
        dcc.Location(id="url"),
    ]
)


@app.callback(
    Output("navbar", "children"),
    Output("page-content", "children"),
    [Input("url", "pathname"), Input("is-path-store", "data")],
)
def update_layout(pathname, _):
    path_exists = path_exits()
    print(f"path_exists: {path_exists}")

    nav_items = build_nav_items(path_exists)
    print([i.name for i in nav_items])
    navbar = [
        dbc.NavItem(
            dbc.NavLink(
                nav_item.name,
                href=nav_item.href,
                active=pathname == nav_item.href,
            )
        )
        for nav_item in nav_items
        if nav_item.show
    ]

    page = html.Div("404: Page not found.")
    for nav_item in nav_items:
        if pathname == nav_item.href:
            page = nav_item.page
            break

    return navbar, page


@callback(
    Output("download-chart-png", "data"),
    Input("btn-export-chart", "n_clicks"),
    State("codes-chart", "figure"),  # figure lives in pages.page.py
    prevent_initial_call=True,
)
def export_current_chart(_, fig_dict):
    if not fig_dict:
        return dash.no_update
    img_bytes = pio.to_image(fig_dict, format="png", scale=3)
    return dict(content=img_bytes, filename="codes-chart.png")


add_callbacks()


def start_server():
    print("🔁 Starting Dash server…")
    app.run(debug=True, use_reloader=True, port=8050)


if __name__ == "__main__":
    print("🔁 Launching Dash app...")
    start_server()

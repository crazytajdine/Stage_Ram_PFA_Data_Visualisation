from dash import html, dcc, Output, Input
from dash.dependencies import Input, Output
import plotly.io as pio
import dash

import dash_bootstrap_components as dbc

from server_instance import get_app

from excel_manager import hookers as excel_hookers, add_callbacks, path_exits
import components.filter as filter


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
        # Filters
        filter.layout,
        # Contenu principal
        html.Div(id="page-content"),
        # Stockage pour suivre l'état du menu
        dcc.Location(id="url"),
    ]
)


def build_nav_items(path_exists: bool):
    if path_exists:
        nav_items = [
            {
                "name": "Dashboard",
                "href": "/",
                "page": home.layout,
                "filter_title": "performance metrics",
            },
            {
                "name": "Analytics",
                "href": "/analytics",
                "page": tech.layout,
                "filter_title": "performance metrics",
            },
            {
                "name": "Weekly",
                "href": "/weekly",
                "page": weekly.layout,
                "filter_title": "performance metrics",
            },
            {
                "name": "Performance Metrics",
                "href": "/Performance_Metrics",
                "page": performance_metrics.layout,
                "filter_title": "performance metrics",
            },
            {
                "name": "Settings",
                "href": "/settings",
                "page": settings.layout,
                "filter": False,
            },
        ]
    else:
        nav_items = [
            {"name": "verify", "href": "/", "page": verify.layout, "show": False},
        ]

    return nav_items


@app.callback(
    Output("navbar", "children"),
    Output("page-content", "children"),
    Output(filter.ID_FILTER_CONTAINER, "style"),
    Output(filter.ID_FILTER_TITLE, "children"),
    [Input("url", "pathname"), Input("is-path-store", "data")],
)
def update_layout(pathname, _):

    path_exists = path_exits()
    print(f"path_exists: {path_exists}")
    nav_items = build_nav_items(path_exists)
    print([i["name"] for i in nav_items])
    title = "Filters"
    navbar = []
    for nav_item in nav_items:
        show = nav_item.get("show", True)
        if not show:
            continue

        is_active = pathname == nav_item["href"]
        if is_active:
            style_filter = (
                {"display": "none"} if not nav_item.get("filter", True) else {}
            )
            title = nav_item.get("filter_title", title)

        navbar.append(
            dbc.NavItem(
                dbc.NavLink(
                    nav_item["name"],
                    href=nav_item["href"],
                    active=is_active,
                )
            )
        )

    page = html.Div("404: Page not found.")
    for nav_item in nav_items:
        if pathname == nav_item["href"]:
            page = nav_item["page"]
            break

    return navbar, page, style_filter, title


# @callback(
#     Output("download-chart-png", "data"),
#     Input("btn-export-chart", "n_clicks"),
#     State("codes-chart", "figure"),  # figure lives in pages.page.py
#     prevent_initial_call=True,
# )
# def export_current_chart(_, fig_dict):
#     if not fig_dict:
#         return dash.no_update

#     img_bytes = pio.to_image(fig_dict, format="png", scale=3)
#     return dict(content=img_bytes, filename="codes-chart.png")


add_callbacks()


def start_server():
    print("🔁 Starting Dash server…")
    app.run(debug=True, use_reloader=True, port=8050)


if __name__ == "__main__":
    print("🔁 Launching Dash app...")
    start_server()

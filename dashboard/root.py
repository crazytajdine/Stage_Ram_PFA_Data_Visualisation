from dash import html, dcc, Output, Input, State
from dash.dependencies import Input, Output
import plotly.io as pio
import dash

from utils_dashboard.utils_navs import build_nav_items
from server_instance import get_app

from excel_manager import (
    ID_PATH_STORE,
    hookers as excel_hookers,
    add_callbacks as add_excel_manager_callback,
    path_exits,
)
from components.filter import (
    layout as filter_layout,
    add_callbacks as add_filter_callbacks,
)
from components.navbar import (
    layout as navbar_layout,
    add_callback as add_navbar_callback,
)

app = get_app()

app.layout = html.Div(
    [
        # hookers
        *excel_hookers,
        # Barre de navigation
        navbar_layout,
        # Filters
        filter_layout,
        # Contenu principal
        html.Div(id="page-content"),
        # Stockage pour suivre l'état du menu
    ]
)


@app.callback(
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


@app.callback(
    Output("page-content", "children"),
    [
        Input("url", "pathname"),
        Input(ID_PATH_STORE, "data"),
    ],
)
def update_content_page(pathname, _):
    path_exists = path_exits()
    nav_items = build_nav_items(path_exists)

    for nav_item in nav_items:

        is_selected = pathname == nav_item.href

        if is_selected:
            print("loading page")
            return nav_item.page

    return html.Div("404 Page Not Found")


add_excel_manager_callback()
add_filter_callbacks()
add_navbar_callback()


def start_server():
    print("🔁 Starting Dash server…")
    app.run(debug=True, use_reloader=False, port=8050)


if __name__ == "__main__":

    start_server()

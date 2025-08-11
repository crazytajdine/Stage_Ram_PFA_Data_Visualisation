from dash import html, Output, Input, State, dcc
from dash.dependencies import Input, Output
import logging
import plotly.io as pio
import dash

from configurations.config import get_base_config
from configurations.log_config import init_log
from utils_dashboard.utils_navs import build_nav_items
from server_instance import get_app, get_server

from utils_dashboard.utils_download import download_dash

from data_managers.excel_manager import (
    ID_PATH_STORE,
    add_watcher_for_data_status,
    add_callbacks as add_excel_manager_callbacks,
    hookers as excel_hookers,
    path_exists,
)
from data_managers.watcher_excel_dir import add_callbacks as add_watcher_excel
from components.filter import (
    layout as filter_layout,
    add_callbacks as add_filter_callbacks,
)
from components.navbar import (
    layout as navbar_layout,
    add_callback as add_navbar_callback,
)

from components.title import layout as tittle_layout

print("Loading server instance...")

app = get_app()
server = get_server()

app.layout = html.Div(
    [
        download_dash,
        # hookers
        *excel_hookers,
        # Barre de navigation
        navbar_layout,
        # Title
        tittle_layout,
        # Filters
        filter_layout,
        # Contenu principal
        html.Div(id="page-content"),
        # Stockage pour suivre l'état du menu
        dcc.Location(id="url"),
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
        add_watcher_for_data_status(),
    ],
)
def update_content_page(pathname, _):
    does_path_exists = path_exists()

    nav_items = build_nav_items(does_path_exists)
    logging.info("does path exist set to %s", does_path_exists)
    if not does_path_exists and nav_items:
        return nav_items[0].page

    for nav_item in nav_items:

        is_selected = pathname == nav_item.href

        if is_selected:
            print("loading page")
            return nav_item.page

    return html.Div("404 Page Not Found")


add_watcher_excel()
add_excel_manager_callbacks()
add_filter_callbacks()
add_navbar_callback()


def start_server(start_dev=True):

    print("🔁 Starting Dash server…")
    app.run(debug=True, use_reloader=start_dev, port=8050)


if __name__ == "__main__":

    config = get_base_config()
    log_file = config.get("log", {}).get("log_file_server", "logs/dashboard_server.log")

    init_log(log_file)

    start_server()

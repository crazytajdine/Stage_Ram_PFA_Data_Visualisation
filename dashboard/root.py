from dash import html, Output, Input, State, dcc
import logging
import plotly.io as pio
import dash
import dash_bootstrap_components as dbc
from configurations.config import get_base_config
from configurations.log_config import init_log
from components.trigger_page_change import add_watcher_params_preferences
from utils_dashboard.utils_navs import build_nav_items
from server_instance import get_app, get_server

from utils_dashboard.utils_download import download_dash

from data_managers.excel_manager import (
    add_watcher_for_data_status,
    add_callbacks as add_excel_manager_callbacks,
    hookers as excel_hookers,
    path_exists,
)
from data_managers.watcher_excel_dir import add_callbacks as add_watcher_excel
from components.filter import (
    ID_FILTER_CONTAINER,
    layout as filter_layout,
    add_callbacks as add_filter_callbacks,
)
from components.navbar import (
    layout as navbar_layout,
)

from components.title import ID_MAIN_TITLE, layout as tittle_layout


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
    Output(ID_MAIN_TITLE, "children"),
    Output(ID_FILTER_CONTAINER, "style"),
    Output("navbar", "children"),
    Input("url", "pathname"),
    add_watcher_for_data_status(),
    add_watcher_params_preferences(),
)
def update_page_and_navbar(pathname, _, pref):
    does_path_exists = path_exists()
    logging.info("Selected Path : %s", pathname)
    nav_items = build_nav_items(does_path_exists)
    logging.info("Does path exist set to %s", does_path_exists)

    logging.info("Nav items metadata: %s", [(i.name, i.show_navbar) for i in nav_items])

    selected_page_href: str = ""

    for nav_item in nav_items:
        if pathname == nav_item.href:
            logging.info(f"user id selected page  {pathname}")
            page_content = nav_item.page
            page_title = nav_item.title
            filter_style = {} if nav_item.show_filter else {"display": "none"}
            selected_page_href = nav_item.href

            break
    else:
        if nav_items:

            page_content = nav_items[0].page
            page_title = nav_items[0].title
            filter_style = {} if nav_items[0].show_filter else {"display": "none"}
            selected_page_href = nav_items[0].href
            logging.info(
                f"user id didn't find any page with {pathname} and will load the first one {selected_page_href}"
            )

        else:
            logging.info(f"user id didn't find any page  {pathname}")
            page_content = html.Div("No page is loaded")
            page_title = ""
            filter_style = {}

    # Build navbar
    navbar = [
        dbc.NavItem(
            dbc.NavLink(
                nav_item.name,
                href=nav_item.href,
                active=(selected_page_href == nav_item.href),
            )
        )
        for nav_item in nav_items
        if nav_item.show_navbar
    ]
    navbar.append(
        dbc.Button(
            [html.Span("Logout", className="label")],
            id="logout-btn",
            className="btn-logout",
            color="light",
            outline=True,
        )
    )

    return page_content, page_title, filter_style, navbar


add_watcher_excel()
add_excel_manager_callbacks()
add_filter_callbacks()


def start_server(start_dev=True):

    logging.info("🔁 Starting Dash server…")
    app.run(debug=True, use_reloader=start_dev, port=8050)


if __name__ == "__main__":

    config = get_base_config()
    log_file = config.get("log", {}).get("log_file_server", "logs/dashboard_server.log")

    init_log(log_file)

    start_server()

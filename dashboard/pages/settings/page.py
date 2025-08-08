# pages/settings/page.py
from datetime import datetime
from dash import html, dcc, Input, Output, State
import dash
import dash_bootstrap_components as dbc
import logging

from server_instance import get_app
from data_managers.excel_manager import (
    ID_INTERVAL_WATCHER,
    ID_PATH_STORE,
    get_path_to_excel,
    get_modification_time_cashed,
    add_watch_file,
)
from utils_dashboard.utils_preference import get_nav_preferences, set_page_visibility

from pages.settings.metadata import metadata

app = get_app()

ID_CURRENT_PATH = "current-path"
ID_UPDATE_PATH_BTN = "update-path-btn"
ID_NEW_PATH_INPUT = "new-path"
ID_UPDATE_PATH_MSG = "update-path-message"
ID_AUTO_REFRESH_STATUS = "auto-refresh-status"
ID_TOGGLE_AUTO_REFRESH = "toggle-auto-refresh"
ID_TOGGLE_REFRESH_MSG = "toggle-refresh-message"
ID_LAST_REFRESH_TIME = "last-refresh-time"
ID_SETTINGS_BUTTON_NAV = "settings-button-navbar"
ID_PAGE_VISIBILITY_MSG = "page-visibility-message"

ID_CONTAINER_VISIBILITY_CONTROLS = "page-visibility-controls"


layout = html.Div(
    [
        # ── Excel File
        dbc.Card(
            [
                dbc.CardHeader("Excel File"),
                dbc.CardBody(
                    [
                        dbc.Label("Current path:", className="fw-bold me-2"),
                        html.Span(id=ID_CURRENT_PATH, className="mb-3"),
                        dbc.Input(
                            id=ID_NEW_PATH_INPUT,
                            placeholder="Enter a new path…",
                            type="text",
                            className="mb-4 excel-card-glass",
                        ),
                        dbc.Button(
                            "Update",
                            id=ID_UPDATE_PATH_BTN,
                            className="btn-glossy my-2",
                        ),
                        dbc.Alert(id=ID_UPDATE_PATH_MSG, is_open=False),
                    ]
                ),
            ],
            className="mb-4",
        ),
        # ── Auto Refresh
        dbc.Card(
            [
                dbc.CardHeader("Auto Refresh"),
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                dbc.Label("Status:", className="fw-bold me-2 mb-0"),
                                html.Span(id=ID_AUTO_REFRESH_STATUS),
                            ],
                            className="d-flex align-items-center mb-2",
                        ),
                        html.Div(
                            [
                                dbc.Label(
                                    "Last refresh:",
                                    className="fw-bold me-2",
                                ),
                                html.Span(
                                    id=ID_LAST_REFRESH_TIME, className="text-muted"
                                ),
                            ],
                            className="mb-3 d-flex",
                        ),
                        dbc.Button(
                            "Toggle state",
                            id=ID_TOGGLE_AUTO_REFRESH,
                            className="btn-glossy",
                        ),
                        dbc.Alert(
                            id=ID_TOGGLE_REFRESH_MSG, is_open=False, className="mt-3"
                        ),
                    ]
                ),
            ],
            className="mb-4",
        ),
        # ── Page Visibility
        dbc.Card(
            [
                dbc.CardHeader("Page Visibility"),
                dbc.CardBody(
                    [
                        html.P(
                            "Select which pages to show in the navigation:",
                            className="mb-3",
                        ),
                        html.Div(id=ID_CONTAINER_VISIBILITY_CONTROLS),
                        html.Hr(className="my-3"),
                        dbc.Button(
                            "Save changes",
                            id=ID_SETTINGS_BUTTON_NAV,
                            className="btn-glossy me-2",
                        ),
                        dbc.Alert(
                            id=ID_PAGE_VISIBILITY_MSG, is_open=False, className="mt-3"
                        ),
                    ]
                ),
            ]
        ),
        # --- Internal stores & interval --------------------------------------
    ],
    className="mx-4",
)


# ──────────────────────────────────────────────────────────────────────────────
# CALLBACKS
# ──────────────────────────────────────────────────────────────────────────────
# 1. Display current Excel path
@app.callback(
    Output(ID_CURRENT_PATH, "children"),
    Input(ID_UPDATE_PATH_MSG, "is_open"),
    prevent_initial_call=False,
)
def display_current_path(_):
    path = get_path_to_excel()
    logging.debug(f"Displaying current Excel path: {path}")
    return get_path_to_excel()


# 4. Update the "Enabled / Disabled" text
@app.callback(
    Output(ID_AUTO_REFRESH_STATUS, "children"),
    Output(ID_AUTO_REFRESH_STATUS, "className"),
    Input(ID_INTERVAL_WATCHER, "disabled"),
)
def update_status_text(disabled):
    logging.debug(f"Auto-refresh status updated:")
    return (
        "Enabled" if not disabled else "Disabled",
        "text-success" if not disabled else "text-danger",
    )


# 5. Update the last-refresh timestamp
@app.callback(Output(ID_LAST_REFRESH_TIME, "children"), add_watch_file())
def update_refresh_time(_):
    modification_time = get_modification_time_cashed()
    logging.debug(f"Last refresh time updated: {modification_time}")

    return str(modification_time)


# 6. Display page visibility controls
@app.callback(
    Output(ID_CONTAINER_VISIBILITY_CONTROLS, "children"),
    Input("url", "pathname"),
)
def update_page_visibility_controls(pathname):
    if pathname == metadata.href:
        nav_preferences = get_nav_preferences()
        logging.debug(
            f"Loading page visibility controls for {len(nav_preferences)} pages"
        )

        checkboxes = [
            dbc.Checkbox(
                id={"type": "page-checkbox", "index": page_label},
                label=page_label,
                value=is_checked,
                className="mb-2",
            )
            for page_label, is_checked in nav_preferences.items()
        ]
        return checkboxes
    else:
        logging.debug(
            f"Not on settings page ({pathname}), no visibility controls loaded."
        )

        return []


# 7. Save page visibility preferences
@app.callback(
    Output(ID_PAGE_VISIBILITY_MSG, "children"),
    Output(ID_PAGE_VISIBILITY_MSG, "color"),
    Output(ID_PAGE_VISIBILITY_MSG, "is_open"),
    Input(ID_SETTINGS_BUTTON_NAV, "n_clicks"),
    State({"type": "page-checkbox", "index": dash.ALL}, "value"),
    State({"type": "page-checkbox", "index": dash.ALL}, "id"),
    prevent_initial_call=True,
)
def save_page_visibility_cb(n_clicks, values, ids):
    prefs = {
        ids[i]["index"]: (values[i] if values[i] is not None else False)
        for i in range(len(ids))
    }
    logging.info(f"Saving page visibility settings: {prefs}")

    if not any(prefs.values()):
        logging.warning(
            "User attempted to save page visibility with no pages selected."
        )
        return (
            "Error: At least one page must be selected.",
            "danger",
            True,
        )

    set_page_visibility(prefs)
    logging.info("Page visibility settings saved successfully.")
    return "Settings saved successfully.", "success", True

# pages/settings/page.py
from dash import html, Input, Output, State
import dash
import dash_bootstrap_components as dbc
import logging

from components.trigger_page_change import add_output_manual_trigger
from components.auth import ID_USER_ID
from configurations.nav_config import MAPPER_NAV_CONFIG
from components.navbar import add_input_loaded_url
from server_instance import get_app

from utils_dashboard.utils_page import (
    get_allowed_pages_all,
    update_user_page_preferences,
)

from pages.settings.metadata import metadata

app = get_app()

ID_SETTINGS_BUTTON_NAV = "settings-button-navbar"
ID_PAGE_VISIBILITY_MSG = "page-visibility-message"

ID_CONTAINER_VISIBILITY_CONTROLS = "page-visibility-controls"


layout = html.Div(
    [
        # ── Excel File
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
    ],
    className="mx-4",
)


# ──────────────────────────────────────────────────────────────────────────────
# CALLBACKS
# ──────────────────────────────────────────────────────────────────────────────


# 6. Display page visibility controls
@app.callback(
    Output(ID_CONTAINER_VISIBILITY_CONTROLS, "children"),
    add_input_loaded_url(),
    State(ID_USER_ID, "data"),
)
def update_page_visibility_controls(pathname, user_id):
    if user_id is None:
        return []
    if pathname == metadata.href:

        allowed_pages = get_allowed_pages_all(user_id)
        allowed_pages = [
            (MAPPER_NAV_CONFIG[allowed_page.page_id], not allowed_page.disabled)
            for allowed_page in allowed_pages
        ]
        logging.debug(
            f"Loading page visibility controls for {len(allowed_pages)} pages"
        )
        checkboxes = [
            dbc.Checkbox(
                id={"type": "page-checkbox", "index": page_label.id},
                label=page_label.name,
                value=is_checked,
                className="mb-2",
            )
            for (page_label, is_checked) in allowed_pages
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
    add_output_manual_trigger(),
    Input(ID_SETTINGS_BUTTON_NAV, "n_clicks"),
    State(ID_USER_ID, "data"),
    State({"type": "page-checkbox", "index": dash.ALL}, "value"),
    State({"type": "page-checkbox", "index": dash.ALL}, "id"),
    prevent_initial_call=True,
)
def save_page_visibility_cb(n_clicks, user_id, values, ids):

    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    prefs = {
        ids[i]["index"]: values[i] if values[i] is not None else False
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
            dash.no_update,
        )

    is_updated = update_user_page_preferences(user_id, prefs)

    if not is_updated:
        logging.error("Failed to update page visibility settings.")
        return (
            "Error: Failed to save settings.",
            "danger",
            True,
            dash.no_update,
        )

    logging.info("Page visibility settings saved successfully.")
    return "Settings saved successfully.", "success", True, None

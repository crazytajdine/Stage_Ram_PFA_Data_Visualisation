# pages/settings/page.py
from dash import html, dcc, Input, Output, State
import dash
import dash_bootstrap_components as dbc
import logging

from components.trigger_page_change import add_output_manual_trigger
from server_instance import get_app

from utils_dashboard.utils_preference import get_nav_preferences, set_page_visibility

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
    add_output_manual_trigger(),
    Input(ID_SETTINGS_BUTTON_NAV, "n_clicks"),
    State({"type": "page-checkbox", "index": dash.ALL}, "value"),
    State({"type": "page-checkbox", "index": dash.ALL}, "id"),
    prevent_initial_call=True,
)
def save_page_visibility_cb(n_clicks, values, ids):

    if not n_clicks:
        raise dash.exceptions.PreventUpdate

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
            dash.no_update,
        )

    set_page_visibility(prefs)
    logging.info("Page visibility settings saved successfully.")
    return "Settings saved successfully.", "success", True, None

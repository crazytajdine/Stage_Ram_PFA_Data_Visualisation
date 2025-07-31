# pages/settings/page.py
from datetime import datetime
from dash import html, dcc, Input, Output, State
import dash
import dash_bootstrap_components as dbc

from server_instance import get_app
from excel_manager import (
    ID_INTERVAL_WATCHER,
    get_path_to_excel,
    update_path_to_excel,
    toggle_auto_refresh,
    is_auto_refresh_disabled,
    get_modification_time_cashed,
    add_watch_file,
    ID_PATH_STORE,
)
from utils_dashboard.utils_preference import get_nav_preferences, set_page_visibility

from pages.settings.metadata import metadata

app = get_app()

ID_TRIGGER_PARAMS_CHANGE_NAVBAR = "trigger_navbar"
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
        dcc.Store(ID_TRIGGER_PARAMS_CHANGE_NAVBAR),
        html.H1("Paramètres", className="mb-4"),
        # ── Fichier Excel
        dbc.Card(
            [
                dbc.CardHeader("Fichier Excel"),
                dbc.CardBody(
                    [
                        dbc.Label("Chemin actuel :", className="fw-bold me-2"),
                        html.Span(id=ID_CURRENT_PATH, className="mb-3"),
                        dbc.Input(
                            id=ID_NEW_PATH_INPUT,
                            placeholder="Entrez un nouveau chemin…",
                            type="text",
                            className="my-2",
                        ),
                        dbc.Button(
                            "Mettre à jour",
                            id=ID_UPDATE_PATH_BTN,
                            color="primary",
                            className="my-2",
                        ),
                        dbc.Alert(id=ID_UPDATE_PATH_MSG, is_open=False),
                    ]
                ),
            ],
            className="mb-4",
        ),
        # ── Actualisation automatique
        dbc.Card(
            [
                dbc.CardHeader("Actualisation automatique"),
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                dbc.Label("Statut :", className="fw-bold me-2 mb-0"),
                                html.Span(id=ID_AUTO_REFRESH_STATUS),
                            ],
                            className=" d-flex align-items-center mb-2",
                        ),
                        html.Div(
                            [
                                dbc.Label(
                                    "Dernière actualisation :",
                                    className="fw-bold me-2 ",
                                ),
                                html.Span(
                                    id=ID_LAST_REFRESH_TIME, className="text-muted"
                                ),
                            ],
                            className="mb-3 d-flex  ",
                        ),
                        dbc.Button(
                            "Basculer l'état",
                            id=ID_TOGGLE_AUTO_REFRESH,
                            color="secondary",
                        ),
                        dbc.Alert(
                            id=ID_TOGGLE_REFRESH_MSG, is_open=False, className="mt-3"
                        ),
                    ]
                ),
            ],
            className="mb-4",
        ),
        # ➕ NEW: File Monitoring Display
        dbc.Card(
            [
                dbc.CardHeader("Surveillance du fichier"),
                dbc.CardBody(
                    [
                        html.Div(
                            id="modification-time-display",
                            style={
                                "padding": "15px",
                                "background-color": "#f8f9fa",
                                "border": "1px solid #dee2e6",
                                "border-radius": "5px",
                                "font-family": "Consolas, Monaco, monospace",
                                "font-size": "14px",
                                "color": "#495057",
                                "min-height": "50px",
                                "display": "flex",
                                "align-items": "center",
                            },
                        )
                    ]
                ),
            ],
            className="mb-4",
        ),
        # ── Visibilité des pages
        dbc.Card(
            [
                dbc.CardHeader("Visibilité des pages"),
                dbc.CardBody(
                    [
                        html.P(
                            "Sélectionnez les pages à afficher dans la navigation :",
                            className="mb-3",
                        ),
                        html.Div(
                            id=ID_CONTAINER_VISIBILITY_CONTROLS,
                        ),
                        html.Hr(className="my-3"),
                        dbc.Button(
                            "Sauvegarder les modifications",
                            id=ID_SETTINGS_BUTTON_NAV,
                            color="primary",
                            className="me-2",
                        ),
                        dbc.Alert(
                            id=ID_PAGE_VISIBILITY_MSG, is_open=False, className="mt-3"
                        ),
                    ]
                ),
            ]
        ),
        # --- Stores & interval interne --------------------------------------
    ]
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
    return get_path_to_excel()


# 2. Handle Excel path update
@app.callback(
    Output(ID_UPDATE_PATH_MSG, "children"),
    Output(ID_UPDATE_PATH_MSG, "color"),
    Output(ID_UPDATE_PATH_MSG, "is_open"),
    Output("is-path-store", "data", allow_duplicate=True),  # ➕  nouveau
    Input(ID_UPDATE_PATH_BTN, "n_clicks"),
    State(ID_NEW_PATH_INPUT, "value"),
    prevent_initial_call=True,
)
def handle_update_path(_, new_path):
    if not new_path:
        return "Veuillez entrer un chemin.", "warning", True, dash.no_update

    success, msg = update_path_to_excel(new_path)
    color = "success" if success else "danger"
    # si succès → on propage le chemin pour que root.py ré-évalue path_exits()
    return msg, color, True, (new_path if success else dash.no_update)


# 3. Toggle auto-refresh on/off
@app.callback(
    Output(ID_TOGGLE_REFRESH_MSG, "children"),
    Output(ID_TOGGLE_REFRESH_MSG, "color"),
    Output(ID_TOGGLE_REFRESH_MSG, "is_open"),
    Output(ID_INTERVAL_WATCHER, "disabled", allow_duplicate=True),
    Input(ID_TOGGLE_AUTO_REFRESH, "n_clicks"),
    prevent_initial_call=True,
)
def toggle_auto_refresh_cb(n_clicks):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    try:
        status = toggle_auto_refresh()
        return (
            f"Actualisation {'activée' if status else 'désactivée'}.",
            "success",
            False,
            status,
        )
    except Exception as e:
        return f"Erreur : {e}", "danger", False, is_auto_refresh_disabled()


# 4. Update the "Activée / Désactivée" text
@app.callback(
    Output(ID_AUTO_REFRESH_STATUS, "children"),
    Output(ID_AUTO_REFRESH_STATUS, "className"),
    Input(
        ID_INTERVAL_WATCHER,
        "disabled",
    ),
)
def update_status_text(disabled):
    return (
        "Activée" if not disabled else "Désactivée",
        "text-success" if not disabled else "text-danger",
    )


# 5. Update the last-refresh timestamp
@app.callback(Output(ID_LAST_REFRESH_TIME, "children"), add_watch_file())
def update_refresh_time(_):

    modification_time = get_modification_time_cashed()
    return str(modification_time)


# 6. Save page-visibility settings
@app.callback(
    Output(ID_CONTAINER_VISIBILITY_CONTROLS, "children"),
    Input("url", "pathname"),
)
def update_page_visibility_controls(pathname):
    if pathname == metadata.href:
        nav_preferences = get_nav_preferences()
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
        return []


@app.callback(
    Output(ID_TRIGGER_PARAMS_CHANGE_NAVBAR, "data"),
    Output(ID_PAGE_VISIBILITY_MSG, "children"),
    Output(ID_PAGE_VISIBILITY_MSG, "color"),
    Output(ID_PAGE_VISIBILITY_MSG, "is_open"),
    Input(ID_SETTINGS_BUTTON_NAV, "n_clicks"),
    State({"type": "page-checkbox", "index": dash.ALL}, "value"),
    State({"type": "page-checkbox", "index": dash.ALL}, "id"),
    prevent_initial_call=True,
)
def save_page_visibility_cb(n_clicks, values, ids):
    # Build a dict { page_label: bool }
    prefs = {
        ids[i]["index"]: (values[i] if values[i] is not None else False)
        for i in range(len(ids))
    }
    # Validate at least one page is shown
    if not any(prefs.values()):
        return (
            dash.no_update,
            "Erreur : Au moins une page doit être sélectionnée.",
            "danger",
            True,
        )

    # Persist
    set_page_visibility(prefs)

    return None, "Paramètres sauvegardés avec succès.", "success", True

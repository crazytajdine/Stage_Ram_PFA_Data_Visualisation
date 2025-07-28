# pages/settings/page.py
from datetime import datetime
from dash import html, dcc, Input, Output, State
import dash
import dash_bootstrap_components as dbc

from server_instance import get_app
from excel_manager import (
    get_path_to_excel,
    update_path_to_excel,
    toggle_auto_refresh,
    is_auto_refresh_enabled,
    ID_PATH_STORE,
)
from utils_dashboard.utils_preference import get_nav_preferences, set_page_visibility

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
                        dbc.Label("Chemin actuel :", className="fw-bold"),
                        html.Div(id=ID_CURRENT_PATH, className="mb-3"),
                        dbc.Input(
                            id=ID_NEW_PATH_INPUT,
                            placeholder="Entrez un nouveau chemin…",
                            type="text",
                            className="mb-2",
                        ),
                        dbc.Button(
                            "Mettre à jour",
                            id=ID_UPDATE_PATH_BTN,
                            color="primary",
                            className="mb-2",
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
                                dbc.Label("Statut :", className="fw-bold me-2"),
                                html.Span(id=ID_AUTO_REFRESH_STATUS),
                            ],
                            className="mb-2 d-flex align-items-center",
                        ),
                        html.Div(
                            [
                                dbc.Label(
                                    "Dernière actualisation :", className="fw-bold me-2"
                                ),
                                html.Span(
                                    id=ID_LAST_REFRESH_TIME, className="text-muted"
                                ),
                            ],
                            className="mb-3 d-flex align-items-center",
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
                            id="page-visibility-controls",
                            children=[
                                dbc.Checkbox(
                                    id={"type": "page-checkbox", "index": page_label},
                                    label=page_label,
                                    value=is_checked,
                                    className="mb-2",
                                )
                                for page_label, is_checked in get_nav_preferences().items()
                            ],
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
    Input(ID_UPDATE_PATH_BTN, "n_clicks"),
    State(ID_NEW_PATH_INPUT, "value"),
    prevent_initial_call=True,
)
def handle_update_path(n_clicks, _, new_path):
    if not new_path:
        return "Veuillez entrer un chemin.", "warning", True

    success, msg = update_path_to_excel(new_path)
    color = "success" if success else "danger"
    return msg, color, True


# 3. Toggle auto-refresh on/off
@app.callback(
    Output(ID_TOGGLE_REFRESH_MSG, "children"),
    Output(ID_TOGGLE_REFRESH_MSG, "color"),
    Output(ID_TOGGLE_REFRESH_MSG, "is_open"),
    Output("auto-refresh-enabled", "data"),
    Input(ID_TOGGLE_AUTO_REFRESH, "n_clicks"),
    prevent_initial_call=True,
)
def handle_toggle_refresh(n_clicks):
    try:
        status = toggle_auto_refresh()
        return (
            f"Actualisation {'activée' if status else 'désactivée'}.",
            "success",
            True,
            status,
        )
    except Exception as e:
        return f"Erreur : {e}", "danger", True, is_auto_refresh_enabled()


# 4. Update the “Activée / Désactivée” text
@app.callback(
    Output(ID_AUTO_REFRESH_STATUS, "children"),
    Output(ID_AUTO_REFRESH_STATUS, "className"),
    Input("auto-refresh-enabled", "data"),
)
def update_auto_refresh_label(enabled):
    return (
        "Activée" if enabled else "Désactivée",
        "text-success" if enabled else "text-danger",
    )


# 5. Update the last-refresh timestamp
@app.callback(
    Output(ID_LAST_REFRESH_TIME, "children"),
    Input("refresh-counter", "n_intervals"),
    prevent_initial_call=False,
)
def update_refresh_time(_):
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 6. Save page-visibility settings
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
    print(prefs)
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

# pages/settings/page.py
from server_instance import get_app
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import dash
# On ré-utilise directement les helpers d’excel_manager
from excel_manager import (
    get_path_to_excel,
    update_path_to_excel,
    toggle_auto_refresh,
    is_auto_refresh_enabled,
)

app = get_app()          # même instance que le reste de l’appli

# ------------- MISE EN PAGE --------------------------------------------------
layout = html.Div(
    [
        html.H1("Paramètres", className="mb-4"),

        # --- Bloc : Fichier Excel -------------------------------------------
        dbc.Card(
            [
                dbc.CardHeader("Fichier Excel"),
                dbc.CardBody(
                    [
                        dbc.Label("Chemin actuel :", className="fw-bold"),
                        html.Div(id="current-path", className="mb-3"),
                        dbc.Input(
                            id="new-path",
                            placeholder="Entrez un nouveau chemin…",
                            type="text",
                            className="mb-2",
                        ),
                        dbc.Button("Mettre à jour",
                                   id="update-path-btn",
                                   color="primary",
                                   className="mb-2"),
                        dbc.Alert(id="update-path-message", is_open=False),
                    ]
                ),
            ],
            className="mb-4",
        ),

        # --- Bloc : Actualisation automatique -------------------------------
        dbc.Card(
            [
                dbc.CardHeader("Actualisation automatique"),
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                dbc.Label("Statut :", className="fw-bold me-2"),
                                html.Span(id="auto-refresh-status",
                                          className="text-success"),
                            ],
                            className="mb-2 d-flex align-items-center",
                        ),
                        html.Div(
                            [
                                dbc.Label("Dernière actualisation :",
                                          className="fw-bold me-2"),
                                html.Span(id="last-refresh-time",
                                          className="text-muted"),
                            ],
                            className="mb-3 d-flex align-items-center",
                        ),
                        dbc.Button("Basculer l’état",
                                   id="toggle-auto-refresh",
                                   color="secondary"),
                        dbc.Alert(id="toggle-refresh-message",
                                  is_open=False,
                                  className="mt-3"),
                    ]
                ),
            ]
        ),

        # --- Stores & interval interne --------------------------------------
        dcc.Store(id="auto-refresh-enabled",
                  data=is_auto_refresh_enabled()),
        dcc.Interval(id="refresh-counter",
                     interval=10_000,           # 10 s
                     n_intervals=0),
    ]
)

# ------------- CALLBACKS -----------------------------------------------------

# Afficher le chemin actuel
@callback(Output("current-path", "children"),
          Input("update-path-message", "is_open"))
def display_current_path(_):
    return get_path_to_excel()

# Mettre à jour le chemin Excel
# pages/settings/page.py  (callback handle_update_path)

@callback(
    Output("update-path-message", "children"),
    Output("update-path-message", "color"),
    Output("update-path-message", "is_open"),
    Output("is-path-store", "data", allow_duplicate=True),          # ➕  nouveau
    Input("update-path-btn", "n_clicks"),
    State("new-path", "value"),
    prevent_initial_call=True,
)
def handle_update_path(_, new_path):
    if not new_path:
        return "Veuillez entrer un chemin.", "warning", True, dash.no_update

    success, msg = update_path_to_excel(new_path)
    color = "success" if success else "danger"
    # si succès → on propage le chemin pour que root.py ré-évalue path_exits()
    return msg, color, True, (new_path if success else dash.no_update)


# Bascule auto-refresh
@callback(
    Output("toggle-refresh-message", "children"),
    Output("toggle-refresh-message", "color"),
    Output("toggle-refresh-message", "is_open"),
    Output("auto-refresh-enabled", "data"),
    Input("toggle-auto-refresh", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_auto_refresh_cb(_):
    try:
        status = toggle_auto_refresh()
        return (f"Actualisation {'activée' if status else 'désactivée'}.",
                "success", True, status)
    except Exception as e:
        return f"Erreur : {e}", "danger", True, is_auto_refresh_enabled()

# Met à jour le texte « Activée / Désactivée »
@callback(
    Output("auto-refresh-status", "children"),
    Output("auto-refresh-status", "className"),
    Input("auto-refresh-enabled", "data"),
)
def update_status_text(enabled):
    return ("Activée" if enabled else "Désactivée",
            "text-success" if enabled else "text-danger")

# Affiche l’heure de la dernière actualisation (simple horloge)
from datetime import datetime
@callback(Output("last-refresh-time", "children"),
          Input("refresh-counter", "n_intervals"))
def update_refresh_time(_):
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

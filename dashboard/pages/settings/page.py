# pages/settings/page.py
from server_instance import get_app
from dash import html, dcc, Input, Output, State, callback, callback_context
import dash_bootstrap_components as dbc
import dash
# On ré-utilise directement les helpers d’excel_manager
from excel_manager import (
    get_path_to_excel,
    update_path_to_excel,
    toggle_auto_refresh,
    is_auto_refresh_enabled,
)
from config import get_all_page_visibility, update_page_visibility

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
                        dbc.Button("Basculer l'état",
                                   id="toggle-auto-refresh",
                                   color="secondary"),
                        dbc.Alert(id="toggle-refresh-message",
                                  is_open=False,
                                  className="mt-3"),
                    ]
                ),
            ],
            className="mb-4",
        ),

        # --- Bloc : Visibilité des pages ------------------------------------
        dbc.Card(
            [
                dbc.CardHeader("Visibilité des pages"),
                dbc.CardBody(
                    [
                        html.P("Sélectionnez les pages à afficher dans la navigation :",
                               className="mb-3"),
                        html.Div(id="page-visibility-controls"),
                        html.Hr(className="my-3"),
                        dbc.Button("Sauvegarder les modifications",
                                   id="save-page-visibility",
                                   color="primary",
                                   className="me-2"),
                        dbc.Button("Réinitialiser",
                                   id="reset-page-visibility",
                                   color="secondary",
                                   outline=True),
                        dbc.Alert(id="page-visibility-message",
                                  is_open=False,
                                  className="mt-3"),
                    ]
                ),
            ]
        ),

        # --- Stores & interval interne --------------------------------------
        dcc.Store(id="auto-refresh-enabled",
                  data=is_auto_refresh_enabled()),
        dcc.Store(id="page-visibility-store",
                  data=get_all_page_visibility()),
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

# --- Callbacks pour la visibilité des pages ---------------------------------

@callback(
    Output("page-visibility-controls", "children"),
    Input("page-visibility-store", "data")
)
def create_page_visibility_controls(page_settings):
    page_labels = {
        "dashboard": "Dashboard",
        "analytics": "Analytics", 
        "weekly": "Weekly",
        "performance_metrics": "Performance Metrics"
    }
    
    controls = []
    for page_key, page_label in page_labels.items():
        is_checked = page_settings.get(page_key, True)
        checkbox = dbc.Checkbox(
            id={"type": "page-checkbox", "index": page_key},
            label=page_label,
            value=is_checked,
            className="mb-2"
        )
        controls.append(checkbox)
    
    return controls

@callback(
    Output("page-visibility-message", "children"),
    Output("page-visibility-message", "color"),
    Output("page-visibility-message", "is_open"),
    Output("page-visibility-store", "data"),
    Input("save-page-visibility", "n_clicks"),
    Input("reset-page-visibility", "n_clicks"),
    State({"type": "page-checkbox", "index": dash.ALL}, "value"),
    State({"type": "page-checkbox", "index": dash.ALL}, "id"),
    prevent_initial_call=True
)
def handle_page_visibility_changes(save_clicks, reset_clicks, checkbox_values, checkbox_ids):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    trigger_id = ctx.triggered[0]["prop_id"]
    
    if "reset-page-visibility" in trigger_id:
        default_settings = {
            "dashboard": True,
            "analytics": True,
            "weekly": True,
            "performance_metrics": True
        }
        update_page_visibility(default_settings)
        return "Paramètres réinitialisés avec succès.", "success", True, default_settings
    
    elif "save-page-visibility" in trigger_id:
        if checkbox_values and checkbox_ids:
            new_settings = {}
            for i, checkbox_id in enumerate(checkbox_ids):
                page_key = checkbox_id["index"]
                new_settings[page_key] = checkbox_values[i] if checkbox_values[i] is not None else False
            
            # Check if at least one page is selected
            if not any(new_settings.values()):
                return "Erreur: Au moins une page doit être sélectionnée.", "danger", True, dash.no_update
            
            update_page_visibility(new_settings)
            return "Paramètres sauvegardés avec succès.", "success", True, new_settings
        else:
            return "Erreur lors de la sauvegarde.", "danger", True, dash.no_update
    
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

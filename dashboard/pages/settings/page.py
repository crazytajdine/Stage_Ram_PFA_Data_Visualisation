# pages/settings/page.py
from server_instance import get_app
from dash import html, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from datetime import datetime


from excel_manager import (
    get_path_to_excel,
    update_path_to_excel,
    toggle_auto_refresh,
    is_auto_refresh_enabled,
)

from utils_dashboard.utils_preference import get_nav_preferences, set_page_visibility

app = get_app()

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
                        dbc.Button(
                            "Mettre à jour",
                            id="update-path-btn",
                            color="primary",
                            className="mb-2",
                        ),
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
                                html.Span(
                                    id="auto-refresh-status", className="text-success"
                                ),
                            ],
                            className="mb-2 d-flex align-items-center",
                        ),
                        html.Div(
                            [
                                dbc.Label(
                                    "Dernière actualisation :", className="fw-bold me-2"
                                ),
                                html.Span(
                                    id="last-refresh-time", className="text-muted"
                                ),
                            ],
                            className="mb-3 d-flex align-items-center",
                        ),
                        dbc.Button(
                            "Basculer l'état",
                            id="toggle-auto-refresh",
                            color="secondary",
                        ),
                        dbc.Alert(
                            id="toggle-refresh-message", is_open=False, className="mt-3"
                        ),
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
                            id="save-page-visibility",
                            color="primary",
                            className="me-2",
                        ),
                        dbc.Alert(
                            id="page-visibility-message",
                            is_open=False,
                            className="mt-3",
                        ),
                    ]
                ),
            ]
        ),
    ]
)

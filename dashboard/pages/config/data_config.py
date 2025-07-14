"""
Data Configuration Page - File and Sheet Selection
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
import json
import os
from pathlib import Path

# Configuration file path
CONFIG_FILE = Path("dashboard_config.json")

def load_config():
    """Load configuration from file"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"file_path": "", "sheet_name": "Sheet1"}

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except:
        return False

def create_config_layout():
    """Create the configuration layout with current values"""
    # Load current configuration
    current_config = load_config()
    
    return html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("📁 Configuration des Données", className="mb-4"),
                
                dbc.Card([
                    dbc.CardHeader("Sélection du Fichier Excel"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Chemin du fichier Excel:", className="form-label"),
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="file-path-input",
                                        type="text",
                                        placeholder="/chemin/vers/votre/fichier.xlsx",
                                        value=current_config.get("file_path", ""),
                                        className="form-control"
                                    ),
                                    dbc.Button(
                                        "📂 Parcourir", 
                                        id="browse-button",
                                        color="secondary",
                                        outline=True,
                                        className="btn-outline-secondary"
                                    )
                                ]),
                                html.Small("Entrez le chemin complet vers votre fichier Excel", 
                                         className="form-text text-muted")
                            ], md=12)
                        ], className="mb-3"),
                        
                        dbc.Row([
                            dbc.Col([
                                html.Label("Nom de la feuille:", className="form-label"),
                                dbc.Input(
                                    id="sheet-name-input",
                                    type="text",
                                    placeholder="Sheet1",
                                    value=current_config.get("sheet_name", "Sheet1"),
                                    className="form-control"
                                ),
                                html.Small("Nom de la feuille Excel à utiliser", 
                                         className="form-text text-muted")
                            ], md=6)
                        ], className="mb-3"),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    "💾 Sauvegarder la Configuration",
                                    id="save-config-button",
                                    color="primary",
                                    size="lg",
                                    className="w-100"
                                )
                            ], md=12)
                        ], className="mb-3"),
                        
                        html.Div(id="config-status-message")
                    ])
                ], className="mb-4"),
                
                dbc.Card([
                    dbc.CardHeader("Statut du Fichier"),
                    dbc.CardBody([
                        html.Div(id="file-status-div")
                    ])
                ], className="mb-4"),
                
                dbc.Card([
                    dbc.CardHeader("Instructions"),
                    dbc.CardBody([
                        html.P([
                            "1. ", html.Strong("Sélectionnez votre fichier Excel"), 
                            " en tapant le chemin complet ou en utilisant le bouton Parcourir"
                        ]),
                        html.P([
                            "2. ", html.Strong("Entrez le nom de la feuille"), 
                            " que vous voulez analyser (par défaut: Sheet1)"
                        ]),
                        html.P([
                            "3. ", html.Strong("Cliquez sur Sauvegarder"), 
                            " pour enregistrer la configuration"
                        ]),
                        html.P([
                            "4. ", html.Strong("Naviguez vers Delay Codes"), 
                            " pour commencer l'analyse"
                        ]),
                        html.Hr(),
                        html.P([
                            html.Strong("Format requis:"), " Le fichier Excel doit contenir les colonnes suivantes:"
                        ]),
                        html.Ul([
                            html.Li("DEP_DAY_SCHED (Date de départ)"),
                            html.Li("DEP_TIME_SCHED (Heure de départ)"),
                            html.Li("LIB_CODE_DR (Description du code)"),
                            html.Li("CODE_DR (Code de retard)"),
                            html.Li("AC_SUBTYPE (Type d'avion)"),
                            html.Li("AC_REGISTRATION (Matricule)"),
                            html.Li("DEP_AP_SCHED (Aéroport de départ)")
                        ])
                    ])
                ])
            ], md=8)
        ], justify="center")
    ], fluid=True, className="py-4")
    ])

def get_layout():
    """Get the dynamic layout"""
    return create_config_layout()

# For compatibility
layout = get_layout()
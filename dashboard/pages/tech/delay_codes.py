"""
Delay Codes Analysis Page - Extracted from self_app_3.py
"""

import polars as pl
from pathlib import Path
from datetime import datetime
from dash import html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

# ------------------------------------------------------------------ #
# 1 ▸  Data loading and preparation                                 #
# ------------------------------------------------------------------ #
def load_config():
    """Load configuration from file"""
    config_file = Path("dashboard_config.json")
    if config_file.exists():
        try:
            import json
            with open(config_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"file_path": "", "sheet_name": "Sheet1"}

def load_delay_data():
    """Load and prepare delay codes data"""
    config = load_config()
    
    if not config.get("file_path"):
        print("❌ No file path configured. Please configure data source first.")
        return pl.DataFrame()
    
    SRC = Path(config["file_path"])
    SHEET = config.get("sheet_name", "Sheet1")
    
    if not SRC.exists():
        print(f"❌ File not found: {SRC}")
        return pl.DataFrame()

    try:
        # Lazy read once
        df_lazy = pl.read_excel(SRC, sheet_name=SHEET).lazy()

        # Normalise column names
        col_map = {c: "_".join(c.strip().split()).upper()
                   for c in df_lazy.collect_schema().names()}
        df_lazy = df_lazy.rename(col_map)

        # Build unified DEP_DATETIME (supports HH:MM:SS or HH:MM)
        df_lazy = df_lazy.with_columns(
            (
                pl.col("DEP_DAY_SCHED").cast(pl.Utf8) + " " + 
                pl.when(pl.col("DEP_TIME_SCHED").str.len_chars() == 5)
                .then(pl.col("DEP_TIME_SCHED") + ":00")
                .otherwise(pl.col("DEP_TIME_SCHED"))
            ).str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False)
             .alias("DEP_DATETIME")
        )

        # Keep only delay-code rows with TEC description
        df_filtered = (
            df_lazy.filter(pl.col("LIB_CODE_DR") == "TEC")
                   .collect()
        )
        
        print(f"✅ Data loaded: {df_filtered.height} rows with TEC codes")
        return df_filtered
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return pl.DataFrame()

def get_data_info():
    """Get current data and dropdown options"""
    df_filtered = load_delay_data()
    
    # Dropdown lists
    flottes = sorted(df_filtered.get_column("AC_SUBTYPE").drop_nulls().unique().to_list()) if not df_filtered.is_empty() else []
    matricules = sorted(df_filtered.get_column("AC_REGISTRATION").drop_nulls().unique().to_list()) if not df_filtered.is_empty() else []
    codes_dr = sorted(df_filtered.get_column("CODE_DR").drop_nulls().unique().to_list()) if not df_filtered.is_empty() else []

    # Datetime input bounds
    if not df_filtered.is_empty():
        dt_min, dt_max = (df_filtered.get_column("DEP_DATETIME").min(), 
                          df_filtered.get_column("DEP_DATETIME").max())
    else:
        dt_min = dt_max = datetime.now()

    dt_min = dt_min or datetime.now()
    dt_max = dt_max or datetime.now()
    dt_min_iso, dt_max_iso = (dt_min.strftime("%Y-%m-%dT%H:%M"),
                              dt_max.strftime("%Y-%m-%dT%H:%M"))
    
    return df_filtered, flottes, matricules, codes_dr, dt_min_iso, dt_max_iso

# ------------------------------------------------------------------ #
# 2 ▸  Helper – aggregate per code                                   #
# ------------------------------------------------------------------ #
def analyze_delay_codes_polars(frame: pl.DataFrame) -> pl.DataFrame:
    """
    Return a Polars frame with:
        CODE_DR | Occurrences | Description | Aéroports | Nb_AP
    """
    if frame.is_empty():
        return pl.DataFrame({
            "CODE_DR": [],
            "Occurrences": [],
            "Description": [],
            "Aéroports": [],
            "Nb_AP": []
        })

    # First get airport counts per code
    airport_counts = (
        frame.group_by(["CODE_DR", "DEP_AP_SCHED"])
        .agg(pl.len().alias("ap_count"))
    )
    
    agg = (
        frame.group_by("CODE_DR")
             .agg([
                 pl.len().alias("Occurrences"),
                 pl.col("LIB_CODE_DR").first().alias("Description"),
                 pl.col("DEP_AP_SCHED").drop_nulls().alias("AP_list")
             ])
             .join(
                 airport_counts.group_by("CODE_DR").agg([
                     pl.col("DEP_AP_SCHED").alias("airports"),
                     pl.col("ap_count").alias("counts")
                 ]),
                 on="CODE_DR",
                 how="left"
             )
             .with_columns([
                 pl.struct(["airports", "counts"]).map_elements(
                     lambda x: ', '.join([
                         f"{ap} ({cnt})" 
                         for ap, cnt in sorted(
                             zip(x["airports"], x["counts"]), 
                             key=lambda item: item[1], 
                             reverse=True
                         )[:15]
                     ]) + (f" ... (+{len(x['airports'])-15} autres)" if len(x["airports"]) > 15 else ""),
                     return_dtype=pl.Utf8
                 ).alias("Aéroports"),
                 pl.col("AP_list").list.n_unique().alias("Nb_AP")
             ])
             .select(["CODE_DR", "Occurrences", "Description",
                      "Aéroports", "Nb_AP"])
             .sort("Occurrences", descending=True)
    )
    return agg

# ------------------------------------------------------------------ #
# 3 ▸  Layout                                                        #
# ------------------------------------------------------------------ #
def create_delay_codes_layout():
    """Create the delay codes analysis layout"""
    
    # Get fresh data info
    df_filtered, flottes, matricules, codes_dr, dt_min_iso, dt_max_iso = get_data_info()
    
    # Check if data is available
    config = load_config()
    has_data = not df_filtered.is_empty()
    
    if not config.get("file_path") or not has_data:
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Alert([
                        html.H4("⚠️ Configuration Requise", className="alert-heading"),
                        html.P("Aucun fichier de données n'est configuré ou le fichier est introuvable."),
                        html.Hr(),
                        html.P("Veuillez configurer votre source de données avant d'utiliser cette page."),
                        dbc.Button("📁 Aller à la Configuration", 
                                 href="/config", color="primary", className="me-2"),
                        dbc.Button("🔄 Recharger", 
                                 id="reload-data-btn", color="secondary", outline=True)
                    ], color="warning", className="text-center")
                ], md=8)
            ], justify="center", className="mt-5")
        ], fluid=True)
    
    left_panel = html.Div(
        [
            # Title & subtitle
            html.H1("ANALYSE DES CODES DE RETARD", className="mb-2",
                    style={"color": "#dfe6f3", "fontSize": 32}),
            html.P("Choisissez vos filtres pour explorer les codes de retard TEC.",
                   className="lead", style={"color": "#a0a7b9"}),

            # Filters section
            dbc.Card([
                dbc.CardBody([
                    # Flotte + Matricule
                    dbc.Row([
                        dbc.Col([
                            html.Label("Type d'avion (Flotte)",
                                       className="text-muted small"),
                            dcc.Dropdown(id="delay-flotte-dd",
                                         options=[{"label": f, "value": f} for f in flottes],
                                         multi=True,
                                         placeholder="Tous les types",
                                         style={'zIndex': 1002},
                                         className="dash-dropdown")
                        ], md=6),
                        dbc.Col([
                            html.Label("Matricule", className="text-muted small"),
                            dcc.Dropdown(id="delay-matricule-dd",
                                         options=[{"label": m, "value": m} for m in matricules],
                                         multi=True,
                                         placeholder="Tous les matricules",
                                         style={'zIndex': 1001},
                                         className="dash-dropdown")
                        ], md=6),
                    ], className="mb-3"),

                    # Code DR filter
                    dbc.Row([
                        dbc.Col([
                            html.Label("Code de retard", className="text-muted small"),
                            dcc.Dropdown(id="delay-code-dd",
                                         options=[{"label": c, "value": c} for c in codes_dr],
                                         multi=True,
                                         placeholder="Tous les codes",
                                         style={'zIndex': 1000},
                                         className="dash-dropdown")
                        ], md=12),
                    ], className="mb-3"),

                    # Datetime inputs
                    dbc.Row([
                        dbc.Col([
                            html.Label("Date/heure de début :",
                                       className="text-muted small"),
                            dbc.Input(id="delay-dt-start-input", 
                                    type="datetime-local",
                                    value=dt_min_iso, 
                                    min=dt_min_iso, 
                                    max=dt_max_iso,
                                    style={"width": "100%", 
                                           'backgroundColor': '#263142',
                                           'color': '#cfd8e3',
                                           'border': '1px solid #3b465d'})
                        ], md=6),
                        dbc.Col([
                            html.Label("Date/heure de fin :",
                                       className="text-muted small"),
                            dbc.Input(id="delay-dt-end-input", 
                                    type="datetime-local",
                                    value=dt_max_iso, 
                                    min=dt_min_iso, 
                                    max=dt_max_iso,
                                    style={"width": "100%",
                                           'backgroundColor': '#263142',
                                           'color': '#cfd8e3',
                                           'border': '1px solid #3b465d'})
                        ], md=6),
                    ], className="mb-3"),

                    # Analyse button
                    dbc.Row([
                        dbc.Col(
                            dbc.Button("🔍 Analyser", id="delay-go-btn", color="primary",
                                       className="w-100", n_clicks=0, size="lg"),
                            md=12)
                    ]),
                ])
            ], className="mb-4", style={"background": "#1d2433"}),

            # Stats section
            html.H3("Statistiques", style={"color": "#dfe6f3", "fontSize": 20}),
            dbc.Card(
                html.Div(id="delay-stats-div", className="p-3"),
                className="mb-4",
                style={"background": "#1d2433"}
            ),

            # Data table
            html.H3("📋 Détail des codes de retard",
                    style={"color": "#dfe6f3", "fontSize": 20}),
            html.Div(id="delay-table-container", style={"maxHeight": "400px", "overflowY": "auto"})
        ],
        style={"paddingRight": "20px"}
    )

    right_panel = [
        html.H2("TOP 10 codes de retard", className="mb-3",
                style={"color": "#dfe6f3", "fontSize": 24}),
        dbc.Card(
            dcc.Graph(id="delay-codes-chart", style={"height": "70vh"}),
            style={"background": "#1d2433"}
        )
    ]

    return dbc.Container(fluid=True, className="px-4", children=[
        dcc.Store(id="delay-filtered-store"),

        # Header strip & dataset size
        dbc.Row(dbc.Col(html.P(
            f"Base de données : {df_filtered.height:,} vols TEC chargés",
            className="text-end text-muted small mt-2"))),

        # Two-pane zone with 60/40 split
        dbc.Row([
            dbc.Col(left_panel,  md=7, lg=7,
                    className="d-flex flex-column vh-100 overflow-auto"),
            dbc.Col(right_panel, md=5, lg=5,
                    className="d-flex flex-column vh-100 overflow-auto")
        ], className="pt-3"),

        # Footer
        dbc.Row(dbc.Col([
            html.Hr(style={"height": 1, "background": "#202736", "border": 0}),
            html.P(f"Dernière mise à jour : {datetime.now():%d/%m/%Y %H:%M}",
                   className="text-center text-muted small")
        ], className="mt-2"))
    ])

# Create the layout function that will be called dynamically
def get_layout():
    return create_delay_codes_layout()

# For compatibility with the current system
layout = get_layout()
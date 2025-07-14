import dash
from dash import html, dcc, dash_table
from dash.dependencies import Input, Output, State

import dash_bootstrap_components as dbc

from dashboard.server_instance import get_app

from excel_manager import get_df, path_exits

app = get_app()


# Données pour les éléments de navigation
if path_exits():
    import dashboard.pages.home.page as home
    import dashboard.pages.tech.page as tech
    import dashboard.pages.tech.delay_codes as delay_codes
    import dashboard.pages.config.data_config as data_config
    nav_items = [
        {"name": "Dashboard", "icon": "fas fa-home", "href": "/", "page": home.layout},
        {"name": "Analytics", "icon": "fas fa-chart-line", "href": "/analytics", "page": tech.layout},
        {"name": "Delay Codes", "icon": "fas fa-clock", "href": "/delay-codes", "page": delay_codes.layout},
        {"name": "Config", "icon": "fas fa-folder-open", "href": "/config", "page": data_config.layout},
        {"name": "Settings", "icon": "fas fa-cog", "href": "/settings", "page": html.Div("Paramètres")},
    ]
else:
    import dashboard.pages.verify.page as verify

    nav_items = [
        {
            "name": "verify",
            "icon": "fas fa-home",
            "href": "/",
            "page": verify.layout,
            "show": False,
        }
    ]

navbar = dbc.Nav(
    children=[
        dbc.NavItem(dbc.NavLink(nav_item["name"], href=nav_item["href"]))
        for nav_item in nav_items
        if nav_item.get("show", True)
    ],
    className="justify-content-center nav-tabs",
    id="navbar",
)


app.layout = html.Div(
    [
        # Barre de navigation
        navbar,
        # Contenu principal
        html.Div(id="page-content"),
        # Stockage pour suivre l'état du menu
        dcc.Location(id="url"),
    ]
)


@app.callback(Output("navbar", "children"), Input("url", "pathname"))
def update_navbar(pathname):

    return [
        dbc.NavItem(
            dbc.NavLink(
                nav_item["name"],
                href=nav_item["href"],
                active=pathname == nav_item["href"],
            )
        )
        for nav_item in nav_items
        if nav_item.get("show", True)
    ]


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page(pathname):
    for nav_item in nav_items:
        if pathname == nav_item["href"]:
            # Special handling for dynamic pages to reload data/config
            if pathname == "/delay-codes":
                return delay_codes.get_layout()
            elif pathname == "/config":
                return data_config.get_layout()
            return nav_item["page"]

# ------------------------------------------------------------------ #
# Delay Codes Callbacks                                             #
# ------------------------------------------------------------------ #
from datetime import datetime
import polars as pl

# Import the delay codes functions
from dashboard.pages.tech.delay_codes import analyze_delay_codes_polars, get_data_info

# Filter & store callback
@app.callback(
    Output("delay-filtered-store", "data"),
    Input("delay-go-btn", "n_clicks"),
    State("delay-flotte-dd", "value"),
    State("delay-matricule-dd", "value"),
    State("delay-code-dd", "value"),
    State("delay-dt-start-input", "value"),
    State("delay-dt-end-input", "value"),
    prevent_initial_call=False
)
def filter_delay_data(n_clicks, fl_sel, mat_sel, code_sel, dt_start, dt_end):
    """Filter data based on user selections"""
    # Get fresh data
    df_filtered, flottes, matricules, codes_dr, dt_min_iso, dt_max_iso = get_data_info()
    
    if df_filtered.is_empty():
        return {"payload": [], "count": 0}
    
    df = df_filtered
    
    # Apply filters
    if fl_sel:
        df = df.filter(pl.col("AC_SUBTYPE").is_in(fl_sel))
    if mat_sel:
        df = df.filter(pl.col("AC_REGISTRATION").is_in(mat_sel))
    if code_sel:
        df = df.filter(pl.col("CODE_DR").is_in(code_sel))
    
    # Datetime filtering
    if dt_start:
        df = df.filter(pl.col("DEP_DATETIME") >= datetime.fromisoformat(dt_start))
    if dt_end:
        df = df.filter(pl.col("DEP_DATETIME") <= datetime.fromisoformat(dt_end))
    
    # Convert to dict for JSON serialization
    return {
        "payload": df.to_dicts(), 
        "count": df.height,
        "timestamp": datetime.now().isoformat(),
        "nonce": n_clicks
    }

# Outputs callback
@app.callback(
    [Output("delay-stats-div", "children"),
     Output("delay-codes-chart", "figure"),
     Output("delay-table-container", "children")],
    Input("delay-filtered-store", "data"),
    prevent_initial_call=False
)
def build_delay_outputs(store_data):
    """Build all output components based on filtered data"""
    
    # Get fresh data
    df_filtered, flottes, matricules, codes_dr, dt_min_iso, dt_max_iso = get_data_info()
    
    # Handle initial load or empty data
    if not store_data or not store_data.get("payload"):
        df = df_filtered
    else:
        df = pl.DataFrame(store_data["payload"])
    
    # Get analysis
    summary = analyze_delay_codes_polars(df)
    
    # 1. Build stats
    total_flights = df.height
    unique_codes = summary.height if not summary.is_empty() else 0
    total_delays = summary["Occurrences"].sum() if not summary.is_empty() else 0
    
    stats = dbc.Row([
        dbc.Col([
            html.H5("Vols analysés", className="text-muted"),
            html.H3(f"{total_flights:,}", className="text-primary mb-0")
        ], md=4),
        dbc.Col([
            html.H5("Codes uniques", className="text-muted"),
            html.H3(f"{unique_codes}", className="text-success mb-0")
        ], md=4),
        dbc.Col([
            html.H5("Total retards", className="text-muted"),
            html.H3(f"{total_delays:,}", className="text-warning mb-0")
        ], md=4)
    ])
    
    # 2. Build chart
    import plotly.graph_objects as go
    if summary.is_empty():
        fig = go.Figure()
        fig.add_annotation(
            text="Aucun code de retard trouvé",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="#a0a7b9")
        )
    else:
        top10 = summary.head(10)
        fig = go.Figure(go.Bar(
            x=top10["Occurrences"].to_list(),
            y=top10["CODE_DR"].to_list(),
            orientation="h",
            marker_color="#10c5ff",
            text=[f"{desc[:30]}..." if len(desc) > 30 else desc 
                  for desc in top10["Description"].to_list()],
            textposition="auto",
            hovertemplate="<b>Code %{y}</b><br>" +
                          "Occurrences: %{x}<br>" +
                          "Description: %{text}<br>" +
                          "<extra></extra>"
        ))
    
    fig.update_layout(
        template="plotly_dark",
        height=600,
        margin=dict(l=50, r=20, t=40, b=40),
        yaxis=dict(categoryorder="total ascending", title="Code"),
        xaxis_title="Occurrences",
        font=dict(size=12)
    )
    
    # 3. Build table
    if summary.is_empty():
        table = dbc.Alert("Aucun code de retard trouvé dans la sélection", 
                         color="warning", className="text-center")
    else:
        # Rename columns for display
        summary = summary.rename({"CODE_DR": "Code", "Nb_AP": "Nb Aéroports"})
        
        table = dash_table.DataTable(
            id="delay-codes-table",
            data=summary.to_dicts(),
            columns=[{"name": col, "id": col} for col in summary.columns],
            style_header={
                "background": "#263142", 
                "color": "#cfd8e3",
                "fontWeight": "bold",
                "borderTop": "1px solid #3b465d",
                "fontSize": "12px"
            },
            style_cell={
                "background": "#1d2433", 
                "color": "#cfd8e3",
                "borderTop": "1px solid #3b465d",
                "textAlign": "left",
                "padding": "8px",
                "fontSize": "11px",
                "whiteSpace": "normal",
                "height": "auto"
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#263142'
                },
                {
                    'if': {'column_id': 'Aéroports'},
                    'textAlign': 'left',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'minWidth': '200px'
                }
            ],
            sort_action="native",
            filter_action="native",
            page_size=8,
            export_format="csv",
            style_table={'height': '350px', 'overflowY': 'auto'}
        )
    
    return stats, fig, table

# Update matricule options based on selected fleet
@app.callback(
    Output("delay-matricule-dd", "options"),
    Input("delay-flotte-dd", "value")
)
def update_delay_matricules(selected):
    """Update matricule dropdown based on selected fleet"""
    # Get fresh data
    df_filtered, flottes, matricules, codes_dr, dt_min_iso, dt_max_iso = get_data_info()
    
    if not selected or df_filtered.is_empty():
        return [{"label": m, "value": m} for m in matricules]
    
    tmp = (df_filtered
           .filter(pl.col("AC_SUBTYPE").is_in(selected))
           .get_column("AC_REGISTRATION")
           .drop_nulls()
           .unique()
           .sort()
           .to_list())
    return [{"label": m, "value": m} for m in tmp]

# Update code options based on other filters
@app.callback(
    Output("delay-code-dd", "options"),
    [Input("delay-flotte-dd", "value"),
     Input("delay-matricule-dd", "value")]
)
def update_delay_codes(fl_sel, mat_sel):
    """Update code dropdown based on other selections"""
    # Get fresh data
    df_filtered, flottes, matricules, codes_dr, dt_min_iso, dt_max_iso = get_data_info()
    
    if df_filtered.is_empty():
        return []
    
    df = df_filtered
    
    if fl_sel:
        df = df.filter(pl.col("AC_SUBTYPE").is_in(fl_sel))
    if mat_sel:
        df = df.filter(pl.col("AC_REGISTRATION").is_in(mat_sel))
    
    available_codes = df.get_column("CODE_DR").drop_nulls().unique().sort().to_list()
    return [{"label": c, "value": c} for c in available_codes]

# ------------------------------------------------------------------ #
# Configuration Callbacks                                           #
# ------------------------------------------------------------------ #
import json
from pathlib import Path

# File status callback
@app.callback(
    Output("file-status-div", "children"),
    [Input("file-path-input", "value"),
     Input("sheet-name-input", "value")]
)
def update_file_status(file_path, sheet_name):
    """Update file status display"""
    if not file_path:
        return dbc.Alert("Aucun fichier sélectionné", color="secondary")
    
    file_path_obj = Path(file_path)
    
    if not file_path_obj.exists():
        return dbc.Alert(f"❌ Fichier introuvable: {file_path}", color="danger")
    
    if not file_path_obj.suffix.lower() in ['.xlsx', '.xls']:
        return dbc.Alert("⚠️ Le fichier doit être un fichier Excel (.xlsx ou .xls)", color="warning")
    
    try:
        import polars as pl
        # Try to read the file to validate it
        df_test = pl.read_excel(file_path, sheet_name=sheet_name or "Sheet1")
        row_count = df_test.height
        col_count = df_test.width
        
        return dbc.Alert([
            html.P(f"✅ Fichier valide: {file_path}"),
            html.P(f"📊 Feuille '{sheet_name}': {row_count:,} lignes, {col_count} colonnes")
        ], color="success")
    except Exception as e:
        return dbc.Alert(f"❌ Erreur lors de la lecture: {str(e)}", color="danger")

# Save configuration callback
@app.callback(
    Output("config-status-message", "children"),
    Input("save-config-button", "n_clicks"),
    [State("file-path-input", "value"),
     State("sheet-name-input", "value")],
    prevent_initial_call=True
)
def save_configuration(n_clicks, file_path, sheet_name):
    """Save configuration to file"""
    if n_clicks and file_path:
        config = {
            "file_path": file_path,
            "sheet_name": sheet_name or "Sheet1"
        }
        
        try:
            with open("dashboard_config.json", 'w') as f:
                json.dump(config, f, indent=2)
            
            return dbc.Alert([
                html.P("✅ Configuration sauvegardée avec succès!"),
                html.P("Vous pouvez maintenant utiliser la page Delay Codes.")
            ], color="success", dismissable=True)
        except Exception as e:
            return dbc.Alert(f"❌ Erreur lors de la sauvegarde: {str(e)}", color="danger")
    
    return ""


if __name__ == '__main__':
    app.run(debug=True)

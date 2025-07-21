"""
weekly_analysis_page.py – Weekly Analysis of Delay Codes
"""

import polars as pl
from datetime import datetime
import dash
from dash import html, dcc, dash_table, Input, Output, State, ctx, no_update
import dash_bootstrap_components as dbc
from dashboard.server_instance import get_app
from dashboard import excel_manager
from datetime import timedelta
import io
import xlsxwriter
from dash.dcc import send_bytes

app = get_app()

# ------------------------------------------------------------------ #
# 1 ▸  Read & prepare data                                           #
# ------------------------------------------------------------------ #

try:
    df_lazy = excel_manager.get_df()
    
    if df_lazy is None:
        raise Exception("No data available from excel_manager")
    
    # Normalise column names
    col_map = {
        c: "_".join(c.strip().split()).upper() for c in df_lazy.collect_schema().names()
    }
    df_lazy = df_lazy.rename(col_map)

    # Ensure DEP_DAY_SCHED is properly formatted as date
    df_lazy = df_lazy.with_columns(
        pl.col("DEP_DAY_SCHED").cast(pl.Date).alias("DEP_DATE")
    )

    # Keep only delay-code rows with TEC description
    df_filtered = df_lazy.filter(pl.col("LIB_CODE_DR") == "TEC").collect()

    print(f"✅ Weekly analysis data loaded: {df_filtered.height} rows with TEC codes")

except Exception as e:
    print(f"❌ Error loading data for weekly analysis: {e}")
    df_filtered = pl.DataFrame()

# Dropdown lists
flottes = (
    sorted(df_filtered.get_column("AC_SUBTYPE").drop_nulls().unique().to_list())
    if not df_filtered.is_empty()
    else []
)
matricules = (
    sorted(df_filtered.get_column("AC_REGISTRATION").drop_nulls().unique().to_list())
    if not df_filtered.is_empty()
    else []
)
codes_dr = (
    sorted(df_filtered.get_column("CODE_DR").drop_nulls().unique().to_list())
    if not df_filtered.is_empty()
    else []
)

# Date input bounds
if not df_filtered.is_empty():
    dt_min, dt_max = (
        df_filtered.get_column("DEP_DATE").min(),
        df_filtered.get_column("DEP_DATE").max(),
    )
else:
    dt_min = dt_max = datetime.now().date()

dt_min = dt_min or datetime.now().date()
dt_max = dt_max or datetime.now().date()
dt_min_iso, dt_max_iso = (
    dt_min.strftime("%Y-%m-%d"),
    dt_max.strftime("%Y-%m-%d"),
)

# 1) Start-date input
start_min   = dt_min
start_max   = dt_max - timedelta(days=7)   # never allow start > dt_max−7
start_value = dt_min + timedelta(days=1)                      # default is the very first day

# 2) End-date input
                    # never allow end < dt_min
end_max     = dt_min + timedelta(days=7)
end_min     = end_max   # default upper bound = start + 7d
end_value   = end_max                      # default value

# Edge‐case safeguard: if your overall range is <7 days, clamp so max≥min
if start_max < start_min:
    start_max = start_min
if end_max < end_min:
    end_max = end_min

# Convert all to ISO strings
start_min_iso   = start_min.isoformat()
start_max_iso   = start_max.isoformat()
start_value_iso = start_value.isoformat()

end_min_iso     = end_min.isoformat()
end_max_iso     = end_max.isoformat()
end_value_iso   = end_value.isoformat()
# ------------------------------------------------------------------ #
# 2 ▸  Helper functions                                              #
# ------------------------------------------------------------------ #

def get_day_of_week(date_val):
    """Get day of week name from date"""
    if isinstance(date_val, str):
        date_obj = datetime.fromisoformat(date_val).date()
    else:
        date_obj = date_val
    
    # Return French day names
    days = {
        0: "Lundi",
        1: "Mardi", 
        2: "Mercredi",
        3: "Jeudi",
        4: "Vendredi",
        5: "Samedi",
        6: "Dimanche"
    }
    return days[date_obj.weekday()]

def analyze_weekly_codes(frame: pl.DataFrame) -> pl.DataFrame:
    """
    Analyze delay codes by day of week.
    Returns DataFrame with codes as rows and days as columns.
    """
    if frame.is_empty():
        return pl.DataFrame()
    
    # Add day of week column
    df_with_days = frame.with_columns(
        pl.col("DEP_DATE").map_elements(get_day_of_week, return_dtype=pl.Utf8).alias("day_of_week")
    )
    
    # Group by code and day of week
    weekly_data = (
        df_with_days
        .group_by(["CODE_DR", "day_of_week"])
        .agg(pl.len().alias("count"))
        .sort(["CODE_DR", "day_of_week"])
    )
    
    if weekly_data.is_empty():
        return pl.DataFrame()
    
    # Create pivot table with codes as rows and days as columns
    days_order = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    unique_codes = weekly_data["CODE_DR"].unique().sort().to_list()
    
    # Create the pivot table manually
    pivot_data = []
    for code in unique_codes:
        row = {"CODE_DR": code}
        code_data = weekly_data.filter(pl.col("CODE_DR") == code)
        
        for day in days_order:
            day_data = code_data.filter(pl.col("day_of_week") == day)
            count = day_data["count"].sum() if not day_data.is_empty() else 0
            row[day] = count
        
        # Add total
        row["Total"] = sum(row[day] for day in days_order)
        pivot_data.append(row)
    
    return pl.DataFrame(pivot_data).sort("Total", descending=True)

# ------------------------------------------------------------------ #
# 3 ▸  Layout                                                       #
# ------------------------------------------------------------------ #

def get_layout():
    """Get the layout with current Monday dates"""
    return dbc.Container(
    fluid=True,
    className="px-4",
    children=[
        dcc.Store(id="weekly-filtered-store"),
        
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("ANALYSE HEBDOMADAIRE DES CODES DE RETARD", className="mb-2"),
                html.P("Analysez la répartition des codes de retard par jour de la semaine.", className="lead mb-4"),
            ]),
            dbc.Col(
                html.P(f"Base de données : {df_filtered.height:,} vols TEC chargés", className="text-end text-muted small mt-2"),
                width="auto"
            ),
        ]),
        
        # Filters Card
        dbc.Card(
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Type d'avion (Flotte)", className="form-label"),
                        dcc.Dropdown(
                            id="weekly-flotte-dd",
                            options=[{"label": f, "value": f} for f in flottes],
                            multi=True,
                            placeholder="Tous les types",
                        ),
                    ], md=4),
                    dbc.Col([
                        html.Label("Matricule", className="form-label"),
                        dcc.Dropdown(
                            id="weekly-matricule-dd",
                            options=[{"label": m, "value": m} for m in matricules],
                            multi=True,
                            placeholder="Tous les matricules",
                        ),
                    ], md=4),
                    
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Date de début", className="form-label"),
                        dbc.Input(
                            id="weekly-dt-start",
                            type="date",
                            value=start_value_iso,
                            min=start_min_iso,
                            max=start_max_iso,
                        ),
                    ], md=3),
                    dbc.Col([
                        html.Label("Date de fin", className="form-label"),
                        dbc.Input(
                            id="weekly-dt-end",
                            type="date",
                            value=end_value_iso,
                            min=end_min_iso,
                            max=end_max_iso,
                        ),
                    ], md=3),
                    dbc.Col([
                        html.Label("", className="form-label"),
                        dbc.Button(
                            "🔍 Analyser",
                            id="weekly-analyze-btn",
                            color="primary",
                            size="lg",
                            className="w-100",
                            n_clicks=0,
                        ),
                    ], md=3),
                    dbc.Col([
                        html.Label("", className="form-label"),
                        dbc.Button(
                            "📋 Exporter Excel",
                            id="weekly-export-btn",
                            color="success",
                            size="lg",
                            className="w-100",
                            n_clicks=0,
                        ),
                    ], md=3),
                ], className="mb-3"),
            ]),
            className="mb-4",
        ),
        
        # Results Table
        dbc.Card(
            dbc.CardBody([
                html.H3("📊 Analyse hebdomadaire", className="h4 mb-3"),
                html.Div(
                    id="weekly-table-container",
                    style={"maxHeight": "600px", "overflowY": "auto"}
                ),
            ]),
            className="mb-4",
        ),
        
        # Download component
        dcc.Download(id="weekly-download"),
        
        # Footer
        dbc.Row(
            dbc.Col([
                html.Hr(),
                html.P(f"Dernière mise à jour : {datetime.now():%d/%m/%Y %H:%M}", className="text-center text-muted small"),
            ], className="mt-2")
        ),
    ],
)
layout = get_layout()
# ------------------------------------------------------------------ #
# 4 ▸  Callbacks                                                    #
# ------------------------------------------------------------------ #

@app.callback(
    Output("weekly-filtered-store", "data"),
    Input("weekly-analyze-btn", "n_clicks"),
    State("weekly-flotte-dd", "value"),
    State("weekly-matricule-dd", "value"),

    State("weekly-dt-start", "value"),
    State("weekly-dt-end", "value"),
    prevent_initial_call=False,
)
def filter_weekly_data(n_clicks, fl_sel, mat_sel, dt_start, dt_end):
    """Filter data for weekly analysis"""
    if df_filtered.is_empty():
        return {"payload": []}
    
    df = df_filtered
    
    # Apply filters
    if fl_sel:
        df = df.filter(pl.col("AC_SUBTYPE").is_in(fl_sel))
    if mat_sel:
        df = df.filter(pl.col("AC_REGISTRATION").is_in(mat_sel))
    
    
    # Date filtering
    if dt_start:
        df = df.filter(pl.col("DEP_DATE") >= datetime.fromisoformat(dt_start).date())
    if dt_end:
        df = df.filter(pl.col("DEP_DATE") <= datetime.fromisoformat(dt_end).date())
    
    return {
        "payload": df.to_dicts(),
        "timestamp": datetime.now().isoformat(),
    }

@app.callback(
    Output("weekly-table-container", "children"),
    Input("weekly-filtered-store", "data"),
    prevent_initial_call=False,
)
def update_weekly_table(store_data):
    """Update weekly analysis table"""
    
    if not store_data or not store_data.get("payload"):
        return dbc.Alert(
            "Aucune donnée à afficher. Utilisez les filtres et cliquez sur 'Analyser'.",
            color="info",
            className="text-center",
        )
    
    df = pl.DataFrame(store_data["payload"])
    
    # Ensure DEP_DATE is properly converted to date if it's a string
    if df.height > 0:
        if df.get_column("DEP_DATE").dtype == pl.Utf8:
            df = df.with_columns(
                pl.col("DEP_DATE").str.strptime(pl.Date, "%Y-%m-%d", strict=False)
            )
    
    # Create weekly analysis
    weekly_analysis = analyze_weekly_codes(df)
    
    if weekly_analysis.is_empty():
        return dbc.Alert(
            "Aucun code de retard trouvé pour les critères sélectionnés.",
            color="warning",
            className="text-center",
        )
    
    # Create table
    columns = [
        {"name": "Code de retard", "id": "CODE_DR"},
        {"name": "Lundi", "id": "Lundi"},
        {"name": "Mardi", "id": "Mardi"},
        {"name": "Mercredi", "id": "Mercredi"},
        {"name": "Jeudi", "id": "Jeudi"},
        {"name": "Vendredi", "id": "Vendredi"},
        {"name": "Samedi", "id": "Samedi"},
        {"name": "Dimanche", "id": "Dimanche"},
        {"name": "Total", "id": "Total"},
    ]
    
    return dash_table.DataTable(
        data=weekly_analysis.to_dicts(),
        columns=columns,
        style_header={
            "backgroundColor": "#f8f9fa",
            "color": "#495057",
            "fontWeight": "bold",
            "border": "1px solid #dee2e6",
            "textAlign": "center",
        },
        style_cell={
            "backgroundColor": "white",
            "color": "#495057",
            "border": "1px solid #dee2e6",
            "textAlign": "center",
            "padding": "8px",
            "fontSize": "11px",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"},
            {"if": {"column_id": "CODE_DR"}, "textAlign": "left", "fontWeight": "bold"},
            {"if": {"column_id": "Total"}, "backgroundColor": "#e3f2fd", "fontWeight": "bold"},
        ],
        sort_action="native",
        filter_action="native",
        page_size=15,
        style_table={"overflowX": "auto"},
    )


@app.callback(
    Output("weekly-download", "data"),
    Input("weekly-export-btn", "n_clicks"),
    State("weekly-filtered-store", "data"),
    State("weekly-flotte-dd",    "value"),
    State("weekly-matricule-dd", "value"),
    State("weekly-dt-start",     "value"),
    prevent_initial_call=True,
)
def export_weekly_data(n_clicks, store_data, flotte_vals, matricule_vals, date_start):
    if not store_data or not store_data.get("payload"):
        return no_update

    df = pl.DataFrame(store_data["payload"])
    weekly_analysis = analyze_weekly_codes(df)
    if weekly_analysis.is_empty():
        return no_update

    # build filename
    matricule = "_".join(matricule_vals) if matricule_vals else "all"
    flotte    = "_".join(flotte_vals)    if flotte_vals    else "all"
    ts = date_start.replace("-", "_")
    filename  = f"weekly_analysis_{matricule}_{flotte}_{ts}.xlsx"

    # write Polars -> Excel in-memory
    buf = io.BytesIO()
    with xlsxwriter.Workbook(buf, {"in_memory": True}) as workbook:
        weekly_analysis.write_excel(workbook=workbook)
    buf.seek(0)

    # **Corrected send_bytes usage**:
    return send_bytes(
        lambda out_io: out_io.write(buf.getvalue()),
        filename=filename
    )
@app.callback(
    Output("weekly-matricule-dd", "options"),
    Input("weekly-flotte-dd", "value")
)
def update_weekly_matricules(selected):
    """Update matricule dropdown based on selected fleet"""
    if not selected or df_filtered.is_empty():
        return [{"label": m, "value": m} for m in matricules]
    
    tmp = (
        df_filtered.filter(pl.col("AC_SUBTYPE").is_in(selected))
        .get_column("AC_REGISTRATION")
        .drop_nulls()
        .unique()
        .sort()
        .to_list()
    )
    return [{"label": m, "value": m} for m in tmp]




@app.callback(
    Output("weekly-dt-end", "min"),
    Output("weekly-dt-end", "max"),
    Output("weekly-dt-end", "value"),
    Input("weekly-dt-start", "value"),
    prevent_initial_call=True,
)
def sync_end_to_start(start_iso):
    if not start_iso:
        raise dash.exceptions.PreventUpdate

    d0 = datetime.fromisoformat(start_iso).date()
    min_end = d0
    max_end = d0 + timedelta(days=6)

    # clamp if beyond your overall dt_max
    if max_end > dt_max:
        max_end = dt_max

    iso_min = min_end.isoformat()
    iso_max = max_end.isoformat()
    return iso_min, iso_max, iso_max
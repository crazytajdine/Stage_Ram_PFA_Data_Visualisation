"""
delay_codes_app.py  –  Dash + Polars  •  Darkly theme
"""

import polars as pl
from pathlib import Path
from datetime import datetime
import dash
from dash import Dash, html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import json
from server_instance import get_app


app = get_app()
# ------------------------------------------------------------------ #
# 1 ▸  Read & prepare data                                           #
# ------------------------------------------------------------------ #
SRC = Path("data.xlsx")
SHEET = "Sheet1"

try:
    # Lazy read once
    df_lazy = pl.read_excel(SRC, sheet_name=SHEET).lazy()

    # Normalise column names
    col_map = {
        c: "_".join(c.strip().split()).upper() for c in df_lazy.collect_schema().names()
    }
    df_lazy = df_lazy.rename(col_map)

    # Build unified DEP_DATETIME (supports HH:MM:SS or HH:MM)
    df_lazy = df_lazy.with_columns(
        (
            pl.col("DEP_DAY_SCHED").cast(pl.Utf8)
            + " "
            + pl.when(pl.col("DEP_TIME_SCHED").str.len_chars() == 5)
            .then(pl.col("DEP_TIME_SCHED") + ":00")
            .otherwise(pl.col("DEP_TIME_SCHED"))
        )
        .str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False)
        .alias("DEP_DATETIME")
    )

    # Keep only delay-code rows with TEC description
    df_filtered = df_lazy.filter(pl.col("LIB_CODE_DR") == "TEC").collect()

    print(f"✅ Data loaded: {df_filtered.height} rows with TEC codes")

except Exception as e:
    print(f"❌ Error loading data: {e}")
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

# Datetime input bounds
if not df_filtered.is_empty():
    dt_min, dt_max = (
        df_filtered.get_column("DEP_DATETIME").min(),
        df_filtered.get_column("DEP_DATETIME").max(),
    )
else:
    dt_min = dt_max = datetime.now()

dt_min = dt_min or datetime.now()
dt_max = dt_max or datetime.now()
dt_min_iso, dt_max_iso = (
    dt_min.strftime("%Y-%m-%dT%H:%M"),
    dt_max.strftime("%Y-%m-%dT%H:%M"),
)


# ------------------------------------------------------------------ #
# 2 ▸  Helper – aggregate per code                                   #
# ------------------------------------------------------------------ #
def analyze_delay_codes_polars(frame: pl.DataFrame) -> pl.DataFrame:
    """
    Return a Polars frame with:
        CODE_DR | Occurrences | Description | Aéroports | Nb_AP
    """
    if frame.is_empty():
        return pl.DataFrame(
            {
                "CODE_DR": [],
                "Occurrences": [],
                "Description": [],
                "Aéroports": [],
                "Nb_AP": [],
            }
        )

    # First get airport counts per code
    airport_counts = frame.group_by(["CODE_DR", "DEP_AP_SCHED"]).agg(
        pl.len().alias("ap_count")
    )

    agg = (
        frame.group_by("CODE_DR")
        .agg(
            [
                pl.len().alias("Occurrences"),
                pl.col("LIB_CODE_DR").first().alias("Description"),
                pl.col("DEP_AP_SCHED").drop_nulls().alias("AP_list"),
            ]
        )
        .join(
            airport_counts.group_by("CODE_DR").agg(
                [
                    pl.col("DEP_AP_SCHED").alias("airports"),
                    pl.col("ap_count").alias("counts"),
                ]
            ),
            on="CODE_DR",
            how="left",
        )
        .with_columns(
            [
                pl.struct(["airports", "counts"])
                .map_elements(
                    lambda x: ", ".join(
                        [
                            f"{ap} ({cnt})"
                            for ap, cnt in sorted(
                                zip(x["airports"], x["counts"]),
                                key=lambda item: item[1],
                                reverse=True,
                            )[:15]
                        ]
                    )
                    + (
                        f" ... (+{len(x['airports'])-15} autres)"
                        if len(x["airports"]) > 15
                        else ""
                    ),
                    return_dtype=pl.Utf8,
                )
                .alias("Aéroports"),
                pl.col("AP_list").list.n_unique().alias("Nb_AP"),
            ]
        )
        .select(["CODE_DR", "Occurrences", "Description", "Aéroports", "Nb_AP"])
        .sort("Occurrences", descending=True)
    )
    return agg


# ------------------------------------------------------------------ #
# 3 ▸  Layout factory                                                #
# ------------------------------------------------------------------ #
def make_layout(total_vols: int) -> html.Div:
    left_panel = html.Div(
        [
            # Title & subtitle
            html.H1(
                "ANALYSE DES CODES DE RETARD",
                className="mb-2",
                style={"color": "#dfe6f3", "fontSize": 32},
            ),
            html.P(
                "Choisissez vos filtres pour explorer les codes de retard TEC.",
                className="lead",
                style={"color": "#a0a7b9"},
            ),
            # Filters section
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            # Flotte + Matricule
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label(
                                                "Type d'avion (Flotte)",
                                                className="text-muted small",
                                            ),
                                            dcc.Dropdown(
                                                id="flotte-dd",
                                                options=[
                                                    {"label": f, "value": f}
                                                    for f in flottes
                                                ],
                                                multi=True,
                                                placeholder="Tous les types",
                                                style={"zIndex": 1002},
                                                className="dash-dropdown",
                                            ),
                                        ],
                                        md=6,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label(
                                                "Matricule",
                                                className="text-muted small",
                                            ),
                                            dcc.Dropdown(
                                                id="matricule-dd",
                                                options=[
                                                    {"label": m, "value": m}
                                                    for m in matricules
                                                ],
                                                multi=True,
                                                placeholder="Tous les matricules",
                                                style={"zIndex": 1001},
                                                className="dash-dropdown",
                                            ),
                                        ],
                                        md=6,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Code DR filter
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label(
                                                "Code de retard",
                                                className="text-muted small",
                                            ),
                                            dcc.Dropdown(
                                                id="code-dd",
                                                options=[
                                                    {"label": c, "value": c}
                                                    for c in codes_dr
                                                ],
                                                multi=True,
                                                placeholder="Tous les codes",
                                                style={"zIndex": 1000},
                                                className="dash-dropdown",
                                            ),
                                        ],
                                        md=12,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Datetime inputs
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label(
                                                "Date/heure de début :",
                                                className="text-muted small",
                                            ),
                                            dbc.Input(
                                                id="dt-start-input",
                                                type="datetime-local",
                                                value=dt_min_iso,
                                                min=dt_min_iso,
                                                max=dt_max_iso,
                                                style={
                                                    "width": "100%",
                                                    "backgroundColor": "#263142",
                                                    "color": "#cfd8e3",
                                                    "border": "1px solid #3b465d",
                                                },
                                            ),
                                        ],
                                        md=6,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label(
                                                "Date/heure de fin :",
                                                className="text-muted small",
                                            ),
                                            dbc.Input(
                                                id="dt-end-input",
                                                type="datetime-local",
                                                value=dt_max_iso,
                                                min=dt_min_iso,
                                                max=dt_max_iso,
                                                style={
                                                    "width": "100%",
                                                    "backgroundColor": "#263142",
                                                    "color": "#cfd8e3",
                                                    "border": "1px solid #3b465d",
                                                },
                                            ),
                                        ],
                                        md=6,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Analyse button
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Button(
                                            "🔍 Analyser",
                                            id="go-btn",
                                            color="primary",
                                            className="w-100",
                                            n_clicks=0,
                                            size="lg",
                                        ),
                                        md=12,
                                    )
                                ]
                            ),
                        ]
                    )
                ],
                className="mb-4",
                style={"background": "#1d2433"},
            ),
            # Stats section
            html.H3("Statistiques", style={"color": "#dfe6f3", "fontSize": 20}),
            dbc.Card(
                html.Div(id="stats-div", className="p-3"),
                className="mb-4",
                style={"background": "#1d2433"},
            ),
            # Data table
            html.H3(
                "📋 Détail des codes de retard",
                style={"color": "#dfe6f3", "fontSize": 20},
            ),
            html.Div(
                id="table-container", style={"maxHeight": "400px", "overflowY": "auto"}
            ),
        ],
        style={"paddingRight": "20px"},
    )

    right_panel = [
        html.H2(
            "TOP 10 codes de retard",
            className="mb-3",
            style={"color": "#dfe6f3", "fontSize": 24},
        ),
        dbc.Card(
            dcc.Graph(id="codes-chart", style={"height": "70vh"}),
            style={"background": "#1d2433"},
        ),
    ]

    return dbc.Container(
        fluid=True,
        className="px-4",
        children=[
            dcc.Store(id="filtered-store"),
            # Header strip & dataset size
            dbc.Row(
                dbc.Col(
                    html.P(
                        f"Base de données : {total_vols:,} vols TEC chargés",
                        className="text-end text-muted small mt-2",
                    )
                )
            ),
            # Two-pane zone with 60/40 split
            dbc.Row(
                [
                    dbc.Col(
                        left_panel,
                        md=7,
                        lg=7,
                        className="d-flex flex-column vh-100 overflow-auto",
                    ),
                    dbc.Col(
                        right_panel,
                        md=5,
                        lg=5,
                        className="d-flex flex-column vh-100 overflow-auto",
                    ),
                ],
                className="pt-3",
            ),
            # Footer
            dbc.Row(
                dbc.Col(
                    [
                        html.Hr(
                            style={"height": 1, "background": "#202736", "border": 0}
                        ),
                        html.P(
                            f"Dernière mise à jour : {datetime.now():%d/%m/%Y %H:%M}",
                            className="text-center text-muted small",
                        ),
                    ],
                    className="mt-2",
                )
            ),
        ],
    )


# ------------------------------------------------------------------ #
# 4 ▸  Dash app & callbacks                                          #
# ------------------------------------------------------------------ #
layout = make_layout(total_vols=df_filtered.height)


# --- Filter & store ------------------------------------------------
@app.callback(
    Output("filtered-store", "data"),
    Input("go-btn", "n_clicks"),
    State("flotte-dd", "value"),
    State("matricule-dd", "value"),
    State("code-dd", "value"),
    State("dt-start-input", "value"),
    State("dt-end-input", "value"),
    prevent_initial_call=False,
)
def filter_data(n_clicks, fl_sel, mat_sel, code_sel, dt_start, dt_end):
    """Filter data based on user selections"""
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
        "nonce": n_clicks,
    }


# --- Outputs -------------------------------------------------------
@app.callback(
    [
        Output("stats-div", "children"),
        Output("codes-chart", "figure"),
        Output("table-container", "children"),
    ],
    Input("filtered-store", "data"),
    prevent_initial_call=False,
)
def build_outputs(store_data):
    """Build all output components based on filtered data"""

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

    stats = dbc.Row(
        [
            dbc.Col(
                [
                    html.H5("Vols analysés", className="text-muted"),
                    html.H3(f"{total_flights:,}", className="text-primary mb-0"),
                ],
                md=4,
            ),
            dbc.Col(
                [
                    html.H5("Codes uniques", className="text-muted"),
                    html.H3(f"{unique_codes}", className="text-success mb-0"),
                ],
                md=4,
            ),
            dbc.Col(
                [
                    html.H5("Total retards", className="text-muted"),
                    html.H3(f"{total_delays:,}", className="text-warning mb-0"),
                ],
                md=4,
            ),
        ]
    )

    # 2. Build chart
    if summary.is_empty():
        fig = go.Figure()
        fig.add_annotation(
            text="Aucun code de retard trouvé",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color="#a0a7b9"),
        )
    else:
        top10 = summary.head(10)
        fig = go.Figure(
            go.Bar(
                x=top10["Occurrences"].to_list(),
                y=top10["CODE_DR"].to_list(),
                orientation="h",
                marker_color="#10c5ff",
                text=[
                    f"{desc[:30]}..." if len(desc) > 30 else desc
                    for desc in top10["Description"].to_list()
                ],
                textposition="auto",
                hovertemplate="<b>Code %{y}</b><br>"
                + "Occurrences: %{x}<br>"
                + "Description: %{text}<br>"
                + "<extra></extra>",
            )
        )

    fig.update_layout(
        template="plotly_dark",
        height=600,
        margin=dict(l=50, r=20, t=40, b=40),
        yaxis=dict(categoryorder="total ascending", title="Code"),
        xaxis_title="Occurrences",
        font=dict(size=12),
    )

    # 3. Build table
    if summary.is_empty():
        table = dbc.Alert(
            "Aucun code de retard trouvé dans la sélection",
            color="warning",
            className="text-center",
        )
    else:
        # Rename columns for display
        summary = summary.rename({"CODE_DR": "Code", "Nb_AP": "Nb Aéroports"})

        table = dash_table.DataTable(
            id="codes-table",
            data=summary.to_dicts(),
            columns=[{"name": col, "id": col} for col in summary.columns],
            style_header={
                "background": "#263142",
                "color": "#cfd8e3",
                "fontWeight": "bold",
                "borderTop": "1px solid #3b465d",
                "fontSize": "12px",
            },
            style_cell={
                "background": "#1d2433",
                "color": "#cfd8e3",
                "borderTop": "1px solid #3b465d",
                "textAlign": "left",
                "padding": "8px",
                "fontSize": "11px",
                "whiteSpace": "normal",
                "height": "auto",
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#263142"},
                {
                    "if": {"column_id": "Aéroports"},
                    "textAlign": "left",
                    "whiteSpace": "normal",
                    "height": "auto",
                    "minWidth": "200px",
                },
            ],
            sort_action="native",
            filter_action="native",
            page_size=8,
            export_format="csv",
            style_table={"height": "350px", "overflowY": "auto"},
        )

    return stats, fig, table


# --- Update matricule options based on selected fleet --------------
@app.callback(Output("matricule-dd", "options"), Input("flotte-dd", "value"))
def update_matricules(selected):
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


# --- Update code options based on other filters --------------------
@app.callback(
    Output("code-dd", "options"),
    [Input("flotte-dd", "value"), Input("matricule-dd", "value")],
)
def update_codes(fl_sel, mat_sel):
    """Update code dropdown based on other selections"""
    if df_filtered.is_empty():
        return []

    df = df_filtered

    if fl_sel:
        df = df.filter(pl.col("AC_SUBTYPE").is_in(fl_sel))
    if mat_sel:
        df = df.filter(pl.col("AC_REGISTRATION").is_in(mat_sel))

    available_codes = df.get_column("CODE_DR").drop_nulls().unique().sort().to_list()
    return [{"label": c, "value": c} for c in available_codes]


# Custom CSS for dropdowns
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Style for dropdown containers */
            .dash-dropdown .Select-control {
                background-color: #263142 !important;
                border-color: #3b465d !important;
            }
            .dash-dropdown .Select-value-label,
            .dash-dropdown .Select-placeholder {
                color: #cfd8e3 !important;
            }
            .dash-dropdown .Select-menu-outer {
                background-color: #263142 !important;
                border-color: #3b465d !important;
            }
            .dash-dropdown .Select-option {
                background-color: #263142 !important;
                color: #cfd8e3 !important;
            }
            .dash-dropdown .Select-option.is-focused,
            .dash-dropdown .Select-option:hover {
                background-color: #3b465d !important;
            }
            .dash-dropdown .Select-multi-value-wrapper {
                background-color: #263142 !important;
            }
            .dash-dropdown .Select-value {
                background-color: #3b465d !important;
                color: #cfd8e3 !important;
            }
            .dash-dropdown .Select-value-icon {
                border-right-color: #6c757d !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

# ------------------------------------------------------------------ #

"""
delay_codes_app.py  –  Dash + Polars  •  Darkly theme
"""

import polars as pl
from pathlib import Path
from datetime import datetime, timedelta
import dash
from dash import Dash, html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import json
from server_instance import get_app
from dashboard import excel_manager
from dashboard.excel_manager import df_all

app = get_app()
# ------------------------------------------------------------------ #
# 1 ▸  Read & prepare data                                           #
# ------------------------------------------------------------------ #


try:
    # Lazy read once
    df_lazy= excel_manager.df

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
                            )
                        ]
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


def analyze_delay_codes_for_table(frame: pl.DataFrame) -> pl.DataFrame:
    """
    Return delay codes analysis for table (independent of code selection)
    Only filtered by flotte, dates, and matricule
    """
    if frame.is_empty():
        return pl.DataFrame(
            {
                "CODE_DR": [],
                "Occurrences": [],
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
                            )
                        ]
                    ),
                    return_dtype=pl.Utf8,
                )
                .alias("Aéroports"),
                pl.col("AP_list").list.n_unique().alias("Nb_AP"),
            ]
        )
        .select(["CODE_DR", "Occurrences", "Aéroports", "Nb_AP"])
        .sort("Occurrences", descending=True)
    )
    return agg


# ---------- 2. Helper ----------
def compute_divisors(start: str | None, end: str | None) -> list[int]:
    """
    Return every integer d (≥1) that divides D, where
    D = whole-day distance between start and end dates.
    When dates are invalid or D ≤ 0, return [].
    """
    if not start or not end:
        return []
    try:
        d0 = datetime.fromisoformat(start[:10])  # strip time portion if present
        d1 = datetime.fromisoformat(end[:10])
    except ValueError:
        return []

    D = (d1 - d0).days + 1            # inclusive: end date minus start date plus 1
    if D <= 0:
        return []

    return [d for d in range( 1, D + 1) if D % d == 0]


"""
It adds a new column to your table that tells you which time period each row belongs to,
    based on the date and how you chose to segment the total duration.

---------------I am talking about the following function---------------

"""
def create_time_segments(df: pl.DataFrame, dt_start: str, dt_end: str, segmentation: int | None) -> pl.DataFrame:
    """
    Add time period column to dataframe based on segmentation.
    If segmentation is None, use the whole duration as one period.
    """
    if df.is_empty():
        return df
    
    if segmentation is None:
        # No segmentation - whole duration is one period
        return df.with_columns(pl.lit("All Period").alias("time_period"))
    
    # Convert start/end to dates
    start_date = datetime.fromisoformat(dt_start[:10]).date()
    end_date = datetime.fromisoformat(dt_end[:10]).date()
    
    # Create time periods based on segmentation
    total_days = (end_date - start_date).days + 1
    
    def get_period_for_date(date_val):
        """
        Return the time period (str) the given date falls in, based on segmentation.
        If segmentation is None, returns "All Period".
        """
        if isinstance(date_val, str):
            date_obj = datetime.fromisoformat(date_val).date()
        else:
            date_obj = date_val
        
        days_from_start = (date_obj - start_date).days
        
        # Calculate the period number based on segmentation
        period_num = min(days_from_start // segmentation, (total_days - 1) // segmentation)
        
        # Calculate the start and end dates for the period
        period_start = start_date + timedelta(days=period_num * segmentation)
        period_end = min(start_date + timedelta(days=(period_num + 1) * segmentation - 1), end_date)
        
        # Return the time period as a string
        return f"{period_start} to {period_end}"
    
    return df.with_columns(
        pl.col("DEP_DATE").map_elements(get_period_for_date, return_dtype=pl.Utf8).alias("time_period")
    )

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
            ),
            html.P(
                "Choisissez vos filtres pour explorer les codes de retard TEC.",
                className="lead",
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
                                                className="form-label",
                                            ),
                                            dcc.Dropdown(
                                                id="flotte-dd",
                                                options=[
                                                    {"label": f, "value": f}
                                                    for f in flottes
                                                ],
                                                multi=True,
                                                placeholder="Tous les types",
                                            ),
                                        ],
                                        md=6,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label(
                                                "Matricule",
                                                className="form-label",
                                            ),
                                            dcc.Dropdown(
                                                id="matricule-dd",
                                                options=[
                                                    {"label": m, "value": m}
                                                    for m in matricules
                                                ],
                                                multi=True,
                                                placeholder="Tous les matricules",
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
                                                className="form-label",
                                            ),
                                            dcc.Dropdown(
                                                id="code-dd",
                                                options=[
                                                    {"label": c, "value": c}
                                                    for c in codes_dr
                                                ],
                                                multi=True,
                                                placeholder="Tous les codes",
                                            ),
                                        ],
                                        md=12,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Segmentation filter
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label(
                                                "Segmentation",
                                                className="form-label",
                                            ),
                                            dcc.Dropdown(
                                                id="segmentation-dd",
                                                placeholder="Select segmentation (days)",
                                                disabled=True,
                                                clearable=False,
                                            ),
                                        ],
                                        md=12,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Date inputs
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label(
                                                "Date de début :",
                                                className="form-label",
                                            ),
                                            dbc.Input(
                                                id="dt-start-input",
                                                type="date",
                                                value=dt_min_iso,
                                                min=dt_min_iso,
                                                max=dt_max_iso,
                                                className="form-control",
                                            ),
                                        ],
                                        md=6,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label(
                                                "Date de fin :",
                                                className="form-label",
                                            ),
                                            dbc.Input(
                                                id="dt-end-input",
                                                type="date",
                                                value=dt_max_iso,
                                                min=dt_min_iso,
                                                max=dt_max_iso,
                                                className="form-control",
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
            ),
            # Stats section
            html.H3("Statistiques", className="h4"),
            dbc.Card(
                html.Div(id="stats-div", className="p-3"),
                className="mb-4",
            ),
            # Data table
            html.H3(
                "📋 Détail des codes de retard",
                className="h4",
            ),
            html.Div(
                id="table-container", style={"maxHeight": "600px", "overflowY": "auto"}
            ),
        ],
        style={"paddingRight": "20px"},
    )

    right_panel = [
        html.H2(
            "Évolution temporelle des codes de retard",
            className="mb-3 h3",
        ),
        dbc.Card(
            dcc.Graph(id="codes-chart", style={"height": "70vh"}),
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
    State("segmentation-dd", "value"),
    State("dt-start-input", "value"),
    State("dt-end-input", "value"),
    prevent_initial_call=False,
)
def filter_data(n_clicks, fl_sel, mat_sel, code_sel, segmentation, dt_start, dt_end):
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

    # Date filtering
    if dt_start:
        df = df.filter(pl.col("DEP_DATE") >= datetime.fromisoformat(dt_start).date())
    if dt_end:
        df = df.filter(pl.col("DEP_DATE") <= datetime.fromisoformat(dt_end).date())

    # Also create data for table (without code filtering)
    df_for_table = df_filtered
    
    # Apply only basic filters for table
    if fl_sel:
        df_for_table = df_for_table.filter(pl.col("AC_SUBTYPE").is_in(fl_sel))
    if mat_sel:
        df_for_table = df_for_table.filter(pl.col("AC_REGISTRATION").is_in(mat_sel))
    
    # Date filtering for table
    if dt_start:
        df_for_table = df_for_table.filter(pl.col("DEP_DATE") >= datetime.fromisoformat(dt_start).date())
    if dt_end:
        df_for_table = df_for_table.filter(pl.col("DEP_DATE") <= datetime.fromisoformat(dt_end).date())

    # Convert to dict for JSON serialization
    return {
        "payload": df.to_dicts(),
        "table_payload": df_for_table.to_dicts(),
        "count": df.height,
        "segmentation": segmentation,
        "code_sel": code_sel,
        "dt_start": dt_start,
        "dt_end": dt_end,
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
    unique_codes = summary.height if not summary.is_empty() else 0
    total_delays = summary["Occurrences"].sum() if not summary.is_empty() else 0

    stats = dbc.Row(
        [
            dbc.Col(
                [
                    html.H5("Codes uniques", className="text-muted"),
                    html.H3(f"{unique_codes}", className="text-success mb-0"),
                ],
                md=6,
            ),
            dbc.Col(
                [
                    html.H5("Total retards", className="text-muted"),
                    html.H3(f"{total_delays}", className="text-warning mb-0"),
                ],
                md=6,
            ),
        ]
    )
    # 2. Build temporal bar chart
    segmentation = store_data.get("segmentation") if store_data else None
    dt_start = store_data.get("dt_start", dt_min_iso) if store_data else dt_min_iso
    dt_end = store_data.get("dt_end", dt_max_iso) if store_data else dt_max_iso
    
    if df.is_empty():
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
        # ALWAYS create time segments from full dataset to ensure consistent periods
        df_with_periods_full = create_time_segments(df, dt_start, dt_end, segmentation)
        
        # Get ALL possible time periods for consistent x-axis
        if df_with_periods_full.is_empty():
            all_periods = []
        else:
            all_periods = df_with_periods_full["time_period"].unique().sort().to_list()
        
        # Get selected codes from store_data
        code_sel = store_data.get("code_sel") if store_data else None
        
        # Filter by selected codes AFTER time segmentation
        if code_sel:
            df_chart = df_with_periods_full.filter(pl.col("CODE_DR").is_in(code_sel))
            selected_codes = code_sel
        else:
            df_chart = df_with_periods_full
            selected_codes = df_chart["CODE_DR"].unique().sort().to_list() if not df_chart.is_empty() else []
        
        if df_chart.is_empty() or not selected_codes:
            fig = go.Figure()
            fig.add_annotation(
                text="Aucune donnée pour les codes sélectionnés",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="#a0a7b9"),
            )
        else:
            # Group by time period and code
            temporal_data = (
                df_chart
                .group_by(["time_period", "CODE_DR"])
                .agg(pl.len().alias("count"))
                .sort(["time_period", "CODE_DR"])
            )
            
            # Create color palette for ALL unique codes (consistent colors)
            all_unique_codes = df["CODE_DR"].unique().sort().to_list() if not df.is_empty() else []
            colors = px.colors.qualitative.Set3
            color_map = {code: colors[i % len(colors)] for i, code in enumerate(all_unique_codes)}
            
            fig = go.Figure()
            
            # Add bars for each SELECTED code
            for code in selected_codes:
                code_data = temporal_data.filter(pl.col("CODE_DR") == code)
                
                # Ensure all periods are represented (fill missing with 0)
                periods_with_data = code_data["time_period"].to_list()
                counts_with_data = code_data["count"].to_list()
                
                # Create full data for all periods
                full_periods = []
                full_counts = []
                for period in all_periods:
                    if period in periods_with_data:
                        idx = periods_with_data.index(period)
                        full_counts.append(counts_with_data[idx])
                    else:
                        full_counts.append(0)
                    full_periods.append(period)
                
                fig.add_trace(go.Bar(
                    x=full_periods,
                    y=full_counts,
                    name=code,
                    marker_color=color_map.get(code, "#cccccc"),
                    hovertemplate=f"<b>{code}</b><br>" +
                                "Période: %{x}<br>" +
                                "Nombre de retards: %{y}<br>" +
                                "<extra></extra>",
                ))
    fig.update_layout(
        template="plotly_white",
        height=600,
        margin=dict(l=50, r=20, t=40, b=40),
        xaxis_title="Période",
        yaxis_title="Nombre total de retards",
        title="Évolution des codes de retard par période",
        barmode="group",
        font=dict(size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
    )

    # 3. Build table (independent of code and segmentation selection)
    if not store_data or not store_data.get("table_payload"):
        table_df = df_filtered
    else:
        table_df = pl.DataFrame(store_data["table_payload"])
        
        # If data exists, ensure date column is properly typed
        if not table_df.is_empty() and "DEP_DATE" in table_df.columns:
            # Convert DEP_DATE back to date type if it's a string
            if table_df.get_column("DEP_DATE").dtype == pl.Utf8:
                table_df = table_df.with_columns(
                    pl.col("DEP_DATE").str.strptime(pl.Date, "%Y-%m-%d", strict=False)
                )
    
    summary_table = analyze_delay_codes_for_table(table_df)
    
    if summary_table.is_empty():
        table = dbc.Alert(
            "Aucun code de retard trouvé dans la sélection",
            color="warning",
            className="text-center",
        )
    else:
        # Rename columns for display
        summary_table = summary_table.rename({"CODE_DR": "Code", "Nb_AP": "Nb Aéroports"})

        table = dash_table.DataTable(
            id="codes-table",
            data=summary_table.to_dicts(),
            columns=[{"name": col, "id": col} for col in summary_table.columns],
            style_header={
                "backgroundColor": "#f8f9fa",
                "color": "#495057",
                "fontWeight": "bold",
                "border": "1px solid #dee2e6",
                "fontSize": "12px",
            },
            style_cell={
                "backgroundColor": "white",
                "color": "#495057",
                "border": "1px solid #dee2e6",
                "textAlign": "left",
                "padding": "8px",
                "fontSize": "11px",
                "whiteSpace": "normal",
                "height": "auto",
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"},
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
            style_table={"height": "500px", "overflowY": "auto"},
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


# ---------- 3. Callback ----------
@app.callback(
    Output("segmentation-dd", "options"),
    Output("segmentation-dd", "disabled"),
    Output("segmentation-dd", "value"),     # reset value if dates change
    Input("dt-start-input", "value"),
    Input("dt-end-input", "value"),
    prevent_initial_call=True,
)
def update_segmentation(start_date, end_date):
    divisors = compute_divisors(start_date, end_date)
    options = [{"label": f"{d} day{'s' if d > 1 else ''}", "value": d} for d in divisors]
    disabled = not options
    return options, disabled, None        # clear selection whenever list rebuilds


# ------------------------------------------------------------------ #

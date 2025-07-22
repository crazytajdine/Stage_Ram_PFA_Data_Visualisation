"""
temporal_analysis_app.py  –  Dash + Polars  •  Temporal Analysis of Delay Codes
"""

import polars as pl
from pathlib import Path
from datetime import datetime, timedelta
import dash
from dash import Dash, html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from server_instance import get_app
import excel_manager

app = get_app()

# ------------------------------------------------------------------ #
# 1 ▸  Read & prepare data                                           #
# ------------------------------------------------------------------ #

try:
    # Lazy read once
    df_lazy = excel_manager.df

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

# Date input bounds (date only, not datetime)
if not df_filtered.is_empty():
    dt_min, dt_max = (
        df_filtered.get_column("DEP_DATE").min(),
        df_filtered.get_column("DEP_DATE").max(),
    )

else:
    dt_min = dt_max = datetime.now().date()

dt_min = dt_min or datetime.now().date()
dt_max = dt_max or datetime.now().date()
dt_min_date, dt_max_date = (
    dt_min.strftime("%Y-%m-%d"),
    dt_max.strftime("%Y-%m-%d"),
)

# ------------------------------------------------------------------ #
# 2 ▸  Helper functions for temporal analysis                       #
# ------------------------------------------------------------------ #


def get_time_period_column(df: pl.DataFrame, segmentation: str) -> pl.DataFrame:
    """Add time period column based on segmentation"""
    if segmentation == "days":
        return df.with_columns(pl.col("DEP_DATE").alias("period"))
    elif segmentation == "weeks":
        return df.with_columns(pl.col("DEP_DATE").dt.strftime("%Y-W%U").alias("period"))
    elif segmentation == "months":
        return df.with_columns(pl.col("DEP_DATE").dt.strftime("%Y-%m").alias("period"))
    else:
        return df


def analyze_temporal_codes(frame: pl.DataFrame, segmentation: str) -> pl.DataFrame:
    """Analyze delay codes by time period"""
    if frame.is_empty():
        return pl.DataFrame()

    # Add time period column
    df_with_period = get_time_period_column(frame, segmentation)

    # Group by period and code
    temporal_analysis = (
        df_with_period.group_by(["period", "CODE_DR"])
        .agg(
            [
                pl.len().alias("occurrences"),
                pl.col("LIB_CODE_DR").first().alias("description"),
            ]
        )
        .sort(["period", "occurrences"], descending=[False, True])
    )

    return temporal_analysis


def get_total_delays_by_period(frame: pl.DataFrame, segmentation: str) -> pl.DataFrame:
    """Get total delays by time period"""
    if frame.is_empty():
        return pl.DataFrame()

    # Add time period column
    df_with_period = get_time_period_column(frame, segmentation)

    # Group by period only
    total_by_period = (
        df_with_period.group_by("period")
        .agg(
            [
                pl.len().alias("total_delays"),
                pl.col("CODE_DR").n_unique().alias("unique_codes"),
            ]
        )
        .sort("period")
    )

    return total_by_period


def get_codes_time_series(frame: pl.DataFrame, segmentation: str) -> pl.DataFrame:
    """Get time series for each delay code"""
    if frame.is_empty():
        return pl.DataFrame()

    # Add time period column
    df_with_period = get_time_period_column(frame, segmentation)

    # Group by period and code
    time_series = (
        df_with_period.group_by(["period", "CODE_DR"])
        .agg(
            [
                pl.len().alias("occurrences"),
                pl.col("LIB_CODE_DR").first().alias("description"),
            ]
        )
        .sort(["period", "CODE_DR"])
    )

    return time_series


# ------------------------------------------------------------------ #
# 3 ▸  Layout                                                       #
# ------------------------------------------------------------------ #


def make_layout(total_vols: int) -> html.Div:
    return dbc.Container(
        fluid=True,
        className="px-4",
        children=[
            dcc.Store(id="temporal-filtered-store"),
            # Header
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1(
                                "ANALYSE TEMPORELLE DES CODES DE RETARD",
                                className="mb-2",
                            ),
                            html.P(
                                "Analysez l'évolution des codes de retard dans le temps.",
                                className="lead mb-4",
                            ),
                        ]
                    ),
                    dbc.Col(
                        html.P(
                            f"Base de données : {total_vols:,} vols TEC chargés",
                            className="text-end text-muted small mt-2",
                        ),
                        width="auto",
                    ),
                ]
            ),
            # Filters
            dbc.Card(
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label(
                                            "Date de début :", className="form-label"
                                        ),
                                        dbc.Input(
                                            id="temporal-dt-start",
                                            type="date",
                                            value=dt_min_date,
                                            min=dt_min_date,
                                            max=dt_max_date,
                                        ),
                                    ],
                                    md=4,
                                ),
                                dbc.Col(
                                    [
                                        html.Label(
                                            "Date de fin :", className="form-label"
                                        ),
                                        dbc.Input(
                                            id="temporal-dt-end",
                                            type="date",
                                            value=dt_max_date,
                                            min=dt_min_date,
                                            max=dt_max_date,
                                        ),
                                    ],
                                    md=4,
                                ),
                                dbc.Col(
                                    [
                                        html.Label(
                                            "Segmentation :", className="form-label"
                                        ),
                                        dcc.Dropdown(
                                            id="temporal-segmentation",
                                            options=[
                                                {"label": "Jours", "value": "days"},
                                                {"label": "Semaines", "value": "weeks"},
                                                {"label": "Mois", "value": "months"},
                                            ],
                                            value="days",
                                            clearable=False,
                                        ),
                                    ],
                                    md=4,
                                ),
                            ],
                            className="mb-3",
                        ),
                        dbc.Row(
                            dbc.Col(
                                dbc.Button(
                                    "🔍 Analyser",
                                    id="temporal-analyze-btn",
                                    color="primary",
                                    size="lg",
                                    className="w-100",
                                    n_clicks=0,
                                ),
                                md=12,
                            )
                        ),
                    ]
                ),
                className="mb-4",
            ),
            # Results
            dbc.Row(
                [
                    # Left column - Table
                    dbc.Col(
                        [
                            html.H3("📋 Tableau des occurrences", className="h4 mb-3"),
                            html.Div(
                                id="temporal-table-container",
                                style={"maxHeight": "600px", "overflowY": "auto"},
                            ),
                        ],
                        md=6,
                    ),
                    # Right column - Charts
                    dbc.Col(
                        [
                            html.H3(
                                "📊 Distribution totale des retards",
                                className="h4 mb-3",
                            ),
                            dbc.Card(
                                dcc.Graph(
                                    id="temporal-column-chart",
                                    style={"height": "400px"},
                                ),
                                className="mb-4",
                            ),
                            html.H3(
                                "📈 Évolution des codes de retard", className="h4 mb-3"
                            ),
                            dbc.Card(
                                dcc.Graph(
                                    id="temporal-line-chart", style={"height": "400px"}
                                ),
                            ),
                        ],
                        md=6,
                    ),
                ],
                className="mb-4",
            ),
            # Footer
            dbc.Row(
                dbc.Col(
                    [
                        html.Hr(),
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
# 4 ▸  Callbacks                                                    #
# ------------------------------------------------------------------ #

layout = make_layout(total_vols=df_filtered.height)


@app.callback(
    Output("temporal-filtered-store", "data"),
    Input("temporal-analyze-btn", "n_clicks"),
    State("temporal-dt-start", "value"),
    State("temporal-dt-end", "value"),
    State("temporal-segmentation", "value"),
    prevent_initial_call=False,
)
def filter_temporal_data(n_clicks, dt_start, dt_end, segmentation):
    """Filter data for temporal analysis"""
    if df_filtered.is_empty():
        return {"payload": [], "segmentation": segmentation}

    df = df_filtered

    # Apply date filters
    if dt_start:
        start_date = datetime.strptime(dt_start, "%Y-%m-%d").date()
        df = df.filter(pl.col("DEP_DATE") >= start_date)
    if dt_end:
        end_date = datetime.strptime(dt_end, "%Y-%m-%d").date()
        df = df.filter(pl.col("DEP_DATE") <= end_date)

    return {
        "payload": df.to_dicts(),
        "segmentation": segmentation,
        "timestamp": datetime.now().isoformat(),
    }


@app.callback(
    [
        Output("temporal-table-container", "children"),
        Output("temporal-column-chart", "figure"),
        Output("temporal-line-chart", "figure"),
    ],
    Input("temporal-filtered-store", "data"),
    prevent_initial_call=False,
)
def update_temporal_outputs(store_data):
    """Update all temporal analysis outputs"""

    if not store_data or not store_data.get("payload"):
        # Empty state
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="Aucune donnée disponible",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="#a0a7b9"),
        )
        empty_fig.update_layout(template="plotly_white")

        empty_table = dbc.Alert(
            "Aucune donnée à afficher",
            color="info",
            className="text-center",
        )

        return empty_table, empty_fig, empty_fig

    df = pl.DataFrame(store_data["payload"])

    # Ensure DEP_DATE is properly converted to date if it's a string
    if df.height > 0:
        # Check if DEP_DATE is string and convert it
        if df.get_column("DEP_DATE").dtype == pl.Utf8:
            df = df.with_columns(
                pl.col("DEP_DATE").str.strptime(pl.Date, "%Y-%m-%d", strict=False)
            )

    segmentation = store_data.get("segmentation", "days")

    # 1. Create temporal analysis table
    temporal_data = analyze_temporal_codes(df, segmentation)

    if temporal_data.is_empty():
        table = dbc.Alert(
            "Aucun code de retard trouvé",
            color="warning",
            className="text-center",
        )
    else:
        table = dash_table.DataTable(
            data=temporal_data.to_dicts(),
            columns=[
                {"name": "Période", "id": "period"},
                {"name": "Code", "id": "CODE_DR"},
                {"name": "Description", "id": "description"},
                {"name": "Occurrences", "id": "occurrences"},
            ],
            style_header={
                "backgroundColor": "#f8f9fa",
                "color": "#495057",
                "fontWeight": "bold",
                "border": "1px solid #dee2e6",
            },
            style_cell={
                "backgroundColor": "white",
                "color": "#495057",
                "border": "1px solid #dee2e6",
                "textAlign": "left",
                "padding": "8px",
                "fontSize": "11px",
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"}
            ],
            sort_action="native",
            filter_action="native",
            page_size=15,
            style_table={"height": "550px", "overflowY": "auto"},
        )

    # 2. Create column chart for total delays
    total_delays = get_total_delays_by_period(df, segmentation)

    if total_delays.is_empty():
        column_fig = go.Figure()
        column_fig.add_annotation(
            text="Aucune donnée disponible",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="#a0a7b9"),
        )
    else:
        column_fig = go.Figure(
            go.Bar(
                x=total_delays["period"].to_list(),
                y=total_delays["total_delays"].to_list(),
                marker_color="#10c5ff",
                name="Total retards",
            )
        )

    column_fig.update_layout(
        template="plotly_white",
        title="Distribution du total de retards par période",
        xaxis_title="Période",
        yaxis_title="Nombre total de retards",
        height=380,
        margin=dict(l=50, r=20, t=50, b=40),
    )

    # 3. Create line chart for individual codes
    time_series = get_codes_time_series(df, segmentation)

    if time_series.is_empty():
        line_fig = go.Figure()
        line_fig.add_annotation(
            text="Aucune donnée disponible",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="#a0a7b9"),
        )
    else:
        # Get top 10 codes by total occurrences
        top_codes = (
            time_series.group_by("CODE_DR")
            .agg(pl.col("occurrences").sum().alias("total"))
            .sort("total", descending=True)
            .head(10)["CODE_DR"]
            .to_list()
        )

        line_fig = go.Figure()

        colors = px.colors.qualitative.Set3
        for i, code in enumerate(top_codes):
            code_data = time_series.filter(pl.col("CODE_DR") == code)

            line_fig.add_trace(
                go.Scatter(
                    x=code_data["period"].to_list(),
                    y=code_data["occurrences"].to_list(),
                    mode="lines+markers",
                    name=code,
                    line=dict(color=colors[i % len(colors)]),
                    hovertemplate=f"<b>{code}</b><br>"
                    + "Période: %{x}<br>"
                    + "Occurrences: %{y}<br>"
                    + "<extra></extra>",
                )
            )

    line_fig.update_layout(
        template="plotly_white",
        title="Évolution des codes de retard dans le temps (Top 10)",
        xaxis_title="Période",
        yaxis_title="Nombre d'occurrences",
        height=380,
        margin=dict(l=50, r=20, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return table, column_fig, line_fig

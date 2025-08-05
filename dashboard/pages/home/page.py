from typing import Literal
from dash import (
    html,
    dcc,
    Output,
    dash_table,
)
import polars as pl
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from utils_dashboard.utils_download import add_export_callbacks
from server_instance import get_app
from excel_manager import (
    get_df,
    add_watcher_for_data,
    COL_NAME_WINDOW_TIME_MAX,
    COL_NAME_WINDOW_TIME,
)

from utils_dashboard.utils_graph import create_bar_figure, create_bar_horizontal_figure

COL_NAME_COUNT_FLIGHTS = "count of flights"
COL_NAME_SUBTYPE = "AC_SUBTYPE"
COL_NAME_PERCENTAGE_DELAY = "pct"
COL_NAME_CATEGORY_GT_15MIN = "delay_category_gt_15min"
COL_NAME_CATEGORY_GT_15MIN_COUNT = "delay_cat_count"
COL_NAME_CATEGORY_GT_15MIN_MEAN = "delay_cat_mean"


ID_SUMMERY_TABLE = "summary-table"
ID_FIGURE_CATEGORY_DELAY_GT_15MIN = "figure-category-delay-gt-15min"
ID_TABLE_FLIGHT_DELAY = "table-flight-delay"
ID_FIGURE_FLIGHT_DELAY = "figure-flight-delay"
ID_FIGURE_SUBTYPE_PR_DELAY_MEAN = "figure-subtype-pr-delay-mean"
ID_TABLE_SUBTYPE_PR_DELAY_MEAN = "table-subtype-pr-delay-mean"

app = get_app()


# Utilitaire conversion minutes -> h:mm


# --- DATA PROCESSING FOR SUBTYPE PCT ---
def process_subtype_pct_data(df: pl.LazyFrame) -> pl.LazyFrame:
    df_retard = df.filter(pl.col("DELAY_TIME") > 0)

    counts = (
        df_retard.group_by("AC_SUBTYPE")
        .agg(pl.count().alias(COL_NAME_COUNT_FLIGHTS))
        .sort(COL_NAME_COUNT_FLIGHTS, descending=True)
    )

    def add_percentage(batch: pl.DataFrame) -> pl.DataFrame:
        total = batch[COL_NAME_COUNT_FLIGHTS].sum()
        if total == 0:
            batch = batch.with_columns(pl.lit(0).alias(COL_NAME_PERCENTAGE_DELAY))
        else:
            batch = batch.with_columns(
                (pl.col(COL_NAME_COUNT_FLIGHTS) * 100 / total).alias(
                    COL_NAME_PERCENTAGE_DELAY
                )
            )
        return batch

    return counts.map_batches(
        add_percentage,
        schema={
            "AC_SUBTYPE": pl.String,
            COL_NAME_COUNT_FLIGHTS: pl.UInt32,
            COL_NAME_PERCENTAGE_DELAY: pl.Float64,
        },
    )


# ------ second


def calculate_period_distribution(df: pl.DataFrame) -> pl.DataFrame:
    counts_df = (
        df.group_by([COL_NAME_WINDOW_TIME, COL_NAME_WINDOW_TIME_MAX])
        .agg(pl.len().alias("count"))
        .sort(COL_NAME_WINDOW_TIME)
    )
    total = counts_df["count"].sum()
    if total == 0:
        return pl.DataFrame(
            {
                COL_NAME_WINDOW_TIME: [],
                "count": [],
                COL_NAME_PERCENTAGE_DELAY: [],
            }
        )
    return counts_df.with_columns(
        (pl.col("count") * 100 / total).alias(COL_NAME_PERCENTAGE_DELAY)
    )


def calculate_delay_pct(df: pl.LazyFrame) -> pl.LazyFrame:
    # 1) bucket rows into two categories
    res = df.with_columns(
        pl.when(pl.col("DELAY_TIME") >= 15)
        .then(pl.lit("flights with delay ≥ 15 min"))
        .otherwise(pl.lit("flights with delay < 15 min"))
        .alias(COL_NAME_CATEGORY_GT_15MIN)
    )
    # 2) count per category

    res = res.group_by(COL_NAME_CATEGORY_GT_15MIN).agg(
        pl.count().alias(COL_NAME_CATEGORY_GT_15MIN_COUNT)
    )

    res = res.with_columns(
        (
            pl.col(COL_NAME_CATEGORY_GT_15MIN_COUNT)
            / pl.col(COL_NAME_CATEGORY_GT_15MIN_COUNT).sum()
        ).alias(COL_NAME_CATEGORY_GT_15MIN_MEAN)
    )

    # 3) compute total via a cross join, then pct
    return res


def build_interval_table_data(df: pl.DataFrame) -> tuple[list[dict], list[dict]]:

    counts_df = (
        df.group_by([COL_NAME_WINDOW_TIME, COL_NAME_WINDOW_TIME_MAX])
        .agg(pl.count().alias("nbr_de_vol"))
        .sort(COL_NAME_WINDOW_TIME, descending=False)
    )
    total = counts_df["nbr_de_vol"].sum()
    if total == 0:
        return [], []
    counts_df = counts_df.with_columns(
        (pl.col("nbr_de_vol") * 100 / total).round(2).alias("pourcentage")
    )
    columns = [
        {"name": "Min_Date", "id": COL_NAME_WINDOW_TIME, "type": "datetime"},
        {"name": "Max_Date", "id": COL_NAME_WINDOW_TIME_MAX, "type": "datetime"},
        {"name": "Nbr_de_vol", "id": "nbr_de_vol", "type": "numeric"},
        {
            "name": "Pourcentage",
            "id": "pourcentage",
            "type": "numeric",
            "format": {"specifier": ".2f"},
        },
    ]
    data = counts_df.to_dicts()
    return columns, data


# ------ third


# ----------


# --- LAYOUT COMPLET ---

layout = dbc.Container(
    [
        html.Div(
            [
                dbc.Alert(
                    id="result-message",
                    is_open=False,
                    dismissable=True,
                    className="mt-3",
                ),
                # Premier bouton + tableau + export
                dbc.Button("Exporter Excel", id="result-export-btn", className="mt-2"),
                dash_table.DataTable(
                    id=ID_SUMMERY_TABLE,
                    columns=[],
                    data=[],
                    page_size=10,
                    style_table={
                        "overflowX": "auto",
                        "marginTop": "10px",
                        "marginBottom": "40px",
                    },
                    style_cell={"textAlign": "left"},
                    sort_action="native",
                ),
                # Graphique subtype pct
                html.Div(
                    dcc.Graph(
                        id=ID_FIGURE_SUBTYPE_PR_DELAY_MEAN,
                        style={"margin": "auto", "height": "400px", "width": "90%"},
                    ),
                    style={
                        "display": "flex",
                        "justifyContent": "center",
                        "alignItems": "center",
                        "marginBottom": "40px",
                    },
                ),
                # Deuxième bouton + tableau + export
                html.Div(
                    [
                        dbc.Button(
                            "Exporter Excel",
                            id="subtype-export-btn",
                            className="mb-2",
                        ),
                        dash_table.DataTable(
                            id=ID_TABLE_SUBTYPE_PR_DELAY_MEAN,
                            columns=[],
                            data=[],
                            page_size=10,
                            style_table={
                                "overflowX": "auto",
                                "marginTop": "10px",
                                "marginBottom": "40px",
                            },
                            style_cell={"textAlign": "left"},
                            sort_action="native",
                        ),
                    ]
                ),
                # Graphique retard %
                html.Div(
                    dcc.Graph(
                        id=ID_FIGURE_CATEGORY_DELAY_GT_15MIN,
                        style={"margin": "auto", "height": "400px", "width": "90%"},
                    ),
                    style={
                        "display": "flex",
                        "justifyContent": "center",
                        "alignItems": "center",
                        "marginBottom": "40px",
                    },
                ),
                # Graphique intervalles
                html.Div(
                    dcc.Graph(
                        id=ID_FIGURE_FLIGHT_DELAY,
                        style={"margin": "auto", "width": "100%"},
                    ),
                    style={
                        "marginBottom": "15px",
                        "background": "white",
                        "padding": "10px",
                        "borderRadius": "8px",
                    },
                ),
                # Troisième bouton + tableau + export
                html.Div(
                    [
                        dbc.Button(
                            "Exporter Excel",
                            id="interval-export-btn",
                            className="mb-2",
                        ),
                        dash_table.DataTable(
                            id=ID_TABLE_FLIGHT_DELAY,
                            columns=[],
                            data=[],
                            page_size=10,
                            style_table={
                                "overflowX": "auto",
                                "marginTop": "10px",
                                "marginBottom": "40px",
                            },
                            style_cell={"textAlign": "left"},
                            sort_action="native",
                        ),
                    ],
                    style={"marginBottom": "40px"},
                ),
            ],
            className="mx-3",
        ),
    ],
    fluid=True,
)

# --- CALLBACKS ---


@app.callback(
    Output("result-message", "children"),
    Output("result-message", "color"),
    Output("result-message", "is_open"),
    Output(ID_SUMMERY_TABLE, "columns"),
    Output(ID_SUMMERY_TABLE, "data"),
    Output(ID_FIGURE_SUBTYPE_PR_DELAY_MEAN, "figure"),
    Output(ID_TABLE_SUBTYPE_PR_DELAY_MEAN, "columns"),
    Output(ID_TABLE_SUBTYPE_PR_DELAY_MEAN, "data"),
    Output(ID_FIGURE_CATEGORY_DELAY_GT_15MIN, "figure"),
    Output(ID_TABLE_FLIGHT_DELAY, "columns"),
    Output(ID_TABLE_FLIGHT_DELAY, "data"),
    Output(ID_FIGURE_FLIGHT_DELAY, "figure"),
    add_watcher_for_data(),
)
def update_all_outputs(_):
    # Get lazy dataframe
    df_lazy = get_df()

    # If no file loaded, return empty outputs with alert
    if df_lazy is None:
        alert = dbc.Alert(
            "No Excel file loaded. Please upload an Excel file first.",
            color="danger",
            className="mt-3",
        )
        empty_fig = go.Figure()
        return (
            alert,
            "danger",
            True,
            [],  # summary table columns
            [],  # summary table data
            empty_fig,  # subtype delay mean figure
            [],  # subtype delay mean columns
            [],  # subtype delay mean data
            empty_fig,  # category delay figure
            [],  # flight delay table columns
            [],  # flight delay table data
            empty_fig,  # interval delay figure
        )

    # Collect eager dataframe for processing
    df = df_lazy.collect()

    # If dataframe is empty, return warning alert and empty outputs
    if df.is_empty():
        return (
            dbc.Alert("No results found.", color="warning", className="mt-3"),
            "warning",
            True,
            [],
            [],
            go.Figure(),
            [],
            [],
            go.Figure(),
            [],
            [],
            go.Figure(),
        )

    # --- Info summary ---
    result_msg = dbc.Alert(
        f"{df.height} result(s) found.", color="success", className="mt-3"
    )

    # --- Summary table ---
    df_summary = df.select(
        [
            "AC_SUBTYPE",
            "AC_REGISTRATION",
            "DEP_DAY_SCHED",
            "DELAY_TIME",
            "DELAY_CODE",
        ]
    )
    columns_summary = [{"name": col, "id": col} for col in df_summary.columns]
    data_summary = df_summary.to_dicts()

    # --- Subtype delay percentage graph and table ---
    subtype_data = process_subtype_pct_data(df_lazy).collect()
    chart_subtype = create_bar_horizontal_figure(
        subtype_data,
        x=COL_NAME_PERCENTAGE_DELAY,
        y=COL_NAME_SUBTYPE,
        title="Delayed flights by SUBTYPE (%)",
    )

    subtype_columns = [{"name": name, "id": name} for name in subtype_data.columns]
    subtype_rows = subtype_data.to_dicts()

    # --- Delay per category bar chart ---
    df_pct = calculate_delay_pct(df_lazy).collect()
    chart_pct = create_bar_figure(
        df_pct,
        x=COL_NAME_CATEGORY_GT_15MIN,
        y=COL_NAME_CATEGORY_GT_15MIN_MEAN,
        title="Delay per category",
    )
    # --- Interval delay distribution table and chart ---
    df_period = calculate_period_distribution(df)
    period_columns = [{"name": c, "id": c} for c in df_period.columns]
    period_data = df_period.to_dicts()
    chart_interval = create_bar_horizontal_figure(
        df_period,
        x="count",
        y=COL_NAME_WINDOW_TIME,
        title="Distribution of flights by intervals",
    )

    # Return all outputs in order requested
    return (
        result_msg,
        "success",
        True,
        columns_summary,
        data_summary,
        chart_subtype,
        subtype_columns,
        subtype_rows,
        chart_pct,
        period_columns,
        period_data,
        chart_interval,
    )


# --- CALLBACKS POUR TELECHARGEMENT EXCEL ---
for tbl, btn, name in [
    (ID_SUMMERY_TABLE, "result-export-btn", "vols_filtres"),
    (ID_TABLE_SUBTYPE_PR_DELAY_MEAN, "subtype-export-btn", "vols_subtype_filtres"),
    (ID_TABLE_FLIGHT_DELAY, "interval-export-btn", "vols_intervalles"),
]:
    add_export_callbacks(id_table=tbl, id_button=btn, name=name)

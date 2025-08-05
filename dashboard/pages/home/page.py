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
ID_TABLE_CATEGORY_DELAY_GT_15MIN = "table-category-delay-gt-15min"
ID_TABLE_FLIGHT_DELAY = "table-flight-delay"
ID_FIGURE_FLIGHT_DELAY = "figure-flight-delay"
ID_FIGURE_SUBTYPE_PR_DELAY_MEAN = "figure-subtype-pr-delay-mean"
ID_TABLE_SUBTYPE_PR_DELAY_MEAN = "table-subtype-pr-delay-mean"


TABLE_NAMES_RENAME = {
    "AC_SUBTYPE": "Aircraft Subtype",
    "AC_REGISTRATION": "Registration",
    "DEP_DAY_SCHED": "Scheduled Departure Day",
    "DELAY_TIME": "Delay Time (min)",
    "DELAY_CODE": "Delay Code",
    "count": "Flight Count",
    COL_NAME_WINDOW_TIME: "Interval Start",
    COL_NAME_WINDOW_TIME_MAX: "Interval End",
    COL_NAME_PERCENTAGE_DELAY: "Percentage of Delayed Flights",
    COL_NAME_COUNT_FLIGHTS: "Count of Delayed Flights",
    COL_NAME_CATEGORY_GT_15MIN: "Delay Category",
    COL_NAME_CATEGORY_GT_15MIN_MEAN: "Category %",
    COL_NAME_CATEGORY_GT_15MIN_COUNT: "Category Count",
}


app = get_app()


def process_subtype_pct_data(df: pl.LazyFrame) -> pl.LazyFrame:
    counts = df.group_by("AC_SUBTYPE").agg(pl.count().alias(COL_NAME_COUNT_FLIGHTS))

    result = counts.with_columns(
        [
            (pl.col(COL_NAME_COUNT_FLIGHTS) * 100 / pl.sum(COL_NAME_COUNT_FLIGHTS))
            .round(2)
            .alias(COL_NAME_PERCENTAGE_DELAY)
        ]
    )

    return result.sort(COL_NAME_PERCENTAGE_DELAY, descending=False)


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
        (pl.col("count") * 100 / total).round(2).alias(COL_NAME_PERCENTAGE_DELAY)
    )


def calculate_delay_pct(df: pl.LazyFrame) -> pl.LazyFrame:
    # 1) Categorize delays
    df = df.with_columns(
        pl.when(pl.col("DELAY_TIME") >= 15)
        .then(pl.lit("flights with delay ≥ 15 min"))
        .otherwise(pl.lit("flights with delay < 15 min"))
        .alias(COL_NAME_CATEGORY_GT_15MIN)
    )

    # 2) Group by time window and delay category
    res = df.group_by(
        [COL_NAME_WINDOW_TIME_MAX, COL_NAME_WINDOW_TIME, COL_NAME_CATEGORY_GT_15MIN]
    ).agg(pl.count().alias(COL_NAME_CATEGORY_GT_15MIN_COUNT))

    # 3) Compute percentage per time window
    res = res.with_columns(
        (
            pl.col(COL_NAME_CATEGORY_GT_15MIN_COUNT)
            * 100
            / pl.col(COL_NAME_CATEGORY_GT_15MIN_COUNT)
            .sum()
            .over([COL_NAME_WINDOW_TIME_MAX, COL_NAME_WINDOW_TIME])
        )
        .round(2)
        .alias(COL_NAME_CATEGORY_GT_15MIN_MEAN)
    )

    return res


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
                html.Div(
                    [
                        dbc.Button(
                            "Exporter Excel",
                            id="category-export-btn",
                            className="mb-2",
                        ),
                        dash_table.DataTable(
                            id=ID_TABLE_CATEGORY_DELAY_GT_15MIN,
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


# 1) Summary table callback
@app.callback(
    Output("result-message", "children"),
    Output("result-message", "color"),
    Output("result-message", "is_open"),
    Output(ID_SUMMERY_TABLE, "columns"),
    Output(ID_SUMMERY_TABLE, "data"),
    add_watcher_for_data(),
)
def update_summary(_):
    df_lazy = get_df()
    if df_lazy is None:
        alert = dbc.Alert(
            "No Excel file loaded. Please upload first.",
            color="danger",
            className="mt-3",
        )
        return alert, "danger", True, [], []
    df = df_lazy.collect()
    if df.is_empty():
        return (
            dbc.Alert("No results found.", color="warning", className="mt-3"),
            "warning",
            True,
            [],
            [],
        )
    # build summary table
    df_summary = df.select(
        [
            "AC_SUBTYPE",
            "AC_REGISTRATION",
            "DEP_DAY_SCHED",
            "DELAY_TIME",
            "DELAY_CODE",
        ]
    )
    cols = [{"name": TABLE_NAMES_RENAME.get(c, c), "id": c} for c in df_summary.columns]
    data = df_summary.to_dicts()
    alert = dbc.Alert(
        f"{df.height} result(s) found.", color="success", className="mt-3"
    )
    return alert, "success", True, cols, data


# 2) Subtype-delay % chart + table callback
@app.callback(
    Output(ID_FIGURE_SUBTYPE_PR_DELAY_MEAN, "figure"),
    Output(ID_TABLE_SUBTYPE_PR_DELAY_MEAN, "columns"),
    Output(ID_TABLE_SUBTYPE_PR_DELAY_MEAN, "data"),
    add_watcher_for_data(),
)
def update_subtype(_):
    df_lazy = get_df()
    if df_lazy is None:
        return go.Figure(), [], []
    df_sub = process_subtype_pct_data(df_lazy).collect()
    # figure
    fig = create_bar_horizontal_figure(
        df_sub,
        x=COL_NAME_PERCENTAGE_DELAY,
        y=COL_NAME_SUBTYPE,
        title="Delayed flights by SUBTYPE (%)",
    )
    # table
    cols = [{"name": TABLE_NAMES_RENAME.get(c, c), "id": c} for c in df_sub.columns]
    data = df_sub.to_dicts()
    return fig, cols, data


# 3) Delay-category chart + table callback
@app.callback(
    Output(ID_FIGURE_CATEGORY_DELAY_GT_15MIN, "figure"),
    Output(ID_TABLE_CATEGORY_DELAY_GT_15MIN, "columns"),
    Output(ID_TABLE_CATEGORY_DELAY_GT_15MIN, "data"),
    add_watcher_for_data(),
)
def update_category(_):
    df_lazy = get_df()
    if df_lazy is None:
        return go.Figure(), [], []
    df_cat = calculate_delay_pct(df_lazy).collect()
    # figure
    fig = create_bar_figure(
        df_cat,
        x=COL_NAME_WINDOW_TIME,
        y=COL_NAME_CATEGORY_GT_15MIN_MEAN,
        color=COL_NAME_CATEGORY_GT_15MIN,
        title="Delay per category",
    )
    # table
    display_cols = [
        COL_NAME_WINDOW_TIME,
        COL_NAME_WINDOW_TIME_MAX,
        COL_NAME_CATEGORY_GT_15MIN,
        COL_NAME_CATEGORY_GT_15MIN_MEAN,
    ]

    df_disp = df_cat.select(display_cols)
    cols = [{"name": TABLE_NAMES_RENAME.get(c, c), "id": c} for c in display_cols]
    data = df_disp.to_dicts()
    return fig, cols, data


# 4) Interval-distribution chart + table callback
@app.callback(
    Output(ID_FIGURE_FLIGHT_DELAY, "figure"),
    Output(ID_TABLE_FLIGHT_DELAY, "columns"),
    Output(ID_TABLE_FLIGHT_DELAY, "data"),
    add_watcher_for_data(),
)
def update_interval(_):
    df_lazy = get_df()
    if df_lazy is None:
        return go.Figure(), [], []
    df = df_lazy.collect()
    if df.is_empty():
        return go.Figure(), [], []
    df_period = calculate_period_distribution(df)
    # figure
    fig = create_bar_horizontal_figure(
        df_period,
        x=COL_NAME_PERCENTAGE_DELAY,
        y=COL_NAME_WINDOW_TIME,
        title="Distribution of flights by intervals",
    )
    # table
    cols = [{"name": TABLE_NAMES_RENAME.get(c, c), "id": c} for c in df_period.columns]
    data = df_period.to_dicts()
    return fig, cols, data


# --- CALLBACKS POUR TELECHARGEMENT EXCEL ---
for tbl, btn, name in [
    (ID_SUMMERY_TABLE, "result-export-btn", "vols_filtres"),
    (ID_TABLE_SUBTYPE_PR_DELAY_MEAN, "subtype-export-btn", "vols_subtype_filtres"),
    (ID_TABLE_FLIGHT_DELAY, "interval-export-btn", "vols_intervalles"),
]:
    add_export_callbacks(id_table=tbl, id_button=btn, name=name)

from typing import Optional
import dash
import dash_bootstrap_components as dbc
from dash import Output, dash_table
from utils_dashboard.utils_graph import (
    create_graph_bar_card,
    generate_card_info_change,
)
from server_instance import get_app

import polars as pl

from excel_manager import (
    COL_NAME_WINDOW_TIME_MAX,
    get_df,
    add_watcher_for_data,
    COL_NAME_TOTAL_COUNT,
    COL_NAME_WINDOW_TIME,
    get_total_df,
)

from utils_dashboard.utils_download import (
    add_export_callbacks,
)


COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY = "flight_with_delay"
COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_GTE_15MIN = "flight_with_delay_gte_15min"
COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_41_46_GTE_15MIN = (
    "flight_with_delay_gte_15min_code_41_46"
)


COL_NAME_PER_FLIGHTS_NOT_DELAYED = "per_flights_not_delayed"
COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN = "per_delayed_flights_not_with_15min"
COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46 = (
    "per_delayed_flights_15min__not_with_41_46"
)

COL_NAME_PER_FLIGHTS_NOT_DELAYED_SHOW = "per_flights_not_delayed_show_show"
COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN_SHOW = (
    "per_delayed_flights_not_with_15min_show"
)
COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46_SHOW = (
    "per_delayed_flights_15min__not_with_41_46_SHOW"
)

ID_GRAPH_DELAY = "graph_delay"
ID_GRAPH_DELAY_15MIN = "graph_delay_15min"
ID_GRAPH_DELAY_41_42_15MIN = "graph_delay_41_42_15min"

ID_CARD_DELAY = "card_delay"
ID_CARD_DELAY_15MIN = "card_delay_15min"
ID_CARD_DELAY_15MIN_41_42 = "card_delay_15min_41_42"

ID_TABLE_CONTAINER = "result_table_percentage"
ID_TABLE = "result_table"

app = get_app()

TABLE_COL_NAMES = [
    {"name": "Window Start", "id": COL_NAME_WINDOW_TIME},
    {"name": "Window End", "id": COL_NAME_WINDOW_TIME_MAX},
    {
        "name": "Percentage of On-Time Flights",
        "id": COL_NAME_PER_FLIGHTS_NOT_DELAYED_SHOW,
    },
    {
        "name": "Percentage of On-Time or Delays Less Than 15 Minutes",
        "id": COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN_SHOW,
    },
    {
        "name": "Percentage of On-Time or less than 15 Minutes, or Delays Not Due to Reasons 41/46",
        "id": COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46_SHOW,
    },
    {
        "name": "Total count of flights",
        "id": COL_NAME_TOTAL_COUNT,
    },
    {
        "name": "Total count of flights with delay",
        "id": COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY,
    },
    {
        "name": "Total count of flights with delay greater than 15 min",
        "id": COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_GTE_15MIN,
    },
    {
        "name": "Total count of flights with delay than 15 min with code delay 41 and 46",
        "id": COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_41_46_GTE_15MIN,
    },
]


def calculate_graph_info_with_period(df: pl.LazyFrame) -> pl.LazyFrame:

    assert df is not None
    ##

    delayed_flights_count_df = df.group_by(COL_NAME_WINDOW_TIME).agg(
        pl.len().alias(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY)
    )

    delayed_15min_df = df.filter((pl.col("Retard en min") >= 15))

    ##
    delayed_15min_count_df = delayed_15min_df.group_by(COL_NAME_WINDOW_TIME).agg(
        pl.len().alias(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_GTE_15MIN)
    )

    ##
    delayed_flights_41_46_gte_15min_count_df = (
        delayed_15min_df.filter(pl.col("CODE_DR").is_in({41, 46}))
        .group_by(COL_NAME_WINDOW_TIME)
        .agg(pl.len().alias(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_41_46_GTE_15MIN))
    )

    total_df = get_total_df()

    joined_df = (
        total_df.join(delayed_flights_count_df, COL_NAME_WINDOW_TIME, how="left")
        .join(delayed_15min_count_df, COL_NAME_WINDOW_TIME, how="left")
        .join(
            delayed_flights_41_46_gte_15min_count_df,
            COL_NAME_WINDOW_TIME,
            how="left",
        )
    )

    joined_df = joined_df.sort(COL_NAME_WINDOW_TIME)

    joined_df = joined_df.with_columns(
        [
            ## delay
            pl.lit(1)
            .sub(
                pl.col(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY)
                / (pl.col(COL_NAME_TOTAL_COUNT))
            )
            .mul(100)
            .alias(COL_NAME_PER_FLIGHTS_NOT_DELAYED),
            ## delay > 15
            pl.lit(1)
            .sub(
                pl.col(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_GTE_15MIN)
                / (pl.col(COL_NAME_TOTAL_COUNT))
            )
            .mul(100)
            .alias(COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN),
            ## delay > 15 min for 41 42
            pl.lit(1)
            .sub(
                (
                    pl.col(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_41_46_GTE_15MIN)
                    / pl.col(COL_NAME_TOTAL_COUNT)
                )
            )
            .mul(100)
            .alias(COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46),
        ]
    )

    columns_to_format = [
        (
            COL_NAME_PER_FLIGHTS_NOT_DELAYED,
            COL_NAME_PER_FLIGHTS_NOT_DELAYED_SHOW,
        ),
        (
            COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN,
            COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN_SHOW,
        ),
        (
            COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46,
            COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46_SHOW,
        ),
    ]

    joined_df = joined_df.with_columns(
        [
            (
                pl.col(col)
                .map_elements(lambda v: f"{v:.2f}%", return_dtype=pl.Utf8)
                .alias(show_col)
            )
            for col, show_col in columns_to_format
        ]
    )

    return joined_df


def calculate_result() -> Optional[pl.DataFrame]:
    df = get_df()

    if df is None:
        return None

    df = calculate_graph_info_with_period(df)

    return df.collect()


def get_two_latest_values(df: pl.DataFrame, x: str):

    unique_vals = (
        df.select(pl.col(x).drop_nulls().unique().sort(reverse=True))
        .to_series()
        .to_list()
    )

    if len(unique_vals) == 0:
        return None, None
    elif len(unique_vals) == 1:
        return unique_vals[0], None
    else:
        return unique_vals[0], unique_vals[1]


layout = dbc.Container(
    [
        # Metrics row
        dbc.Row(
            [
                dbc.Col(id=ID_CARD_DELAY, md=4),
                dbc.Col(id=ID_CARD_DELAY_15MIN, md=4),
                dbc.Col(id=ID_CARD_DELAY_15MIN_41_42, md=4),
            ],
            className="g-4 mb-5",
            justify="center",
        ),
        # Graphs row (unchanged)
        dbc.Row(
            [
                dbc.Col(
                    id=ID_GRAPH_DELAY,
                ),
                dbc.Col(
                    id=ID_GRAPH_DELAY_15MIN,
                ),
                dbc.Col(
                    id=ID_GRAPH_DELAY_41_42_15MIN,
                    lg=12,
                    xl=12,
                ),
            ],
            className="g-4 justify-content-center",
        ),
        dbc.Button("Export Excel", id="export-pre-metrics-btn", className="mt-2"),
        dbc.Row(
            id=ID_TABLE_CONTAINER,
        ),
    ],
    fluid=True,
    className="p-4",
)


add_export_callbacks(
    ID_TABLE,
    "export-pre-metrics-btn",
    "performance_metrics",
)


@app.callback(
    [
        Output(ID_CARD_DELAY, "children"),
        Output(ID_CARD_DELAY_15MIN, "children"),
        Output(ID_CARD_DELAY_15MIN_41_42, "children"),
        Output(ID_GRAPH_DELAY, "children"),
        Output(ID_GRAPH_DELAY_15MIN, "children"),
        Output(ID_GRAPH_DELAY_41_42_15MIN, "children"),
        Output(ID_TABLE_CONTAINER, "children"),
    ],
    add_watcher_for_data(),
)
def create_layout(
    _,
):

    df = get_df()
    if df is None:
        return dash.no_update

    result = calculate_result()

    if result is None:
        return dash.no_update

    card1 = generate_card_info_change(
        result,
        COL_NAME_PER_FLIGHTS_NOT_DELAYED,
        "Percentage of On-Time Flights",
    )  # example first card
    card2 = generate_card_info_change(
        result,
        COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN,
        "Percentage of On-Time or Delays Less Than 15 Minutes",
    )  # example second card
    card3 = generate_card_info_change(
        result,
        COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46,
        "Percentage of On-Time or less than 15 Minutes, or Delays Not Due to Reasons 41/46",
    )  # example second card

    fig1 = create_graph_bar_card(
        result,
        COL_NAME_WINDOW_TIME,
        COL_NAME_PER_FLIGHTS_NOT_DELAYED,
        "Percentage of On-Time Flights",
        COL_NAME_PER_FLIGHTS_NOT_DELAYED_SHOW,
    )
    fig2 = create_graph_bar_card(
        result,
        COL_NAME_WINDOW_TIME,
        COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN,
        "Percentage of On-Time or Delays Less Than 15 Minutes",
        COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN_SHOW,
    )
    fig3 = create_graph_bar_card(
        result,
        COL_NAME_WINDOW_TIME,
        COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46,
        "Percentage of On-Time or less than 15 Minutes, or Delays Not Due to Reasons 41/46",
        COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46_SHOW,
    )

    table_col_names = [
        {"id": col["id"], "name": col["name"]} for col in TABLE_COL_NAMES
    ]

    table_data = (
        result.drop_nulls(
            subset=[
                COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY,
                COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_GTE_15MIN,
                COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_41_46_GTE_15MIN,
            ]
        )
        .select([col["id"] for col in table_col_names])
        .to_dicts()
    )

    table = []

    if result.height != 0:
        table = dash_table.DataTable(
            data=table_data,
            columns=table_col_names,
            id=ID_TABLE,
            page_size=10,
            sort_action="native",
            style_table={
                "overflowX": "auto",
                "marginTop": "10px",
                "marginBottom": "40px",
            },
            style_cell={"textAlign": "left"},
            sort_by=[{"column_id": COL_NAME_WINDOW_TIME, "direction": "desc"}],
        )

    return card1, card2, card3, fig1, fig2, fig3, table

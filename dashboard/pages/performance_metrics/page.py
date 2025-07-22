from datetime import datetime
from typing import List, Optional
import dash_bootstrap_components as dbc
from dash import html, dcc
from server_instance import get_app

import polars as pl
from excel_manager import (
    get_df,
    get_count_df,
    COL_NAME_TOTAL_COUNT,
    COL_NAME_WINDOW_TIME,
    COL_NAME_DEPARTURE_DATETIME,
)


COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY = "flight_with_delay"
COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_GTE_15MIN = "flight_with_delay_gte_15min"
COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_41_42_GTE_15MIN = (
    "flight_with_delay_gte_15min_code_41_42"
)

COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_42 = (
    "per_delayed_flights_15min__not_with_41_42"
)
COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN = "per_delayed_flights_not_with_15min"
COL_NAME_PER_FLIGHTS_NOT_DELAYED = "per_flights_not_delayed"


app = get_app()


def create_layout(window_str):
    df = get_df()
    if df is None:
        return None
    result = calculate_result(window_str)

    if result is None:
        return None

    (
        date_window_res,
        per_flights_not_delayed,
        per_delayed_flights_not_with_15min,
        per_delayed_flights_15min_not_with_41_42,
    ) = result


def calculate_graph_info(df: pl.LazyFrame) -> pl.DataFrame:

    assert df is not None

    total_df = get_count_df()

    ##
    delayed_flights_count_df = df.select(
        pl.len().alias(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY)
    )

    delayed_15min_df = df.filter((pl.col("Retard en min") >= 15))

    ##
    delayed_15min_count_df = delayed_15min_df.select(
        pl.len().alias(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_GTE_15MIN)
    )

    ##
    delayed_flights_41_42_gte_15min_count_df = delayed_15min_df.filter(
        (pl.col("CODE_DR").is_in({41, 42}))
    ).select(pl.len().alias(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_41_42_GTE_15MIN))

    joined_df = (
        total_df.join(
            delayed_flights_count_df,
        )
        .join(
            delayed_15min_count_df,
        )
        .join(
            delayed_flights_41_42_gte_15min_count_df,
        )
    )

    return joined_df.collect()


def calculate_graph_info_with_period(df: pl.LazyFrame, window_str: str) -> pl.DataFrame:

    assert window_str and df is not None

    total_df = get_count_df(window_str)

    windowed_df = df.with_columns(
        pl.col(COL_NAME_DEPARTURE_DATETIME)
        .dt.truncate(window_str)
        .alias(COL_NAME_WINDOW_TIME)
    )

    ##
    delayed_flights_count_df = windowed_df.group_by(COL_NAME_WINDOW_TIME).agg(
        pl.len().alias(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY)
    )

    delayed_15min_df = windowed_df.filter((pl.col("Retard en min") >= 15))

    ##
    delayed_15min_count_df = delayed_15min_df.group_by(COL_NAME_WINDOW_TIME).agg(
        pl.len().alias(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_GTE_15MIN)
    )

    ##
    delayed_flights_41_42_gte_15min_count_df = (
        delayed_15min_df.filter(pl.col("CODE_DR").is_in({41, 42}))
        .group_by(COL_NAME_WINDOW_TIME)
        .agg(pl.len().alias(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_41_42_GTE_15MIN))
    )

    graph_info_df = (
        total_df.join(delayed_flights_count_df)
        .join(delayed_15min_count_df)
        .join(
            delayed_flights_41_42_gte_15min_count_df,
        )
        .collect()
    )

    joined_df = (
        total_df.join(delayed_flights_count_df, COL_NAME_WINDOW_TIME, how="left")
        .join(delayed_15min_count_df, COL_NAME_WINDOW_TIME, how="left")
        .join(
            delayed_flights_41_42_gte_15min_count_df, COL_NAME_WINDOW_TIME, how="left"
        )
    )

    joined_df = joined_df.with_columns(
        [
            ## delay
            pl.lit(1)
            .sub(
                pl.col(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY)
                / (pl.col(COL_NAME_TOTAL_COUNT))
            )
            .alias(COL_NAME_PER_FLIGHTS_NOT_DELAYED),
            ## delay > 15
            pl.lit(1)
            .sub(
                pl.col(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_GTE_15MIN)
                / (pl.col(COL_NAME_TOTAL_COUNT))
            )
            .alias(COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN),
            ## delay > 15 min for 41 42
            pl.lit(1)
            .sub(
                (
                    pl.col(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_41_42_GTE_15MIN)
                    / pl.col(COL_NAME_TOTAL_COUNT)
                )
            )
            .alias(COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_42),
        ]
    )

    return joined_df.collect()


def calculate_result(
    window_str: str = "",
) -> Optional[
    tuple[
        Optional[List[datetime]],
        List[float],
        List[float],
        List[float],
    ]
]:
    df = get_df()

    if df is None:
        return None

    date_window_res = None

    if window_str:
        res_df = calculate_graph_info_with_period(df, window_str)

        date_window_res = res_df.select(COL_NAME_WINDOW_TIME).to_series().to_list()

    else:
        res_df = calculate_graph_info(df)

    per_flights_not_delayed = (
        res_df.select(COL_NAME_PER_FLIGHTS_NOT_DELAYED).to_series().to_list()
    )

    per_delayed_flights_not_with_15min = (
        res_df.select(COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN).to_series().to_list()
    )

    per_delayed_flights_15min_not_with_41_42 = (
        res_df.select(COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_42)
        .to_series()
        .to_list()
    )
    return (
        date_window_res,
        per_flights_not_delayed,
        per_delayed_flights_not_with_15min,
        per_delayed_flights_15min_not_with_41_42,
    )


import plotly.express as px
import pandas as pd

# Sample bar data
df = pd.DataFrame(
    {
        "Category": ["A", "B", "C", "D"],
        "Value1": [4, 7, 1, 5],
        "Value2": [2, 3, 8, 6],
        "Value3": [5, 2, 3, 7],
    }
)

# Generate plots
fig1 = px.bar(df, x="Category", y="Value1", title="Bar Plot 1")
fig2 = px.bar(df, x="Category", y="Value2", title="Bar Plot 2")
fig3 = px.bar(df, x="Category", y="Value3", title="Bar Plot 3")

# Dash app

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H4("1,240", className="card-title"),
                                    html.P("↑ 2.5%", className="text-success"),
                                ]
                            )
                        ],
                        className="shadow-sm",
                    ),
                    width=6,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H4("865", className="card-title"),
                                    html.P("↓ 1.2%", className="text-danger"),
                                ]
                            )
                        ],
                        className="shadow-sm",
                    ),
                    width=6,
                ),
            ],
            className="my-4",
        ),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(figure=fig1), md=4),
                dbc.Col(dcc.Graph(figure=fig2), md=4),
                dbc.Col(dcc.Graph(figure=fig3), md=4),
            ]
        ),
    ],
    fluid=True,
)

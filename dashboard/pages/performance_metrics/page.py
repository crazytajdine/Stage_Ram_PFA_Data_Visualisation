from datetime import datetime
from typing import List, Optional
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, html, dcc, dash_table
from server_instance import get_app

import plotly.graph_objs as go

import polars as pl
from excel_manager import (
    get_df,
    get_count_df,
    add_watcher_for_data,
    COL_NAME_TOTAL_COUNT,
    COL_NAME_WINDOW_TIME,
    COL_NAME_DEPARTURE_DATETIME,
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

app = get_app()

TABLE_COL_NAMES = [
    {"name": "time", "id": COL_NAME_DEPARTURE_DATETIME},
    {"name": "Percentage not delayed", "id": COL_NAME_PER_FLIGHTS_NOT_DELAYED_SHOW},
    {"name": "bla", "id": COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN_SHOW},
    {"name": "blaa", "id": COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46_SHOW},
]


import plotly.express as px

# Sample bar data
import dash_bootstrap_components as dbc
from dash import dcc, html
import plotly.express as px


def calculate_graph_info(df: pl.LazyFrame) -> pl.LazyFrame:

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
    ).select(pl.len().alias(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_41_46_GTE_15MIN))

    joined_df: pl.LazyFrame = pl.concat(
        [
            total_df,
            delayed_flights_count_df,
            delayed_15min_count_df,
            delayed_flights_41_42_gte_15min_count_df,
        ],
        how="horizontal",
    )

    return joined_df


def calculate_graph_info_with_period(df: pl.LazyFrame, window_str: str) -> pl.LazyFrame:

    assert window_str and df is not None

    window_str += "d"
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
    delayed_flights_41_46_gte_15min_count_df = (
        delayed_15min_df.filter(pl.col("CODE_DR").is_in({41, 46}))
        .group_by(COL_NAME_WINDOW_TIME)
        .agg(pl.len().alias(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_41_46_GTE_15MIN))
    )

    joined_df = (
        total_df.join(delayed_flights_count_df, COL_NAME_WINDOW_TIME, how="left")
        .join(delayed_15min_count_df, COL_NAME_WINDOW_TIME, how="left")
        .join(
            delayed_flights_41_46_gte_15min_count_df, COL_NAME_WINDOW_TIME, how="left"
        )
        .fill_null(0)
    )

    joined_df = joined_df.sort(COL_NAME_WINDOW_TIME)

    return joined_df


from dash import dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import polars as pl


def create_graph_card(
    df: pl.DataFrame,
    x: str,
    y: str,
    title: str,
    text=None,
) -> dbc.Card | None:

    if x not in df.columns:
        return None

    len_date = df.select(pl.col(x).len()).item()
    print("len ", len_date)

    # Create figure
    fig = px.bar(df, x=x, y=y, title=title, text=text)
    max_y = df[y].max() * 1.15

    threshold_sep_x = 12
    threshold_show_y = 20

    # Update layout
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title_x=0.5,
        margin=dict(t=50, b=30, l=20, r=20),
        yaxis=dict(range=[0, max_y], visible=len_date > threshold_show_y),
        yaxis_title="",
        xaxis_title="",
    )

    # Style bars
    fig.update_traces(
        textposition="outside" if len_date <= threshold_show_y else "none",
        marker_color="rgb(0, 123, 255)",
        hovertemplate="%{x}<br>%{text}<extra></extra>",
        textfont_size=16,
    )

    # Handle short x-axis
    unique_x = df[x].unique()
    if len(unique_x) <= threshold_sep_x:
        fig.update_xaxes(tickmode="array", tickvals=unique_x)

    # Return the full card component
    return dbc.Card(
        dbc.CardBody([dcc.Graph(figure=fig)]),
        className=f"mb-4",
    )


def generate_card(df: pl.DataFrame, col_name: str, title: str) -> dbc.Card:

    assert df is not None and col_name is not None

    latest_values = df.select(pl.col(col_name).tail(2)).to_series().to_list()
    # Calculate change
    if COL_NAME_WINDOW_TIME in df.columns and len(latest_values) == 2:
        this_year, last_year = latest_values
        change = this_year - last_year
    else:
        this_year = latest_values[0]
        change = None

    # Determine display for change
    if change is None:
        change_div = html.Span("N/A", className="text-secondary")
        stripe_color = "secondary"
    else:
        # positive vs negative
        if change >= 0:
            icon_cls = "bi bi-caret-up-fill"
            color_cls = "text-success"
            stripe_color = "success"
        else:
            icon_cls = "bi bi-caret-down-fill"
            color_cls = "text-danger"
            stripe_color = "danger"

        change_div = html.Div(
            [
                html.I(className=f"{icon_cls} me-1 fs-5"),
                html.Span(f"{abs(change):.1f}%", className="fs-6"),
            ],
            className=f"{color_cls} d-flex justify-content-center align-items-center",
        )

    return dbc.Card(
        [
            # Stripe (header) – fixed 4px height
            dbc.CardHeader(
                [
                    html.Div(
                        className=f"bg-{stripe_color} rounded-top mb-1",
                        style={"height": "4px"},
                    ),
                    html.H5(title, className="text-muted px-4 mb-0"),
                ],
                className="p-0 border-0 text-center bg-transparent",
            ),
            # Body – fixed height (or flex‑fill if you want it to grow)
            dbc.CardBody(
                [
                    html.H2(f"{this_year:.2f}%", className="m-0"),
                ],
                className="d-flex flex-fill align-items-center justify-content-center px-4",
            ),
            # Footer – fixed height
            dbc.CardFooter(
                change_div,
                className="text-center bg-transparent border-0",
            ),
        ],
        className="d-flex flex-column shadow-sm rounded-2 w-100 h-100",
    )


def calculate_result(
    window_str: str = "",
) -> Optional[pl.DataFrame]:
    df = get_df()

    if df is None:
        return None
    print("Calculating window with string:", window_str)

    if window_str:
        res_df = calculate_graph_info_with_period(df, window_str)

    else:
        res_df = calculate_graph_info(df)

    res_df = res_df.with_columns(
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

    res_df = res_df.with_columns(
        [
            (
                pl.col(col)
                .round(2)
                .cast(pl.Utf8)
                .map_elements(lambda v: f"{v}%", return_dtype=pl.Utf8)
                .alias(show_col)
            )
            for col, show_col in columns_to_format
        ]
    )
    return res_df.collect()


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
        dcc.Input(
            id="window",
            type="text",  # or "number", "password", etc.
            placeholder="Enter window size...",
            style={"width": "150px"},
        ),
        dbc.Button("sub", id="submit-button"),
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
        dbc.Row(
            dash_table.DataTable(
                id="result_table_percentage",
                columns=TABLE_COL_NAMES,
                page_size=10,
                style_table={
                    "overflowX": "auto",
                    "margin-top": "10px",
                    "margin-bottom": "40px",
                },
                style_cell={"textAlign": "left"},
                sort_action="native",
            ),
        ),
    ],
    fluid=True,
    className="p-4",
)


@app.callback(
    [
        Output(ID_CARD_DELAY, "children"),
        Output(ID_CARD_DELAY_15MIN, "children"),
        Output(ID_CARD_DELAY_15MIN_41_42, "children"),
        Output(ID_GRAPH_DELAY, "children"),
        Output(ID_GRAPH_DELAY_15MIN, "children"),
        Output(ID_GRAPH_DELAY_41_42_15MIN, "children"),
    ],
    [
        add_watcher_for_data(),
        Input("submit-button", "n_clicks"),
        State("window", "value"),
    ],
)
def create_layout(_, n_clicks, window_str):

    df = get_df()
    if df is None:
        return dash.no_update
    result = calculate_result(window_str)

    if result is None:
        return dash.no_update

    card1 = generate_card(
        result,
        COL_NAME_PER_FLIGHTS_NOT_DELAYED,
        "Percentage of On-Time Flights",
    )  # example first card
    card2 = generate_card(
        result,
        COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN,
        "Percentage of On-Time or Delays Less Than 15 Minutes",
    )  # example second card
    card3 = generate_card(
        result,
        COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46,
        "Percentage of On-Time or less than 15 Minutes, or Delays Not Due to Reasons 41/46",
    )  # example second card

    fig1 = create_graph_card(
        result,
        COL_NAME_WINDOW_TIME,
        COL_NAME_PER_FLIGHTS_NOT_DELAYED,
        "Percentage of On-Time Flights",
        COL_NAME_PER_FLIGHTS_NOT_DELAYED_SHOW,
    )
    fig2 = create_graph_card(
        result,
        COL_NAME_WINDOW_TIME,
        COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN,
        "Percentage of On-Time or Delays Less Than 15 Minutes",
        COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN_SHOW,
    )
    fig3 = create_graph_card(
        result,
        COL_NAME_WINDOW_TIME,
        COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46,
        "Percentage of On-Time or less than 15 Minutes, or Delays Not Due to Reasons 41/46",
        COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46_SHOW,
    )

    return card1, card2, card3, fig1, fig2, fig3

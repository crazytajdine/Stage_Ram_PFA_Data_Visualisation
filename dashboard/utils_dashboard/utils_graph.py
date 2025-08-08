# utils_graph.py

import logging
from typing import Literal
import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px, plotly.graph_objs as go

import polars as pl

from data_managers.excel_manager import COL_NAME_WINDOW_TIME

import plotly.io as pio

pio.templates.default = "plotly"


def create_bar_figure(
    df: pl.DataFrame,
    x: str,
    y: str,
    title: str,
    unit: str = "%",
    color: str | None = None,
    barmode: Literal["group", "stack"] = "group",
    legend_title: str | None = None,
) -> go.Figure | None:

    if x not in df.columns or y not in df.columns:
        return None

    # Create a new column for text display
    df = df.with_columns(
        pl.col(y)
        .round(2)
        .map_elements(lambda v: f"{v:.2f}{unit}", return_dtype=pl.Utf8)
        .alias("text_label")
    )

    len_date = df.select(pl.col(x).len()).item()
    logging.debug("Number of rows in x-axis: %d", len_date)

    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        text="text_label",
        barmode=barmode,
        color=color,
    )

    threshold_sep_x = 12
    threshold_show_y = 20

    fig.update_xaxes(tickformat="%y-%m-%d")

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title_x=0.5,
        margin=dict(t=50, b=30, l=20, r=20),
        yaxis=dict(range=[0, 115], visible=len_date > threshold_show_y),
        yaxis_title="",
        xaxis_title="",
    )

    if legend_title is not None:
        fig.update_layout(legend_title_text=legend_title)

    hover_template_base = (
        "%{x}<br>Percentage : %{text}<br>Detailed : %{y}<extra></extra>"
    )

    fig.update_traces(
        textposition="outside" if len_date <= threshold_show_y else "none",
        textangle=0,
        hovertemplate=hover_template_base,
        textfont_size=16,
    )

    unique_x = df[x].unique()
    logging.debug("Unique values on x-axis: %s", unique_x)
    if len(unique_x) <= threshold_sep_x:
        logging.debug("Setting tickmode to 'array' with tickvals")
        fig.update_xaxes(tickmode="array", tickvals=unique_x)

    return fig


def create_bar_horizontal_figure(
    df: pl.DataFrame,
    x: str,
    y: str,
    title: str,
    unit: str = "%",
    color: str | None = None,
    barmode: Literal["group", "stack"] = "group",
    legend_title: str | None = None,
) -> go.Figure | None:

    if x not in df.columns or y not in df.columns:
        return None

    # Create text label column
    df = df.with_columns((pl.col(x).round(2).cast(str) + unit).alias("text_label"))

    len_date = df.select(pl.col(x).len()).item()
    logging.debug("Number of rows in x-axis: %d", len_date)

    threshold_sep_y = 20
    threshold_show_x = 20

    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        text="text_label",
        orientation="h",
        barmode=barmode,
        color=color,
    )

    fig.update_yaxes(tickformat="%y-%m-%d")

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title_x=0.5,
        margin=dict(t=50, b=30, l=20, r=20),
        xaxis=dict(range=[0, 120], visible=len_date > threshold_show_x),
        yaxis_title="",
        xaxis_title="",
    )

    fig.update_traces(
        textposition=("auto" if len_date <= threshold_show_x else "none"),
        textangle=0,
        hovertemplate="%{y}<br>Percentage : %{text}<br>Detailed : %{x} <extra></extra>",
        textfont_size=16,
    )
    if legend_title is not None:
        fig.update_layout(legend_title_text=legend_title)

    unique_y = df[y].unique()
    logging.debug("Unique values on y-axis: %s", unique_y)
    if len(unique_y) <= threshold_sep_y:
        logging.debug("Setting tickmode to 'array' with tickvals")
        fig.update_yaxes(tickmode="array", tickvals=unique_y)

    return fig



def generate_card_info_change(
    df: pl.DataFrame,
    col_name: str,
    title: str,
    include_footer: bool = True,
    extra_class="",
) -> dbc.Card:

    logging.info(
        "Generating info card for column '%s' with title '%s'", col_name, title
    )

    assert df is not None and col_name is not None

    latest_values = (
        df.drop_nulls(pl.col(col_name))
        .select(pl.col(col_name).tail(2))
        .to_series()
        .to_list()
    )
    logging.debug("Latest non-null values: %s", latest_values)

    if COL_NAME_WINDOW_TIME in df.columns and len(latest_values) == 2:
        last_year, this_year = latest_values
        change = this_year - last_year
        logging.debug("Calculated change: %f (this_year - last_year)", change)

    elif len(latest_values) == 1:
        this_year = latest_values[0]
        change = None
        logging.debug("Only one latest value available: %f", this_year)

    else:
        this_year = None
        change = None
        logging.warning(
            "Not enough data to calculate change. Latest values: %s", latest_values
        )

    if change is None:
        change_div = html.Span("N/A", className="text-secondary")
        stripe_color = "secondary"
    else:
        if change >= 0:
            icon_cls, color_cls, stripe_color = (
                "bi-caret-up-fill",
                "text-success",
                "success",
            )
        else:
            icon_cls, color_cls, stripe_color = (
                "bi-caret-down-fill",
                "text-danger",
                "danger",
            )

        change_div = html.Div(
            [
                html.I(className=f"{icon_cls} me-1 fs-5"),
                html.Span(f"{abs(change):.2f}%", className="fs-6"),
            ],
            className=f"{color_cls} d-flex justify-content-center align-items-center",
        )

    children = [
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
        dbc.CardBody(
            [
                html.H2(
                    f"{this_year:.2f}%" if this_year is not None else "N/A",
                    className="m-0",
                ),
            ],
            className="d-flex flex-fill align-items-center justify-content-center px-4",
        ),
    ]

    if include_footer:
        children.append(
            dbc.CardFooter(
                change_div,
                className="text-center bg-transparent border-0",
            )
        )

    return dbc.Card(
        children,
        className="d-flex flex-column shadow-sm rounded-2 w-100 h-100",
    )

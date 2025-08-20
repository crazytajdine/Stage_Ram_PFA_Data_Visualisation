# utils_graph.py

import logging
from typing import Literal, Optional
import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px
import plotly.graph_objs as go

import polars as pl

from data_managers.excel_manager import COL_NAME_WINDOW_TIME

import plotly.io as pio

pio.templates.default = "plotly"


plot_config = {
    # everything else you already put in config …
    "toImageButtonOptions": {
        "format": "png",  # or "svg" / "pdf" for vector
        "filename": "codes-chart",
        "width": 1600,  # px  (≈ A4 landscape)
        "height": 600,  # px
        "scale": 3,  # 3× pixel-density → crisp on Retina
    }
}


def create_bar_figure(
    df: pl.DataFrame,
    x: str,
    y: str,
    title: str,
    x_max: Optional[str] = None,
    unit: str = "%",
    color: Optional[str] = None,
    barmode: Literal["auto", "group", "stack"] = "auto",
    legend_title: Optional[str] = None,
    value_other: Optional[float] = None,
) -> Optional[go.Figure]:

    if x not in df.columns or y not in df.columns:
        return go.Figure()

    df = df.sort([x, y], descending=[False, True])

    color_column = color
    if value_other:
        df = df.with_columns(
            pl.when(pl.col(y) < value_other)
            .then(pl.lit("Other"))
            .otherwise(pl.col(color))
            .alias("color_other")
        )
        color_column = "color_other"

    # Create a new column for text display
    df = df.with_columns(
        pl.col(y)
        .round(2)
        .map_elements(lambda v: f"{v:.2f}{unit}", return_dtype=pl.Utf8)
        .alias("text_label")
    )

    len_date = df.select(pl.col(x).len()).item()
    logging.debug("Number of rows in x-axis: %d", len_date)

    custom_data_cols = []
    index_map = {}

    x_max_valid = x_max and x_max in df.columns
    if x_max_valid:
        index_map["x_max"] = len(custom_data_cols)
        custom_data_cols.append(x_max)
    color_valid = color and color in df.columns
    if color_valid:

        df = df.with_columns(pl.col(color).cast(pl.Utf8))
        index_map["color"] = len(custom_data_cols)
        custom_data_cols.append(color)
        distinct_colors = df.select(pl.col(color)).n_unique()

        distinct_time = df.select(pl.col(x)).n_unique()
        if barmode == "auto":
            barmode = "stack" if (distinct_colors * distinct_time) > 10 else barmode
    if barmode == "auto":
        barmode = "group"
    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        text="text_label",
        barmode=barmode,
        color=color_column,
        custom_data=custom_data_cols if custom_data_cols else None,
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

    x_label_template = (
        f"From %{{x}} to %{{customdata[{index_map['x_max']}]}}<br>"
        if "x_max" in index_map
        else "%{x}<br>"
    )

    color_template = (
        f"{legend_title} : %{{customdata[{index_map['color']}]}}<br>"
        if "color" in index_map
        else ""
    )

    fig.update_traces(
        textposition="auto",
        marker=dict(cornerradius=4),
        textangle=0,
        hovertemplate=(
            x_label_template
            + color_template
            + "value : %{text}<br>"
            + "<extra></extra>"
        ),
        textfont_size=16,
    )

    unique_x = df[x].unique()
    logging.debug("Unique values on x-axis: %s", unique_x)
    if len(unique_x) <= threshold_sep_x:
        logging.debug("Setting tickmode to 'array' with tickvals")
        fig.update_xaxes(type="category", categoryorder="array", categoryarray=unique_x)

    return fig


def create_bar_horizontal_figure(
    df: pl.DataFrame,
    x: str,
    y: str,
    title: str,
    y_max: Optional[str] = None,
    unit: str = "%",
    color: Optional[str] = None,
    barmode: Literal["group", "stack"] = "group",
    legend_title: Optional[str] = None,
    value_other: Optional[float] = None,
) -> Optional[go.Figure]:

    if x not in df.columns or y not in df.columns:
        return None

    color_column = color
    if value_other:
        df = df.with_columns(
            pl.when(pl.col(y) < value_other)
            .then(pl.lit("Other"))
            .otherwise(pl.col(color))
            .alias("color_other")
        )
        color_column = "color_other"
    # Text label for bar display
    df = df.with_columns((pl.col(x).round(2).cast(str) + unit).alias("text_label"))

    len_date = df.select(pl.col(x).len()).item()
    logging.debug("Number of rows in x-axis: %d", len_date)

    threshold_sep_y = 20
    threshold_show_x = 20

    custom_data_cols = []
    index_map = {}

    if y_max and y_max in df.columns:
        index_map["y_max"] = len(custom_data_cols)
        custom_data_cols.append(y_max)

    if color and color in df.columns:
        df = df.with_columns(pl.col(color).cast(pl.Utf8))

        index_map["color"] = len(custom_data_cols)
        custom_data_cols.append(color)

    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        text="text_label",
        orientation="h",
        barmode=barmode,
        color=color_column,
        custom_data=custom_data_cols,
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

    y_label_template = (
        f"From %{{y}} to %{{customdata[{index_map['y_max']}]}}<br>"
        if "y_max" in index_map
        else "%{y}<br>"
    )

    color_template = (
        f"{legend_title} : %{{customdata[{index_map['color']}]}}<br>"
        if "color" in index_map
        else ""
    )
    fig.update_traces(
        textposition="auto",
        textangle=0,
        hovertemplate=(
            y_label_template
            + color_template
            + "value : %{text}<br>"
            + "<extra></extra>"
        ),
        textfont_size=16,
        marker=dict(cornerradius=4),
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
        stripe_color = "transparent"
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
                    className=f"bg-{stripe_color}  ",
                    style={"height": "6px"},
                ),
                html.H5(title, className="text-muted px-4 mb-0"),
            ],
            className="p-0 border-0 text-center bg-transparent  ",
            style={
                "border-top-left-radius": "0.5rem",
                "border-top-right-radius": "0.5rem",
                "overflow": "hidden",
            },
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
                style={"fontWeight": "300"},
            )
        )

    return dbc.Card(
        children,
        className="d-flex flex-column shadow-sm rounded-2 w-100 h-100",
    )


def create_navbar(
    df,
    tabs: str,
    x: str,
    y,
    title: str,
    color: str,
    x_max: Optional[str] = None,
    unit: str = "%",
    legend_title: Optional[str] = None,
    value_other: Optional[float] = None,
):
    by_fam = df.partition_by(tabs, as_dict=True, maintain_order=True)

    tab_children = []
    for fam, fam_data in by_fam.items():
        fam = fam[0]
        fig = create_bar_figure(
            df=fam_data,
            x=x,
            x_max=x_max,
            y=y,
            unit=unit,
            title=title.format(fam=fam),
            color=color,
            legend_title=legend_title,
            value_other=value_other,
        )
        tab_children.append(
            dcc.Tab(
                label=fam,
                value=fam,
                children=[
                    dcc.Graph(
                        figure=fig,
                        config=plot_config,
                        style={
                            "backgroundColor": "white",
                            "boxShadow": "0px 4px 6px rgba(0, 0, 0, 0.1)",
                            "borderBottomLeftRadius": "12px",
                            "borderBottomRightRadius": "12px",
                            "padding": "10px",
                            "border": "1px solid #d6d6d6",
                            "borderTop": "none",
                            "height": "80vh",
                        },
                    )
                ],
                selected_style={
                    "borderTop": "3px solid var(--ram-red)",
                },
            )
        )

    return tab_children

"""
weekly_analysis_page.py – Weekly Analysis of Delay Codes
"""

# ─────────────── Standard library ───────────────
from dash import html, dash_table, Output, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

# ─────────────── Application modules ───────────────
from calculations.weekly import analyze_weekly_codes, COL_NAME_DATE_PERCENTAGE
from utils_dashboard.utils_download import (
    add_export_callbacks,
)
from server_instance import get_app
from data_managers.excel_manager import (
    add_watcher_for_data,
    # COL_NAME_TOTAL_COUNT  # only needed if you reuse it here
)

from utils_dashboard.utils_graph import create_bar_figure

import polars as pl

app = get_app()


# ------------------------------------------------------------------ #
# 3 ▸  Layout                                                       #
# ------------------------------------------------------------------ #
ID_WEEKLY_TABLE = "weekly-table"
ID_WEEKLY_TABLE_PERCENTAGE = "weekly-table-percentage"
ID_WEEKLY_BARS = "weekly-bars"
layout = dbc.Container(
    fluid=True,
    className="p-4",
    children=[
        dbc.Card(
            dbc.CardBody(dcc.Graph(id=ID_WEEKLY_BARS), class_name="graph"),
            className="mb-4",
        ),
        dbc.Button(
            [html.I(className="bi bi-download me-2"), "Exporter Excel"],
            id="weekly-export-btn",
            className="btn-export mt-2",
            n_clicks=0,
        ),
        dbc.Card(
            dbc.CardBody(
                dash_table.DataTable(
                    id=ID_WEEKLY_TABLE,
                    style_table={"overflowX": "auto"},
                    style_data_conditional=[
                        {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"},
                        {"if": {"row_index": "even"}, "backgroundColor": "white"},
                    ],
                )
            ),
            className="mb-4",
        ),
        dbc.Button(
            [html.I(className="bi bi-download me-2"), "Exporter Excel"],
            id="weekly-export-percentage-btn",
            className="btn-export mt-2",
            n_clicks=0,
        ),
        dbc.Card(
            dbc.CardBody(
                dash_table.DataTable(
                    id=ID_WEEKLY_TABLE_PERCENTAGE,
                    style_table={"overflowX": "auto"},
                    style_data_conditional=[
                        {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"},
                        {"if": {"row_index": "even"}, "backgroundColor": "white"},
                    ],
                )
            ),
            className="mb-4",
        ),
    ],
)


# ------------------------------------------------------------------ #
# 4 ▸  Callbacks                                                    #
# ------------------------------------------------------------------ #


@app.callback(
    Output(ID_WEEKLY_TABLE, "data"),
    Output(ID_WEEKLY_TABLE, "columns"),
    Output(ID_WEEKLY_TABLE_PERCENTAGE, "data"),
    Output(ID_WEEKLY_TABLE_PERCENTAGE, "columns"),
    Output(ID_WEEKLY_BARS, "figure"),
    add_watcher_for_data(),
)
def refresh_weekly_table(_):
    df, days_cols = analyze_weekly_codes()
    percentage_col_names = [COL_NAME_DATE_PERCENTAGE.format(c=c) for c in days_cols]
    if df is None:
        return [], [], [], [], go.Figure()

    data = df.to_dicts()

    columns = (
        [{"id": "DELAY_CODE", "name": "Code"}]
        + [{"id": d, "name": d} for d in days_cols]
        + [{"id": "Total", "name": "Total"}]
    )

    df_percentage: pl.DataFrame = df.select(pl.exclude([*days_cols, "Total"])).rename(
        {c: c.replace("_pct", "") for c in percentage_col_names}
    )

    data_percentage = df_percentage.to_dicts()

    columns_percentage = [{"id": "DELAY_CODE", "name": "Code"}] + [
        {"id": d, "name": d} for d in days_cols
    ]

    df_long = df_percentage.unpivot(
        index=["DELAY_CODE"],
        on=days_cols,
        variable_name="Day",
        value_name="Percentage",
    )

    fig = create_bar_figure(
        df_long,
        "Day",
        "Percentage",
        title="Distribution of codes by day of the week",
        color="DELAY_CODE",
        legend_title="Delay code",
        barmode="group",
    )

    return data, columns, data_percentage, columns_percentage, fig


add_export_callbacks(
    ID_WEEKLY_TABLE, "weekly-export-btn", "weekly_delay_codes_analysis"
)

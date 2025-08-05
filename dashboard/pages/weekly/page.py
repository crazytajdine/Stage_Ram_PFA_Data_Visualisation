"""
weekly_analysis_page.py – Weekly Analysis of Delay Codes
"""

# ─────────────── Standard library ───────────────
from datetime import datetime

# ─────────────── Third-party ───────────────
import polars as pl
import dash
from dash import html, dash_table, Output
import dash_bootstrap_components as dbc

# ─────────────── Application modules ───────────────
from utils_dashboard.utils_download import (
    add_export_callbacks,
)
from server_instance import get_app
from excel_manager import (
    get_df,
    add_watcher_for_data,
    # COL_NAME_TOTAL_COUNT  # only needed if you reuse it here
)


DAYS_EN = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

DAY_NAME_MAP = {i: d for i, d in enumerate(DAYS_EN)}

app = get_app()

CELL_STYLE = {
    "backgroundColor": "white",
    "border": "1px solid #dee2e6",
    "textAlign": "center",
    "padding": "8px",
    "fontSize": "11px",
}
HEADER_STYLE = CELL_STYLE | {
    "backgroundColor": "#f8f9fa",
    "fontWeight": "bold",
    "color": "#495057",
}

# ------------------------------------------------------------------ #
# 2 ▸  Helper functions                                              #
# ------------------------------------------------------------------ #


def analyze_weekly_codes() -> tuple[list[dict], list[dict]]:
    df_lazy = get_df()
    if df_lazy is None:
        return [], []

    df = (
        df_lazy.sort("DEP_DAY_SCHED")
        .with_columns(
            pl.col("DEP_DAY_SCHED").dt.strftime("%A").alias("DAY_OF_WEEK_DEP")
        )
        .collect()
    )

    if df.is_empty():
        return [], []

    # Group and pivot
    pivot = (
        df.group_by(["DELAY_CODE", "DAY_OF_WEEK_DEP"])
        .agg(pl.len().alias("n"))
        .pivot(values="n", index="DELAY_CODE", columns="DAY_OF_WEEK_DEP")
        .fill_null(0)
    )

    # Preserve day order based on first appearance
    days_ordered = list(dict.fromkeys(df["DAY_OF_WEEK_DEP"].to_list()))
    if not days_ordered:
        return [], []

    # Reorder and add Total
    pivot = (
        pivot.select("DELAY_CODE", *days_ordered)
        .with_columns(pl.sum_horizontal(days_ordered).alias("Total"))
        .sort("Total", descending=True)
    )

    columns = (
        [{"id": "DELAY_CODE", "name": "Code"}]
        + [{"id": d, "name": d} for d in days_ordered]
        + [{"id": "Total", "name": "Total"}]
    )

    return pivot.to_dicts(), columns


# ------------------------------------------------------------------ #
# 3 ▸  Layout                                                       #
# ------------------------------------------------------------------ #
ID_WEEKLY_TABLE = "weekly-table"

layout = dbc.Container(
    fluid=True,
    className="p-4",
    children=[
        dbc.Row(
            dbc.Col(
                [
                    html.H1("Weekly Analysis of Delay Codes"),
                    html.P(
                        "Distribution of codes by day of the week.",
                        className="lead",
                    ),
                ]
            )
        ),
        dbc.Button("Export Excel", id="weekly-export-btn", className="my-2"),
        dbc.Card(
            dbc.CardBody(dash_table.DataTable(id=ID_WEEKLY_TABLE)), className="mb-4"
        ),
        dbc.Row(
            dbc.Col(
                [html.Hr(), html.Small(id="last-update", className="text-muted")],
                className="text-center",
            )
        ),
    ],
)


# ------------------------------------------------------------------ #
# 4 ▸  Callbacks                                                    #
# ------------------------------------------------------------------ #


@app.callback(
    Output(ID_WEEKLY_TABLE, "data"),
    Output(ID_WEEKLY_TABLE, "columns"),
    Output("last-update", "children"),
    add_watcher_for_data(),
)
def refresh_weekly_table(_):
    data, columns = analyze_weekly_codes()
    if not data:
        return [], [], "No data available"

    return data, columns, f"Last updated: {datetime.now():%d/%m/%Y %H:%M}"


add_export_callbacks(
    ID_WEEKLY_TABLE, "weekly-export-btn", "weekly_delay_codes_analysis"
)

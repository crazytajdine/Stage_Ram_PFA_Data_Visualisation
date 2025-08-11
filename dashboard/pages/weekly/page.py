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
from calculations.weekly import analyze_weekly_codes
from utils_dashboard.utils_download import (
    add_export_callbacks,
)
from server_instance import get_app
from data_managers.excel_manager import (
    get_df,
    add_watcher_for_data,
    # COL_NAME_TOTAL_COUNT  # only needed if you reuse it here
)


app = get_app()


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
                    html.H2(
                        "Distribution of codes by day of the week.",
                        className="lead",
                    ),
                ]
            )
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
                        {
                            "if": {"row_index": "odd"},
                            "backgroundColor": "#f8f9fa",  # light gray
                        },
                        {
                            "if": {"row_index": "even"},
                            "backgroundColor": "white",
                        },
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
    add_watcher_for_data(),
)
def refresh_weekly_table(_):
    df = analyze_weekly_codes()

    if df is None:
        return [], []

    data = df.to_dicts()

    # preserve the pivot's column order:
    days = [c for c in df.columns if c not in ("DELAY_CODE", "Total")]

    columns = (
        [{"id": "DELAY_CODE", "name": "Code"}]
        + [{"id": d, "name": d} for d in days]
        + [{"id": "Total", "name": "Total"}]
    )

    return data, columns


add_export_callbacks(
    ID_WEEKLY_TABLE, "weekly-export-btn", "weekly_delay_codes_analysis"
)

"""
weekly_analysis_page.py – Weekly Analysis of Delay Codes
"""

# ─────────────── Standard library ───────────────
from datetime import date, datetime

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

# ─────────────── Third-party ───────────────
import polars as pl

# ─────────────── Application modules ───────────────
from calculations.weekly import analyze_weekly_codes
from dash import Output, dash_table, dcc, html
from data_managers.excel_manager import add_watcher_for_data, get_df
from server_instance import get_app
from utils_dashboard.utils_download import add_export_callbacks

app = get_app()

# ------------------------------------------------------------------ #
# Helpers                                                            #
# ------------------------------------------------------------------ #

# Day palettes (adjust if your labels differ)
_EN_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_EN_FULL = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
_FR_SHORT = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
_FR_FULL = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


def _detect_palette(days: list[str]) -> list[str] | None:
    s = set(days)
    for p in (_EN_SHORT, _EN_FULL, _FR_SHORT, _FR_FULL):
        if any(d in s for d in p):
            return p
    return None


def _first_selected_weekday() -> int | None:
    """
    Infer start weekday (Mon=0..Sun=6) from the MIN date of the currently filtered data.
    """
    src = get_df()
    if src is None:
        return None
    if isinstance(src, pl.LazyFrame):
        try:
            src = src.select_first().collect()  # tiny collect if possible
        except Exception:
            src = src.collect()

    # Guess a date column name (add yours if different)
    candidates = ["DEP_DATE", "DEP_DAY_SCHED", "DATE", "DEP_TIME_SCHED"]
    date_col = next((c for c in candidates if c in src.columns), None)
    if date_col is None:
        return None

    try:
        if src.schema[date_col] == pl.Utf8:
            src = src.with_columns(pl.col(date_col).str.strptime(pl.Date, strict=False))
        elif src.schema[date_col] == pl.Datetime:
            src = src.with_columns(pl.col(date_col).cast(pl.Date))

        min_dt = src.select(pl.col(date_col).min()).to_series().item()
        if isinstance(min_dt, datetime):
            min_dt = min_dt.date()
        if isinstance(min_dt, date):
            return min_dt.weekday()  # Mon=0..Sun=6
    except Exception:
        return None
    return None


def _rotate_days(days: list[str]) -> list[str]:
    """
    Rotate the weekday labels so they start from the first selected weekday.
    If no palette or weekday can be inferred, return `days` unchanged.
    """
    if not days:
        return days

    palette = _detect_palette(days)
    start_idx = _first_selected_weekday()
    if palette is None or start_idx is None:
        return days

    rotated = palette[start_idx:] + palette[:start_idx]
    # Keep only labels that exist in the DF (preserve rotated order)
    present = set(days)
    return [d for d in rotated if d in present]


# ------------------------------------------------------------------ #
# Layout                                                             #
# ------------------------------------------------------------------ #
ID_WEEKLY_TABLE = "weekly-table"
ID_WEEKLY_BARS = "weekly-bars"

layout = dbc.Container(
    fluid=True,
    className="p-4",
    children=[
        dbc.Row(
            dbc.Col(
                html.H2("Distribution of codes by day of the week.", className="lead")
            )
        ),
        dbc.Card(dbc.CardBody(dcc.Graph(id=ID_WEEKLY_BARS)), className="mb-4"),
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
    ],
)

# ------------------------------------------------------------------ #
# Callbacks                                                          #
# ------------------------------------------------------------------ #


# TABLE — same data, only column order is rotated to start from first selected day.
@app.callback(
    Output(ID_WEEKLY_TABLE, "data"),
    Output(ID_WEEKLY_TABLE, "columns"),
    add_watcher_for_data(),
)
def refresh_weekly_table(_):
    df = (
        analyze_weekly_codes()
    )  # Expect: Polars DF with columns: DELAY_CODE, <days...>, [Total]

    if df is None:
        return [], []

    data = df.to_dicts()

    # Get day columns exactly as they come from your pipeline
    day_cols = [c for c in df.columns if c not in ("DELAY_CODE", "Total")]
    # Rotate order so it starts at the first selected weekday
    rotated = _rotate_days(day_cols)

    columns = (
        [{"id": "DELAY_CODE", "name": "Code"}]
        + [{"id": d, "name": d} for d in rotated]
        + ([{"id": "Total", "name": "Total"}] if "Total" in df.columns else [])
    )
    return data, columns


# CHART — grouped bars, one color per code, same rotated day order, sums duplicates
@app.callback(
    Output(ID_WEEKLY_BARS, "figure"),
    add_watcher_for_data(),
)
def build_weekly_bars(_):
    df = analyze_weekly_codes()
    fig = go.Figure().update_layout(
        xaxis_title="",
        yaxis_title="Occurrences",
        barmode="group",
        legend_title="Code",
        hovermode="x unified",
    )
    if df is None or df.is_empty():
        return fig

    day_cols = [c for c in df.columns if c not in ("DELAY_CODE", "Total")]
    rotated = _rotate_days(day_cols)
    if not rotated:
        return fig

    # Long format, then GROUP (sum) to merge multiple same weekdays across weeks
    long_df = (
        df.melt(
            id_vars="DELAY_CODE",
            value_vars=rotated,  # use rotated order
            variable_name="Day",
            value_name="Occ",
        )
        .with_columns(
            [
                pl.col("Occ").cast(pl.Float64, strict=False).fill_null(0.0),
                pl.col("Day").cast(pl.Utf8),
                pl.col("DELAY_CODE").cast(pl.Utf8),
            ]
        )
        .group_by(["DELAY_CODE", "Day"])
        .agg(pl.col("Occ").sum().alias("Occ"))
    )

    # Build traces; keep X order exactly as `rotated`
    codes = long_df.select("DELAY_CODE").unique().to_series().to_list()
    for code in codes:
        y_vals = (
            long_df.filter(pl.col("DELAY_CODE") == code)
            .join(
                pl.DataFrame({"Day": rotated}),  # ensures we follow rotated order
                on="Day",
                how="right",
            )
            .select(pl.col("Occ").fill_null(0.0))
            .to_series()
            .to_list()
        )
        fig.add_bar(name=str(code), x=rotated, y=y_vals)

    # Lock x-axis category order to the rotated list
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=rotated)
    return fig


# Export (unchanged)
add_export_callbacks(
    ID_WEEKLY_TABLE, "weekly-export-btn", "weekly_delay_codes_analysis"
)

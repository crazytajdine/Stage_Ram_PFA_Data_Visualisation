"""
weekly_analysis_page.py – Weekly Analysis of Delay Codes
"""

# ─────────────── Standard library ───────────────
from datetime import date, datetime

import dash_bootstrap_components as dbc
import plotly.graph_objects as go

# ─────────────── Third-party ───────────────
import polars as pl

# ─────────────── Application modules ───────────────
from calculations.weekly import analyze_weekly_codes
from dash import Output, dash_table, dcc, html, State, Input, callback
from data_managers.excel_manager import add_watcher_for_data, get_df
from server_instance import get_app

# utils for consistent graphs
try:
    from utils_dashboard.utils_graph import create_bar_figure
except ImportError:
    from utils_dashboard.utils_graph import create_bar_figure

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
@callback(
    Output("weekly-bars", "figure"),  # ← keep your real graph id
    Input(ID_WEEKLY_TABLE, "data"),  # ← your DataTable id
    State(ID_WEEKLY_TABLE, "columns"),
)
def bars_pct_from_table(rows, cols):
    base_fig = go.Figure().update_layout(
        xaxis_title="",
        yaxis_title="Share (%)",
        barmode="stack",
        legend_title="Code",
        hovermode="x unified",
    )
    if not rows:
        return base_fig

    # 1) Column ids & order (preserve table order for X axis)
    column_ids = [c["id"] if isinstance(c, dict) else c for c in (cols or [])] or list(
        rows[0].keys()
    )

    CODE_COL_CANDIDATES = ["DELAY_CODE", "Code", "CODE"]
    TOTAL_COLS = {"Total", "TOTAL", "Somme", "SUM"}

    code_col = next((c for c in CODE_COL_CANDIDATES if c in column_ids), None)
    if code_col is None:
        # fallback: first non-numeric column
        sample = rows[0]
        code_col = next((c for c in column_ids if not _is_number(sample.get(c))), None)

    # numeric day columns (exclude code + total-like)
    day_cols = [
        c
        for c in column_ids
        if c != code_col
        and c not in TOTAL_COLS
        and any(_is_number(r.get(c)) for r in rows)
    ]
    if not code_col or not day_cols:
        return base_fig

    # 2) Day totals directly from table values
    day_totals = {d: 0.0 for d in day_cols}
    for r in rows:
        for d in day_cols:
            v = _to_float(r.get(d))
            if v is not None:
                day_totals[d] += max(v, 0.0)

    # 3) Build long-format records with percentages (no extra calc beyond table)
    long_pct = []
    for r in rows:
        code_val = "" if r.get(code_col) is None else str(r.get(code_col))
        for d in day_cols:
            total = day_totals.get(d, 0.0)
            occ = _to_float(r.get(d)) or 0.0
            pct = (occ / total * 100.0) if total > 0 else 0.0
            long_pct.append({"Day": d, "Pct": pct, "DELAY_CODE": code_val})

    # 4) Convert to Polars DF (required by utils_graph.create_bar_figure)
    df_pl = pl.DataFrame(long_pct).with_columns(
        [
            pl.col("Day").cast(pl.Utf8),
            pl.col("DELAY_CODE").cast(pl.Utf8),
            pl.col("Pct").cast(pl.Float64),
        ]
    )

    # 5) Build figure with util (100% stacked)
    fig = (
        create_bar_figure(
            df=df_pl,
            x="Day",
            y="Pct",
            title="",
            x_max=None,
            unit="%",
            color="DELAY_CODE",
            barmode="stack",
            legend_title="Code",
        )
        or base_fig
    )

    # 6) Keep table day order & cap axis
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=day_cols)
    fig.update_yaxes(range=[0, 100])

    return fig


# Helpers (already in your file, keep them; shown here for completeness)
def _is_number(x) -> bool:
    try:
        float(str(x).replace(",", "."))
        return True
    except Exception:
        return False


def _to_float(x):
    try:
        return float(str(x).replace(",", "."))
    except Exception:
        return None


def _to_float(x):
    try:
        return float(str(x).replace(",", "."))
    except Exception:
        return None

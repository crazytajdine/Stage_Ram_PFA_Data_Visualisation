"""
weekly_analysis_page.py – Weekly Analysis of Delay Codes
"""

 # ─────────────── Standard library ───────────────
from datetime import datetime, date, timedelta
import io

 # ─────────────── Third-party ───────────────
import polars as pl
import dash
from dash import html, dcc, dash_table, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import xlsxwriter

 # ─────────────── Application modules ───────────────
from server_instance import get_app
from excel_manager import (
     get_df,
     add_watcher_for_data,
     COL_NAME_DEPARTURE_DATETIME,
     COL_NAME_WINDOW_TIME,
    # COL_NAME_TOTAL_COUNT  # only needed if you reuse it here
 )
from dash.dcc import send_bytes
from components.filter import FILTER_STORE_ACTUAL
from filter_state import get_filter_state


DAYS_FR = ("Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche")
DAY_NAME_MAP = {i: d for i, d in enumerate(DAYS_FR)}

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


def _blank_weekly_table() -> pl.DataFrame:
    return pl.DataFrame({
        "CODE_DR": ["-"],
        **{day: [0] for day in DAYS_FR},
        "Total": [0]
    })

def analyze_weekly_codes() -> tuple[pl.DataFrame, list[str]]:
    # ① read & sort chronologically ------------------------------------------------
    df_lazy = get_df()
    if df_lazy is None:
        return _blank_weekly_table(), DAYS_FR

    df = (
        df_lazy
        .sort("DEP_DAY_SCHED", descending=False)   # oldest → newest
        .collect()
    )

    if df.is_empty() or "DAY_OF_WEEK_DEP" not in df.columns:
        return _blank_weekly_table(), DAYS_FR

    # ② build the aggregation ------------------------------------------------------
    # this already SUMS all flights that share the same French day name
    pivot = (
        df
        .group_by(["CODE_DR", "DAY_OF_WEEK_DEP"])
        .agg(pl.len().alias("n"))
        .pivot(values="n", index="CODE_DR", columns="DAY_OF_WEEK_DEP")
        .fill_null(0)
    )

    # ③ extract the day names in *chronological* order, deduplicated ---------------
    raw_days = (
        df
        .select("DEP_DAY_SCHED", "DAY_OF_WEEK_DEP")
        .sort("DEP_DAY_SCHED")                       # keep chrono order
        .get_column("DAY_OF_WEEK_DEP")
        .to_list()
    )

    seen: set[str]      = set()
    days_ordered: list[str] = []
    for d in raw_days:          # preserves first‑appearance order
        if d not in seen:
            seen.add(d)
            days_ordered.append(d)

    if not days_ordered:                    # fallback, should not happen
        return _blank_weekly_table(), DAYS_FR

    # ④ re‑order columns + add Total ----------------------------------------------
    pivot = (
        pivot
        .select("CODE_DR", *days_ordered)           # no duplicates now
        .with_columns(pl.sum_horizontal(days_ordered).alias("Total"))
        .sort("Total", descending=True)
    )

    return pivot, days_ordered

# ------------------------------------------------------------------ #
# 3 ▸  Layout                                                       #
# ------------------------------------------------------------------ #
ID_WEEKLY_TABLE = "weekly-table"
ID_DOWNLOAD      = "weekly-download"

layout = dbc.Container(
    fluid=True, className="p-4", children=[
        dbc.Row(dbc.Col([
            html.H1("Analyse hebdomadaire des codes de retard"),
            html.P("Répartition des codes par jour de la semaine.", className="lead")
        ])),
        dcc.Download(id=ID_DOWNLOAD),
        dbc.Button("📥 Exporter Excel", id="weekly-export-btn", className="mt-2"),
        dbc.Card(dbc.CardBody(dash_table.DataTable(id=ID_WEEKLY_TABLE)), className="mb-4"),
        dbc.Row(dbc.Col([
            html.Hr(),
            html.Small(id="last-update", className="text-muted")
        ], className="text-center"))
])


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
    weekly, days_ordered = analyze_weekly_codes()
    if weekly.is_empty():
        return [], [], "Aucune donnée"

    columns = [{"id": "CODE_DR", "name": "Code"}] + \
              [{"id": d, "name": d} for d in days_ordered] + \
              [{"id": "Total", "name": "Total"}]

    return weekly.to_dicts(), columns, f"Dernière mise à jour : {datetime.now():%d/%m/%Y %H:%M}"


@app.callback(
    Output(ID_DOWNLOAD, "data"),
    Input("weekly-export-btn", "n_clicks"),
    State(FILTER_STORE_ACTUAL, "data"),  # 👈 get current filters
    prevent_initial_call=True,
)
def export_to_excel(n_clicks, _):
    # analyze_weekly_codes fetches its own data internally
    weekly, days = analyze_weekly_codes()
    if weekly.is_empty():
        raise dash.exceptions.PreventUpdate

    filters = get_filter_state() or {}
    start = filters.get("dt_start") or "ALL"
    end = filters.get("dt_end") or "ALL"
    seg = filters.get("fl_segmentation") or "ALL"
    flotte = filters.get("fl_subtype") or "ALL"
    matricule = filters.get("fl_matricule") or "ALL"

    if isinstance(seg, str) and seg.endswith("d"):
        seg = seg.replace("d", "j")

    fname_parts = ["weekly_analysis"]

    # Ajout des dates
    if start != "ALL" and end != "ALL":
        fname_parts.append(f"{start.replace('_', '/')}to{end.replace('_', '/')}")
    else:
        fname_parts.append("ALL_DATES")

    # Ajout de la segmentation
    if seg != "ALL":
        fname_parts.append(f"seg{seg}")
    else:
        fname_parts.append("ALL_SEG")
    # Ajout de la flotte
    if flotte != "ALL":
        fname_parts.append(f"flotte{flotte}")
    else:
        fname_parts.append("ALL_FLOTTE")
    # Ajout du matricule
    if matricule != "ALL":
        fname_parts.append(f"matricule{matricule}")
    else:
        fname_parts.append("ALL_MATRICULE")

    filename = "_".join(fname_parts) + ".xlsx"


    # Create file
    buffer = io.BytesIO()
    with xlsxwriter.Workbook(buffer, {"in_memory": True}) as wb:
        weekly.write_excel(workbook=wb)
    buffer.seek(0)

    return send_bytes(lambda s: s.write(buffer.getvalue()), filename=filename)

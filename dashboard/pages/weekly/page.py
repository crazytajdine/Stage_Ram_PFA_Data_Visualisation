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


def get_day_name(date_val: date | str) -> str:
    if isinstance(date_val, str):
        date_val = datetime.fromisoformat(date_val).date()
    return DAY_NAME_MAP[date_val.weekday()]


def _blank_weekly_table() -> pl.DataFrame:
    return pl.DataFrame({
        "CODE_DR": ["-"],
        **{day: [0] for day in DAYS_FR},
        "Total": [0]
    })


def analyze_weekly_codes() -> pl.DataFrame:
    df_lazy = get_df()
    if df_lazy is None:
        return _blank_weekly_table()

    df = df_lazy.collect()
    if df.is_empty():
        return _blank_weekly_table()

    # 💡 Vérifie la plage de dates (en jours) du DataFrame
    if COL_NAME_DEPARTURE_DATETIME not in df.columns:
        return _blank_weekly_table()

    try:
        dates = df.select(COL_NAME_DEPARTURE_DATETIME).to_series()
        min_date = dates.min()
        max_date = dates.max()

        if (max_date - min_date).days >= 7:
            return _blank_weekly_table()
    except Exception:
        # En cas de format incohérent ou conversion ratée
        return _blank_weekly_table()

    # Ajouter le nom du jour de la semaine
    df = df.with_columns(
        pl.col(COL_NAME_DEPARTURE_DATETIME)
          .map_elements(get_day_name, pl.Utf8)
          .alias("day_of_week")
    )

    # Group by + pivot
    pivot = (
        df
        .group_by(["CODE_DR", "day_of_week"])
        .agg(pl.len().alias("n"))
        .pivot(values="n", index="CODE_DR", columns="day_of_week")
        .fill_null(0)
    )

    # Ajouter les jours manquants
    for day in DAYS_FR:
        if day not in pivot.columns:
            pivot = pivot.with_columns(pl.lit(0).cast(pl.Int64).alias(day))

    # Ordonner et totaliser
    pivot = (
        pivot
        .select("CODE_DR", *DAYS_FR)
        .with_columns(pl.sum_horizontal(DAYS_FR).alias("Total"))
        .sort("Total", descending=True)
    )

    return pivot



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
    weekly = analyze_weekly_codes()
    if weekly.is_empty():
        return [], [], "Aucune donnée"

    cols = [{"id": "CODE_DR", "name": "Code"}] + [
        {"id": d, "name": d} for d in DAYS_FR
    ] + [{"id": "Total", "name": "Total"}]

    return weekly.to_dicts(), cols, f"Dernière mise à jour : {datetime.now():%d/%m/%Y %H:%M}"


@app.callback(
    Output(ID_DOWNLOAD, "data"),
    Input("weekly-export-btn", "n_clicks"),
    State(FILTER_STORE_ACTUAL, "data"),  # 👈 get current filters
    prevent_initial_call=True,
)
def export_to_excel(_, store_actual_data):
    # analyze_weekly_codes fetches its own data internally
    weekly = analyze_weekly_codes()
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

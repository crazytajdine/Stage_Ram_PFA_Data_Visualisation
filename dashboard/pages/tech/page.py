"""
delay_codes_app.py  –  Dash + Polars  •  Darkly theme
"""

import polars as pl
from pathlib import Path
from datetime import datetime, timedelta
from dash import Dash, html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from server_instance import get_app
import excel_manager
import math
from dash import ctx, no_update
from dash.dcc import send_bytes
import io
import xlsxwriter
from components.filter import FILTER_STORE_ACTUAL

app = get_app()
# ------------------------------------------------------------------ #
# 1 ▸  Read & prepare data                                           #
# ------------------------------------------------------------------ #
time_period = excel_manager.COL_NAME_WINDOW_TIME
time_period_max = excel_manager.COL_NAME_WINDOW_TIME_MAX


# ------------------------------------------------------------------ #
# 2 ▸  Helper – aggregate per code                                   #
# ------------------------------------------------------------------ #
def analyze_delay_codes_polars(frame: pl.DataFrame) -> pl.DataFrame:
    """
    Return a Polars frame with:
        CODE_DR | Occurrences | Description | Aéroports | Nb_AP
    """
    if frame.is_empty():
        return pl.DataFrame(
            {
                "CODE_DR": [],
                "Occurrences": [],
                "Description": [],
                "Aéroports": [],
                "Nb_AP": [],
            }
        )

    # First get airport counts per code
    airport_counts = frame.group_by(["CODE_DR", "DEP_AP_SCHED"]).agg(
        pl.len().alias("ap_count")
    )

    agg = (
        frame.group_by("CODE_DR")
        .agg(
            [
                pl.len().alias("Occurrences"),
                pl.col("LIB_CODE_DR").first().alias("Description"),
                pl.col("DEP_AP_SCHED").drop_nulls().alias("AP_list"),
            ]
        )
        .join(
            airport_counts.group_by("CODE_DR").agg(
                [
                    pl.col("DEP_AP_SCHED").alias("airports"),
                    pl.col("ap_count").alias("counts"),
                ]
            ),
            on="CODE_DR",
            how="left",
        )
        .with_columns(
            [
                pl.struct(["airports", "counts"])
                .map_elements(
                    lambda x: ", ".join(
                        [
                            f"{ap} ({cnt})"
                            for ap, cnt in sorted(
                                zip(x["airports"], x["counts"]),
                                key=lambda item: item[1],
                                reverse=True,
                            )
                        ]
                    ),
                    return_dtype=pl.Utf8,
                )
                .alias("Aéroports"),
                pl.col("AP_list").list.n_unique().alias("Nb_AP"),
            ]
        )
        .select(["CODE_DR", "Occurrences", "Description", "Aéroports", "Nb_AP"])
        .sort("Occurrences", descending=True)
    )
    return agg


def analyze_delay_codes_for_table(frame: pl.DataFrame) -> pl.DataFrame:
    """
    Return delay codes analysis for table (independent of code selection)
    Only filtered by flotte, dates, and matricule
    """
    if frame.is_empty():
        return pl.DataFrame(
            {
                "CODE_DR": [],
                "Occurrences": [],
                "Aéroports": [],
                "Nb_AP": [],
            }
        )

    # First get airport counts per code
    airport_counts = frame.group_by(["CODE_DR", "DEP_AP_SCHED"]).agg(
        pl.len().alias("ap_count")
    )

    agg = (
        frame.group_by("CODE_DR")
        .agg(
            [
                pl.len().alias("Occurrences"),
                pl.col("LIB_CODE_DR").first().alias("Description"),
                pl.col("DEP_AP_SCHED").drop_nulls().alias("AP_list"),
            ]
        )
        .join(
            airport_counts.group_by("CODE_DR").agg(
                [
                    pl.col("DEP_AP_SCHED").alias("airports"),
                    pl.col("ap_count").alias("counts"),
                ]
            ),
            on="CODE_DR",
            how="left",
        )
        .with_columns(
            [
                pl.struct(["airports", "counts"])
                .map_elements(
                    lambda x: ", ".join(
                        [
                            f"{ap} ({cnt})"
                            for ap, cnt in sorted(
                                zip(x["airports"], x["counts"]),
                                key=lambda item: item[1],
                                reverse=True,
                            )
                        ]
                    ),
                    return_dtype=pl.Utf8,
                )
                .alias("Aéroports"),
                pl.col("AP_list").list.n_unique().alias("Nb_AP"),
            ]
        )
        .select(["CODE_DR", "Description", "Occurrences", "Aéroports", "Nb_AP"])
        .sort("Occurrences", descending=True)
    )
    return agg


# ---------- 2. Helper ----------
def compute_options(start: str | None, end: str | None) -> list[int]:
    """
    Return every integer d (≥1) that divides D, where
    D = whole-day distance between start and end dates.
    When dates are invalid or D ≤ 0, return [].
    """
    if not start or not end:
        return []
    try:
        d0 = datetime.fromisoformat(start[:10])  # strip time portion if present
        d1 = datetime.fromisoformat(end[:10])
    except ValueError:
        return []

    D = (d1 - d0).days + 1  # inclusive: end date minus start date plus 1
    if D <= 0:
        return []

    return [d for d in range(1, D + 1)]


"""
It adds a new column to your table that tells you which time period each row belongs to,
    based on the date and how you chose to segment the total duration.

---------------I am talking about the following function---------------

"""


def build_filename(base: str, filters: dict[str, str | None]) -> str:
    """
    Construit un nom de fichier intelligent basé sur les filtres.
    """
    start = filters.get("dt_start") or "ALL"
    end = filters.get("dt_end") or "ALL"
    seg = filters.get("fl_segmentation") or "ALL"
    flotte = filters.get("fl_subtype") or "ALL"
    matricule = filters.get("fl_matricule") or "ALL"

    if isinstance(seg, str) and seg.endswith("d"):
        seg = seg.replace("d", "j")

    parts = [base]

    if start != "ALL" and end != "ALL":
        parts.append(f"{start.replace('_', '/')}_to_{end.replace('_', '/')}")
    else:
        parts.append("ALL_DATES")

    parts.append(f"seg{seg}" if seg != "ALL" else "ALL_SEG")
    parts.append(f"flotte{flotte}" if flotte != "ALL" else "ALL_FLOTTE")
    parts.append(f"matricule{matricule}" if matricule != "ALL" else "ALL_MATRICULE")

    return "_".join(parts) + ".xlsx"


# ------------------------------------------------------------------ #
# 3 ▸  Layout factory                                                #
# ------------------------------------------------------------------ #
def make_layout() -> html.Div:
    # ----- FILTERS + STATS -----------------------------------------
    stats_block = html.Div(
        [
            # ── stats ───────────────────────────────────────────────
            html.H3("Statistiques", className="h4"),
            dbc.Card(html.Div(id="stats-div", className="p-3"), className="mb-4"),
        ]
    )

    # ----- CHART GRID ----------------------------------------------
    charts_block = html.Div(
        id="charts-container",
        children=[],
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(2, 1fr)",
            "gap": "16px",
            "alignItems": "start",
        },
    )

    # ----- TABLE (placed last) -------------------------------------
    table_block = html.Div(
        [
            html.H3("Détail des codes de retard", className="h4 mt-4"),
            dcc.Download(id="download-table"),
            dbc.Button("📥 Exporter Excel", id="export-btn", className="mt-2"),
            html.Div(id="table-container"),
        ]
    )

    # ----- PAGE ----------------------------------------------------
    return dbc.Container(
        fluid=True,
        className="px-4",
        children=[
            stats_block,
            charts_block,
            table_block,
            html.Hr(style={"height": 1, "background": "#202736", "border": 0}),
            html.P(
                f"Dernière mise à jour : {datetime.now():%d/%m/%Y %H:%M}",
                className="text-center text-muted small",
            ),
        ],
    )


# ------------------------------------------------------------------ #
# 4 ▸  Dash app & callbacks                                          #
# ------------------------------------------------------------------ #
layout = make_layout()


def build_structured_table(df: pl.DataFrame, segmentation: str | None) -> pl.DataFrame:
    if df.is_empty():
        return pl.DataFrame(
            {
                time_period_max: [],
                "Famille": [],
                "Code": [],
                "Occurrences": [],
                "Aéroports": [],
                "Nb Aéroports": [],
            }
        )

    airport_counts = df.group_by(
        [time_period_max, "FAMILLE_DR", "CODE_DR", "DEP_AP_SCHED"]
    ).agg(pl.len().alias("ap_count"))

    grouped = (
        df.group_by([time_period_max, "FAMILLE_DR", "CODE_DR"])
        .agg(
            [
                pl.len().alias("Occurrences"),
                pl.col("DEP_AP_SCHED").drop_nulls().alias("AP_list"),
            ]
        )
        .join(
            airport_counts.group_by([time_period_max, "FAMILLE_DR", "CODE_DR"]).agg(
                [
                    pl.col("DEP_AP_SCHED").alias("airports"),
                    pl.col("ap_count").alias("counts"),
                ]
            ),
            on=[time_period_max, "FAMILLE_DR", "CODE_DR"],
            how="left",
        )
        .with_columns(
            [
                pl.struct(["airports", "counts"])
                .map_elements(
                    lambda x: ", ".join(
                        f"{ap} ({cnt})"
                        for ap, cnt in sorted(
                            zip(x["airports"], x["counts"]),
                            key=lambda i: i[1],
                            reverse=True,
                        )
                    ),
                    return_dtype=pl.Utf8,
                )
                .alias("Aéroports"),
                pl.col("AP_list").list.n_unique().alias("Nb Aéroports"),
            ]
        )
        .select(
            [
                time_period_max,
                "FAMILLE_DR",
                "CODE_DR",
                "Occurrences",
                "Aéroports",
                "Nb Aéroports",
            ]
        )
        .rename({"CODE_DR": "Code", "FAMILLE_DR": "Famille"})  # ✅ ICI
        .sort(
            [time_period_max, "Famille", "Occurrences"], descending=[False, False, True]
        )
    )
    return grouped


plot_config = {
    # everything else you already put in config …
    "toImageButtonOptions": {
        "format": "png",  # or "svg" / "pdf" for vector
        "filename": "codes-chart",
        "width": 1600,  # px  (≈ A4 landscape)
        "height": 900,  # px
        "scale": 3,  # 3× pixel-density → crisp on Retina
    }
}


# --- Outputs -------------------------------------------------------
@app.callback(
    [
        Output("stats-div", "children"),
        Output("charts-container", "children"),
        Output("table-container", "children"),
        Output("download-table", "data"),
    ],
    Input("export-btn", "n_clicks"),
    excel_manager.add_watcher_for_data(),  # watch for data changes
    State(FILTER_STORE_ACTUAL, "data"),  # récupère segmentation + dates
    prevent_initial_call=False,
)
def build_outputs(n_clicks, _, filters):
    """Build all output components based on filtered data"""

    df = excel_manager.get_df().collect()
    filters = filters or {}
    segmentation = filters.get("fl_segmentation")
    start = filters.get("dt_start", "")
    end = filters.get("dt_end", "")

    # Get analysis
    summary = analyze_delay_codes_polars(df)

    # 1. Build stats
    unique_codes = summary.height if not summary.is_empty() else 0
    total_delays = summary["Occurrences"].sum() if not summary.is_empty() else 0

    stats = dbc.Row(
        [
            dbc.Col(
                [
                    html.H5("Codes uniques", className="text-muted"),
                    html.H3(f"{unique_codes}", className="text-success mb-0"),
                ],
                md=6,
            ),
            dbc.Col(
                [
                    html.H5("Total retards", className="text-muted"),
                    html.H3(f"{total_delays}", className="text-warning mb-0"),
                ],
                md=6,
            ),
        ]
    )
    # 2. Build temporal bar chart

    # ---------- COMMON PERIOD TOTALS (used by every family chart) -------
    # 2️⃣ exact counts per (period, family, code)
    temporal_all = df.group_by([time_period_max, "FAMILLE_DR", "CODE_DR"]).agg(
        pl.len().alias("count")
    )

    # 3️⃣ grand-total per period (all families, all codes)
    period_totals = temporal_all.group_by(time_period_max).agg(
        pl.col("count").sum().alias("period_total")
    )

    # 4️⃣ join + exact share
    temporal_all = temporal_all.join(period_totals, on=time_period_max).with_columns(
        (pl.col("count") / pl.col("period_total") * 100).alias("perc")
    )

    selected_codes = (
        df["CODE_DR"].unique().sort().to_list() if not df.is_empty() else []
    )
    all_periods = df.get_column(time_period_max).unique().sort().to_list()
    if not selected_codes:
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune donnée pour les codes sélectionnés",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="#a0a7b9"),
        )
    else:
        # Group by time period and code
        # ---------- FAMILY-LEVEL CHARTS ------------------------------------
        family_figs = []  # list of Graph components to return

        # consistent colour map across all charts
        all_unique_codes = df["CODE_DR"].unique().sort().to_list()
        palette = px.colors.qualitative.Set3
        color_map = {
            c: palette[i % len(palette)] for i, c in enumerate(all_unique_codes)
        }

        for fam in temporal_all["FAMILLE_DR"].unique().sort():
            fam_data = temporal_all.filter(pl.col("FAMILLE_DR") == fam)

            if fam_data.is_empty():
                continue

            fig = go.Figure()

            for code in fam_data["CODE_DR"].unique().sort():
                rows = fam_data.filter(pl.col("CODE_DR") == code)

                # maps in the exact grid order
                perc_map = {r[time_period_max]: r["perc"] for r in rows.to_dicts()}
                count_map = {r[time_period_max]: r["count"] for r in rows.to_dicts()}

                y_vals = [perc_map.get(p, 0) for p in all_periods]
                raw_counts = [count_map.get(p, 0) for p in all_periods]

                fig.add_trace(
                    go.Bar(
                        x=all_periods,
                        y=y_vals,
                        name=code,
                        marker_color=color_map.get(code, "#cccccc"),
                        customdata=list(zip(raw_counts, y_vals)),
                        hovertemplate=(
                            "<b>%{meta}</b><br>"
                            "Période : %{x}<br>"
                            "Occur. : %{customdata[0]}<br>"
                            "Pourc. : %{customdata[1]:.2f}%<extra></extra>"
                        ),
                        meta=code,
                        text=[
                            f"{v:.2f} %" if v else "" for v in y_vals
                        ],  # optional labels
                        textposition="outside",
                        cliponaxis=False,
                    )
                )

            HEADER_H = 36  # grey bar height (px) – keep padding inside this
            FIG_H = 420  # visible Plotly canvas height
            WRAP_H = HEADER_H + FIG_H
            # build the bar­chart …
            fig.update_layout(
                yaxis=dict(
                    range=[0, 100],
                    tickformat=".0f",
                    dtick=10,
                    title="Pourcentage (%)",
                ),
                bargap=0.2,
                height=FIG_H,
                margin=dict(
                    l=40, r=10, t=20, b=70
                ),  # b = 70 leaves room for “outside” labels
            )

            # ---- grey-header “card” ------------------------------------------
            family_figs.append(
                html.Div(
                    [
                        # header bar
                        html.Div(
                            f"Famille : {fam}",
                            style={
                                "background": "#6c757d",
                                "color": "#fff",
                                "height": f"{HEADER_H}px",
                                "display": "flex",
                                "alignItems": "center",
                                "paddingLeft": "12px",
                                "fontWeight": 600,
                                "borderTopLeftRadius": "6px",
                                "borderTopRightRadius": "6px",
                            },
                        ),
                        # graph
                        dcc.Graph(id="codes-chart", figure=fig, config=plot_config),
                    ],
                    style={
                        "border": "1px solid #dee2e6",
                        "borderRadius": "6px",
                        "overflow": "hidden",
                        "overflow": "visible",
                        "background": "#ffffff",
                    },
                )
            )

    # 3. Build table (independent of code and segmentation selection)
    # --- Table structurée ---
    segmentation = filters.get("fl_segmentation") if filters else None

    # Prépare le DataFrame date-typed
    if not df.is_empty() and excel_manager.COL_NAME_DEPARTURE_DATETIME in df.columns:
        if df.get_column(excel_manager.COL_NAME_DEPARTURE_DATETIME).dtype == pl.Utf8:
            df = df.with_columns(
                pl.col(excel_manager.COL_NAME_DEPARTURE_DATETIME).str.strptime(
                    pl.Date, "%Y-%m-%d", strict=False
                )
            )

    summary_table = build_structured_table(df, segmentation)

    data = summary_table.to_dicts()
    last_date = None
    last_family = None
    for row in data:
        if row[time_period_max] == last_date:
            row[time_period_max] = ""
        else:
            last_date = row[time_period_max]

        if row["Famille"] == last_family and not row[time_period_max]:
            row["Famille"] = ""
        else:
            last_family = row["Famille"]

    if summary_table.is_empty():
        table = dbc.Alert(
            "Aucun code de retard trouvé dans la sélection",
            color="warning",
            className="text-center",
        )
    else:

        table = dash_table.DataTable(
            id="codes-table",
            data=data,
            columns=[{"name": c, "id": c} for c in summary_table.columns],
            style_header={
                "backgroundColor": "#f8f9fa",
                "color": "#495057",
                "fontWeight": "bold",
                "border": "1px solid #dee2e6",
                "fontSize": "12px",
            },
            style_cell={
                "backgroundColor": "white",
                "color": "#495057",
                "border": "1px solid #dee2e6",
                "textAlign": "left",
                "padding": "8px",
                "fontSize": "11px",
                "whiteSpace": "normal",
                "height": "auto",
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"},
                {
                    "if": {"column_id": "Aéroports"},
                    "textAlign": "left",
                    "whiteSpace": "normal",
                    "height": "auto",
                    "minWidth": "200px",
                },
            ],
            sort_action="native",
            filter_action="native",
            page_size=8,  # include hidden cols if you like
            style_table={"height": "500px", "overflowY": "auto"},
        )

    # --- Export Excel ---
    triggered = ctx.triggered_id
    if triggered == "export-btn" and not summary_table.is_empty():
        buffer = io.BytesIO()
        with xlsxwriter.Workbook(buffer, {"in_memory": True}) as wb:
            ws = wb.add_worksheet()
            for i, col in enumerate(summary_table.columns):
                ws.write(0, i, col)
            for r, row in enumerate(summary_table.iter_rows(), start=1):
                for c, val in enumerate(row):
                    ws.write(r, c, val)
        buffer.seek(0)
        fname = build_filename("retards_export", filters)
        return (
            stats,
            family_figs,
            table,
            send_bytes(lambda s: s.write(buffer.getvalue()), filename=fname),
        )

    return stats, family_figs, table, no_update

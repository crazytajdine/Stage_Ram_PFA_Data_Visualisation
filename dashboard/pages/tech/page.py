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
from dashboard.utils_dashboard.utils_download import add_export_callbacks
from server_instance import get_app
import excel_manager
import math
from dash import ctx, no_update
import io
from components.filter import FILTER_STORE_ACTUAL
from dashboard.utils_dashboard.utils_graph import create_bar_figure, create_bar_horizontal_figure, create_graph_bar_card

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
                "DELAY_CODE": [],
                "Occurrences": [],
                "Description": [],
                "Aéroports": [],
                "Nb_AP": [],
            }
        )

    # First get airport counts per code
    airport_counts = frame.group_by(["DELAY_CODE", "DEP_AP_SCHED"]).agg(
        pl.len().alias("ap_count")
    )

    agg = (
        frame.group_by("DELAY_CODE")
        .agg(
            [
                pl.len().alias("Occurrences"),
                pl.col("LIB_CODE_DR").first().alias("Description"),
                pl.col("DEP_AP_SCHED").drop_nulls().alias("AP_list"),
            ]
        )
        .join(
            airport_counts.group_by("DELAY_CODE").agg(
                [
                    pl.col("DEP_AP_SCHED").alias("airports"),
                    pl.col("ap_count").alias("counts"),
                ]
            ),
            on="DELAY_CODE",
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
        .select(["DELAY_CODE", "Occurrences", "Description", "Aéroports", "Nb_AP"])
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
                "DELAY_CODE": [],
                "Occurrences": [],
                "Aéroports": [],
                "Nb_AP": [],
            }
        )

    # First get airport counts per code
    airport_counts = frame.group_by(["DELAY_CODE", "DEP_AP_SCHED"]).agg(
        pl.len().alias("ap_count")
    )

    agg = (
        frame.group_by("DELAY_CODE")
        .agg(
            [
                pl.len().alias("Occurrences"),
                pl.col("LIB_CODE_DR").first().alias("Description"),
                pl.col("DEP_AP_SCHED").drop_nulls().alias("AP_list"),
            ]
        )
        .join(
            airport_counts.group_by("DELAY_CODE").agg(
                [
                    pl.col("DEP_AP_SCHED").alias("airports"),
                    pl.col("ap_count").alias("counts"),
                ]
            ),
            on="DELAY_CODE",
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
        .select(["DELAY_CODE", "Description", "Occurrences", "Aéroports", "Nb_AP"])
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
        "gridTemplateColumns": "1fr",   # ← au lieu de repeat(2, 1fr)
        "gap": "16px",
        "alignItems": "start",
    },
)

    # ----- TABLE (placed last) -------------------------------------
    table_block = html.Div(
        [
            html.H3("Détail des codes de retard", className="h4 mt-4"),
            dcc.Download(id="download-table"),
            dbc.Button("Exporter Excel", id="export-btn", className="mt-2"),
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


def build_structured_table(df: pl.DataFrame) -> pl.DataFrame:
    if df.is_empty():
        return pl.DataFrame(
            {
                time_period: [],
                "Famille": [],
                "Code": [],
                "Occurrences": [],
                "Aéroports": [],
                "Nb Aéroports": [],
            }
        )

    airport_counts = df.group_by(
        [time_period, "FAMILLE_DR", "DELAY_CODE", "DEP_AP_SCHED"]
    ).agg(pl.len().alias("ap_count"))

    grouped = (
        df.group_by([time_period, "FAMILLE_DR", "DELAY_CODE"])
        .agg(
            [
                pl.len().alias("Occurrences"),
                pl.col("DEP_AP_SCHED").drop_nulls().alias("AP_list"),
            ]
        )
        .join(
            airport_counts.group_by([time_period, "FAMILLE_DR", "DELAY_CODE"]).agg(
                [
                    pl.col("DEP_AP_SCHED").alias("airports"),
                    pl.col("ap_count").alias("counts"),
                ]
            ),
            on=[time_period, "FAMILLE_DR", "DELAY_CODE"],
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
                time_period,
                "FAMILLE_DR",
                "DELAY_CODE",
                "Occurrences",
                "Aéroports",
                "Nb Aéroports",
            ]
        )
        .rename({"DELAY_CODE": "Code", "FAMILLE_DR": "Famille"})  # ✅ ICI
        .sort([time_period, "Famille", "Occurrences"], descending=[False, False, True])
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
    ],
    excel_manager.add_watcher_for_data(),  # watch for data changes
    prevent_initial_call=False,
)
def build_outputs(n_clicks):
    """Build all output components based on filtered data"""

    df = excel_manager.get_df().collect()

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
    temporal_all = df.group_by([time_period, "FAMILLE_DR", "DELAY_CODE"]).agg(
        pl.len().alias("count")
    )

    # 3️⃣ grand-total per period (all families, all codes)
    period_totals = temporal_all.group_by(time_period).agg(
        pl.col("count").sum().alias("period_total")
    )

    # 4️⃣ join + exact share
    temporal_all = temporal_all.join(period_totals, on=time_period).with_columns(
        (pl.col("count") / pl.col("period_total") * 100).alias("perc")
    )
    # (Re-)use temporal_all
    famille_share_df = (
        temporal_all.group_by([time_period, "FAMILLE_DR"])
        .agg(pl.col("count").sum().alias("famille_count"))
        .join(period_totals, on=time_period)
        .with_columns(
            (pl.col("famille_count") / pl.col("period_total") * 100).alias("percentage")
        )
    )


    # Group by time period and code
    # ---------- FAMILY-LEVEL CHARTS ------------------------------------
    family_figs = []  # list of Graph components to return

    # consistent colour map across all charts
    all_unique_codes = df["DELAY_CODE"].unique().sort().to_list()
    palette = px.colors.qualitative.Set3
    color_map = {
        c: palette[i % len(palette)] for i, c in enumerate(all_unique_codes)
    }

 # ------------------------------------------------------------------
    # Construire les onglets (une Tab par famille)
    tab_children = []

    for fam in temporal_all["FAMILLE_DR"].unique().sort():
        fam_data = temporal_all.filter(pl.col("FAMILLE_DR") == fam)

        dts = (
            fam_data.group_by(time_period, "DELAY_CODE")
                    .agg(
                        pl.col("count").sum().alias("all_counts"),
                        pl.col("perc").sum().alias("y_vals"),
                    )
                    .with_columns(pl.col("DELAY_CODE").cast(pl.Utf8))
        )

        fig = create_bar_figure(
            df=dts,
            x=time_period,
            y="y_vals",
            title=fam,
            unit="%",
            color="DELAY_CODE",
            barmode="group",
            legend_title=fam,
        )

        # ➜ un onglet ; inutile de mettre un id sur le Graph
        tab_children.append(
            dcc.Tab(
                label=fam,          # texte de l’onglet
                value=fam,          # valeur (pour l’état actif)
                children=[
                    dcc.Graph(figure=fig, config=plot_config, style={"height": 450})
                ],
                
            )
        )

    # composant Tabs complet
    family_tabs = dcc.Tabs(
        id="family-tabs",
        value=tab_children[0].value if tab_children else None,  # premier actif
        children=tab_children,
        persistence=True,
        colors={
            "background": "#ffffff",
            "primary": "#0d6efd",
            "border": "#dee2e6",
        },
        style={                         # ← ajoutez ceci
        "width": "100%",            # occupe toute la colonne
        "display": "flex",          # les onglets se comportent comme flex-items
        "justifyContent": "center", # centrés horizontalement
        },
    )


    # 3. Build table (independent of code and segmentation selection)
    # --- Table structurée ---

    # Prépare le DataFrame date-typed
    if not df.is_empty() and excel_manager.COL_NAME_DEPARTURE_DATETIME in df.columns:
        if df.get_column(excel_manager.COL_NAME_DEPARTURE_DATETIME).dtype == pl.Utf8:
            df = df.with_columns(
                pl.col(excel_manager.COL_NAME_DEPARTURE_DATETIME).str.strptime(
                    pl.Date, "%Y-%m-%d", strict=False
                )
            )

    summary_table = build_structured_table(df)

    data = summary_table.to_dicts()
    last_date = None
    last_family = None
    for row in data:
        if row[time_period] == last_date:
            row[time_period] = ""
        else:
            last_date = row[time_period]

        if row["Famille"] == last_family and not row[time_period]:
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

    for famille in famille_share_df["FAMILLE_DR"].unique().sort():
        fig_familles = create_bar_horizontal_figure(
            df=famille_share_df,
            x="percentage",
            y=time_period,
            title=f"{famille}",
            unit="%",
            color="FAMILLE_DR",
            barmode="stack",
        )
    # --- juste après avoir construit fig_familles ---------------------
    # ▸ juste après avoir créé fig_familles  ⬇️
    big_chart = html.Div(
        dcc.Graph(
            figure=fig_familles,
            config=plot_config,
            style={"width": "100%"},  # occupe 100 % de la div
        ),
        # ↓ la clé : span de la colonne 1 jusqu’à la dernière (‑1)
        style={"gridColumn": "1 / -1"},  # ou "1 / span 2" si tu préfères
    )

    charts_out = [
    big_chart,     # graphique global (déjà défini plus haut)
    family_tabs,   # barre d’onglets avec un seul graph visible
]

    return stats, charts_out, table


add_export_callbacks(
    id_table="codes-table",
    id_button="export-btn",
    name="codes-retard",
)

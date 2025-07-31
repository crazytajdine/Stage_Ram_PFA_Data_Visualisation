from dash import (
    html,
    dcc,
    Input,
    Output,
    State,
    dash_table,
    callback_context,
    no_update,
)
from dash.dcc import send_bytes
import polars as pl
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import plotly.graph_objs as go
import math
import xlsxwriter
from io import BytesIO
import time

from server_instance import get_app
from excel_manager import (
    get_df,
    add_watcher_for_data,
    COL_NAME_WINDOW_TIME_MAX,
    COL_NAME_WINDOW_TIME,
    COL_NAME_DEPARTURE_DATETIME,
    COL_NAME_WINDOW_TIME,
    # COL_NAME_TOTAL_COUNT  # only if reused
)

app = get_app()


def convert_minutes_to_hours_minutes(minutes: int) -> str:
    heures = minutes // 60
    mins = minutes % 60
    return f"{heures}h {mins}m"


layout = dbc.Container(
    [
        html.Div(
            children=[
                dbc.Alert(
                    id="summary-info",
                    color="info",
                    is_open=False,
                    className="mb-4",
                    style={
                        "fontWeight": "bold",
                        "fontSize": "1.1rem",
                        "whiteSpace": "pre-line",
                    },
                ),
                dbc.Alert(
                    id="result-message",
                    is_open=False,
                    dismissable=True,
                    className="mt-3",
                ),
                # Premier bouton et tableau + download
                dbc.Button(
                    "📥 Exporter Excel", id="weekly-export-btn", className="mt-2"
                ),
                dcc.Download(id="search-download"),
                dash_table.DataTable(
                    id="result-table",
                    columns=[],
                    data=[],
                    page_size=10,
                    style_table={
                        "overflowX": "auto",
                        "marginTop": "10px",
                        "marginBottom": "40px",
                    },
                    style_cell={"textAlign": "left"},
                    sort_action="native",
                ),
                # Graphique SUBTYPE %
                html.Div(
                    dcc.Graph(
                        id="bar-chart-subtype-pct",
                        style={"margin": "auto", "height": "400px", "width": "90%"},
                    ),
                    style={
                        "display": "flex",
                        "justifyContent": "center",
                        "alignItems": "center",
                        "marginBottom": "40px",
                    },
                ),
                # Deuxième bouton, tableau + download
                html.Div(
                    [
                        dbc.Button(
                            "📥 Exporter Excel subtype",
                            id="subtype-export-btn",
                            className="mb-2",
                        ),
                        dcc.Download(id="subtype-download"),
                        dash_table.DataTable(
                            id="subtype-table",
                            columns=[],
                            data=[],
                            page_size=10,
                            style_table={
                                "overflowX": "auto",
                                "marginTop": "10px",
                                "marginBottom": "40px",
                            },
                            style_cell={"textAlign": "left"},
                            sort_action="native",
                        ),
                    ]
                ),
                html.Div(
                    dcc.Graph(
                        id="bar-chart-pct",
                        style={"margin": "auto", "height": "400px", "width": "90%"},
                    ),
                    style={
                        "display": "flex",
                        "justifyContent": "center",
                        "alignItems": "center",
                        "marginBottom": "40px",
                    },
                ),
                html.Div(
                    dcc.Graph(
                        id="bar-chart-interval",
                        style={"margin": "auto", "width": "100%"},
                    ),
                    style={
                        "marginBottom": "15px",
                        "background": "white",
                        "padding": "10px",
                        "borderRadius": "8px",
                    },
                ),
                html.Div(
    [
        dbc.Button("📥 Exporter Excel intervalles", id="interval-export-btn", className="mb-2"),
        dcc.Download(id="interval-download"),
        dash_table.DataTable(
            id="interval-table",
            columns=[],
            data=[],
            page_size=10,
            style_table={"overflowX": "auto", "margin-top": "10px", "margin-bottom": "40px"},
            style_cell={"textAlign": "left"},
            sort_action="native",
        ),
    ],
    style={"margin-bottom": "40px"},
)

            ],
            className="mx-3",
        ),
    ],
    fluid=True,
)

from dash import no_update
import plotly.graph_objects as go
import polars as pl
from datetime import datetime, timedelta
import math
import dash_bootstrap_components as dbc


def convert_minutes_to_hours_minutes(minutes: int | float) -> str:
    m = int(minutes or 0)
    h, r = divmod(m, 60)
    return f"{h}h{r:02d}"


def _get_df_collected():
    df_lazy = get_df()
    if df_lazy is None:
        return None
    return df_lazy.collect()


def _filter_and_prepare(df: pl.DataFrame) -> tuple[pl.DataFrame, str]:
    if df.is_empty():
        return df, "Aucun résultat."
    df = df.sort("Retard en min", descending=True)
    nb_retard_15 = df.filter(pl.col("Retard en min") >= 15).height
    df_max = df.filter(pl.col("Retard en min") > 0).limit(1)
    if df_max.height > 0:
        row = df_max[0]
        subtype = row["AC_SUBTYPE"]
        subtype = subtype.item() if hasattr(subtype, "item") else subtype
        registration = row["AC_REGISTRATION"]
        registration = (
            registration.item() if hasattr(registration, "item") else registration
        )
        retard_min = row["Retard en min"]
        retard_min = retard_min.item() if hasattr(retard_min, "item") else retard_min
        retard_hm = convert_minutes_to_hours_minutes(retard_min)
        vol_info = (
            f"\nVol avec le plus grand retard : {subtype} {registration}, "
            f"durée du retard : {retard_hm} ({retard_min} min)\n"
        )
    else:
        vol_info = "\nAucun vol avec retard supérieur à 0 min."
    summary_text = f"Nombre de vols avec retard ≥ 15 min : {nb_retard_15}{vol_info}"
    return df, summary_text


def _build_table(df: pl.DataFrame) -> tuple[list[dict], list[dict]]:
    if df.is_empty():
        return [], []
    df_display = df.select(
        [
            "AC_SUBTYPE",
            "AC_REGISTRATION",
            "DEP_DAY_SCHED",
            "Retard en min",
            "CODE_DR",
        ]
    ).rename(
        {
            "AC_SUBTYPE": "SUBTYPE",
            "AC_REGISTRATION": "REGISTRATION",
            "DEP_DAY_SCHED": "DATETIME",
            "CODE_DR": "CODE RETARD",
            "Retard en min": "RETARD (min)",
        }
    )
    columns = [{"name": c, "id": c} for c in df_display.columns]
    data = df_display.to_dicts()
    return columns, data


def _build_pct_figure(df: pl.DataFrame) -> go.Figure:
    if df.is_empty():
        return go.Figure()
    total = df.height
    if total == 0:
        return go.Figure()
    count_15_plus = df.filter(pl.col("Retard en min") >= 15).height
    count_15_moins = total - count_15_plus
    pct_15_plus = (count_15_plus / total) * 100
    pct_15_moins = 100 - pct_15_plus
    fig = go.Figure(
        data=[
            go.Bar(
                x=["Retard < 15 min", "Retard ≥ 15 min"],
                y=[pct_15_moins, pct_15_plus],
            )
        ]
    )
    fig.update_layout(
        title="Pourcentage des vols par catégorie de retard",
        yaxis_title="Pourcentage (%)",
        xaxis_title="Catégorie",
        yaxis=dict(range=[0, 100]),
    )
    return fig


def _build_subtype_pct_figure(df: pl.DataFrame) -> go.Figure:
    if df.is_empty():
        return go.Figure()
    df_retard = df.filter(pl.col("Retard en min") > 0)
    if df_retard.is_empty():
        return go.Figure()
    total = df_retard.height
    counts = (
        df_retard.group_by("AC_SUBTYPE")
        .agg(pl.count().alias("count"))
        .sort("count", descending=True)
    )
    counts = counts.with_columns((pl.col("count") * 100 / total).alias("pct"))
    subtypes = counts["AC_SUBTYPE"].to_list()
    pcts = counts["pct"].to_list()
    counts_vals = counts["count"].to_list()
    text_labels = [f"{cnt} vols - {pct:.1f}%" for cnt, pct in zip(counts_vals, pcts)]
    fig = go.Figure(
        data=[
            go.Bar(
                x=pcts,
                y=subtypes,
                orientation="h",
                text=text_labels,
                textposition="outside",
                hovertemplate="%{y}<br>%{text}<extra></extra>",
            )
        ]
    )
    height = min(max(400, 30 * len(subtypes) + 100), 1200)
    fig.update_layout(
        title="Répartition des vols en retard par SUBTYPE (%)",
        xaxis_title="Pourcentage (%)",
        yaxis_title="SUBTYPE",
        yaxis=dict(autorange="reversed"),
        height=height,
        margin=dict(l=180, r=60, t=60, b=60),
        xaxis=dict(range=[0, 105]),
        plot_bgcolor="#fff",
        bargap=0.25,
    )
    return fig


def build_subtype_table_data(df: pl.DataFrame):
    if df.is_empty():
        return [], []
    df_retard = df.filter(pl.col("Retard en min") > 0)
    if df_retard.is_empty():
        return [], []
    total = df_retard.height
    counts = (
        df_retard.group_by("AC_SUBTYPE")
        .agg(pl.count().alias("count"))
        .sort("count", descending=True)
    )
    counts = counts.with_columns((pl.col("count") * 100 / total).alias("pct"))
    counts_display = counts.rename(
        {"AC_SUBTYPE": "SUBTYPE", "count": "NOMBRE", "pct": "POURCENTAGE (%)"}
    )
    columns = [{"name": c, "id": c} for c in counts_display.columns]
    data = counts_display.to_dicts()
    return columns, data


PERIOD_START = COL_NAME_WINDOW_TIME_MAX  # start of window
PERIOD_END = COL_NAME_WINDOW_TIME  # end of window


def build_period_chart(df: pl.DataFrame) -> go.Figure:
    if df.is_empty() or PERIOD_START not in df.columns:
        return go.Figure()
    has_end = PERIOD_END in df.columns and PERIOD_END != PERIOD_START
    if has_end:
        df_lab = df.with_columns(
            [
                pl.col(PERIOD_START)
                .cast(pl.Date)
                .dt.strftime("%Y-%m-%d")
                .alias("_start_s"),
                pl.col(PERIOD_END)
                .cast(pl.Date)
                .dt.strftime("%Y-%m-%d")
                .alias("_end_s"),
            ]
        ).with_columns(
            (pl.col("_start_s") + pl.lit(" → ") + pl.col("_end_s")).alias("label"),
        )
        sort_expr = pl.col(PERIOD_START).cast(pl.Date).alias("_sort")
        label_col = "label"
    else:
        if df.schema[PERIOD_START] == pl.Utf8:
            df_lab = df.rename({PERIOD_START: "label"})
            df_lab = df_lab.with_columns(
                pl.col("label")
                .str.slice(0, 10)
                .str.strptime(pl.Date, "%Y-%m-%d", strict=False)
                .alias("_sort")
            )
            label_col = "label"
            sort_expr = pl.col("_sort")
        else:
            df_lab = df.with_columns(
                pl.col(PERIOD_START)
                .cast(pl.Date)
                .dt.strftime("%Y-%m-%d")
                .alias("label"),
                pl.col(PERIOD_START).cast(pl.Date).alias("_sort"),
            )
            label_col = "label"
            sort_expr = pl.col("_sort")
    counts_df = (
        df_lab.group_by([label_col, sort_expr])
        .agg(pl.len().alias("count"))
        .sort("_sort", descending=False)
    )
    total = counts_df["count"].sum()
    if total == 0:
        return go.Figure()
    counts_df = counts_df.with_columns((pl.col("count") * 100 / total).alias("pct"))
    labels = counts_df[label_col].to_list()
    counts = counts_df["count"].to_list()
    pcts = counts_df["pct"].to_list()
    fig = go.Figure(
        data=[
            go.Bar(
                y=labels,
                x=pcts,
                orientation="h",
                text=[f"{c} vols" for c in counts],
                textposition="outside",
                hovertemplate="%{y}<br>%{x:.2f}%<br>%{text}<extra></extra>",
            )
        ]
    )
    n = len(labels)
    height = min(max(400, 30 * n + 100), 1200)
    fig.update_layout(
        title="Répartition des vols par intervalles (en %)",
        yaxis_title="Intervalle de dates",
        xaxis_title="Pourcentage (%)",
        bargap=0.25,
        height=height,
        margin=dict(l=180, r=60, t=60, b=60),
        yaxis=dict(autorange="reversed", automargin=True),
        xaxis=dict(range=[0, 105], automargin=True),
        plot_bgcolor="#fff",
    )
    return fig


# CALLBACKS --


@app.callback(
    Output("subtype-table", "columns"),
    Output("subtype-table", "data"),
    add_watcher_for_data(),
)
def update_subtype_table(_):
    df = get_df()
    if df is None:
        return [], []
    df = df.collect()
    if df.is_empty():
        return [], []
    df, _ = _filter_and_prepare(df)
    columns, data = build_subtype_table_data(df)
    return columns, data


@app.callback(
    Output("summary-info", "children"),
    Output("summary-info", "is_open"),
    Output("result-message", "children"),
    Output("result-message", "color"),
    Output("result-message", "is_open"),
    add_watcher_for_data(),
)
def update_summary(_):
    df = get_df()
    if df is None:
        alert = dbc.Alert(
            "Aucun fichier Excel chargé. Veuillez charger un fichier Excel d'abord.",
            color="danger",
            className="mt-3",
        )
        return "", False, alert, "danger", True

    df = df.collect()
    if df.is_empty():
        alert = dbc.Alert(
            "Aucun résultat trouvé pour les critères spécifiés.",
            color="warning",
            className="mt-3",
        )
        return "", False, alert, "warning", True

    df, summary_text = _filter_and_prepare(df)
    result_msg = dbc.Alert(
        f"{df.height} résultat(s) trouvé(s).", color="success", className="mt-3"
    )
    return summary_text, True, result_msg, "success", True


@app.callback(
    Output("result-table", "columns"),
    Output("result-table", "data"),
    add_watcher_for_data(),
)
def update_table(_):
    df = get_df()
    if df is None:
        return [], []
    df = df.collect()
    if df.is_empty():
        return [], []
    df, _ = _filter_and_prepare(df)
    columns, data = _build_table(df)
    return columns, data


@app.callback(
    Output("bar-chart-pct", "figure"),
    add_watcher_for_data(),
)
def update_pct_chart(_):
    df = get_df()
    if df is None:
        return go.Figure()
    df = df.collect()
    if df.is_empty():
        return go.Figure()
    df, _ = _filter_and_prepare(df)
    return _build_pct_figure(df)


@app.callback(
    Output("bar-chart-interval", "figure"),
    add_watcher_for_data(),
)
def update_period_chart(_):
    df = get_df()
    if df is None:
        return go.Figure()
    df = df.collect()
    if df.is_empty():
        return go.Figure()
    return build_period_chart(df)


@app.callback(
    Output("bar-chart-subtype-pct", "figure"),
    add_watcher_for_data(),
)
def update_subtype_pct_chart(_):
    df = get_df()
    if df is None:
        return go.Figure()
    df = df.collect()
    if df.is_empty():
        return go.Figure()
    df, _ = _filter_and_prepare(df)
    return _build_subtype_pct_figure(df)


# --- Callback téléchargement premier tableau ---
@app.callback(
    Output("search-download", "data"),
    Input("weekly-export-btn", "n_clicks"),
    State("result-table", "data"),
    prevent_initial_call=True,
)
def download_excel(n_clicks, table_data):
    if not n_clicks or not table_data:
        return no_update

    df_to_download = pl.DataFrame(table_data)
    buf = BytesIO()
    workbook = xlsxwriter.Workbook(buf, {"in_memory": True})
    worksheet = workbook.add_worksheet("Vols filtrés")

    for j, col in enumerate(df_to_download.columns):
        worksheet.write(0, j, col)
    for i, row in enumerate(df_to_download.rows(), start=1):
        for j, value in enumerate(row):
            worksheet.write(i, j, value)

    workbook.close()
    buf.seek(0)

    filename = "vols_filtres.xlsx"
    return send_bytes(lambda out_io: out_io.write(buf.getvalue()), filename=filename)


# --- Callback téléchargement deuxième tableau ---
@app.callback(
    Output("subtype-download", "data"),
    Input("subtype-export-btn", "n_clicks"),
    State("subtype-table", "data"),
    prevent_initial_call=True,
)
def download_subtype_excel(n_clicks, table_data):
    if not n_clicks or not table_data:
        return no_update

    df_to_download = pl.DataFrame(table_data)
    buf = BytesIO()
    workbook = xlsxwriter.Workbook(buf, {"in_memory": True})
    worksheet = workbook.add_worksheet("Subtype Vols")

    for j, col in enumerate(df_to_download.columns):
        worksheet.write(0, j, col)
    for i, row in enumerate(df_to_download.rows(), start=1):
        for j, value in enumerate(row):
            worksheet.write(i, j, value)

    workbook.close()
    buf.seek(0)

    filename = "vols_subtype_filtres.xlsx"
    return send_bytes(lambda out_io: out_io.write(buf.getvalue()), filename=filename)
def build_interval_table_data(df: pl.DataFrame) -> tuple[list[dict], list[dict]]:
    if df.is_empty() or PERIOD_START not in df.columns:
        return [], []

    has_end = PERIOD_END in df.columns and PERIOD_END != PERIOD_START
    if has_end:
        df_lab = df.with_columns([
            pl.col(PERIOD_START).cast(pl.Date).alias("WINDOW_DATETIME_DEP"),
            pl.col(PERIOD_END).cast(pl.Date).alias("WINDOW_DATETIME_DEP_MAX"),
        ])
    else:
        df_lab = df.with_columns([
            pl.col(PERIOD_START).cast(pl.Date).alias("WINDOW_DATETIME_DEP"),
            pl.col(PERIOD_START).cast(pl.Date).alias("WINDOW_DATETIME_DEP_MAX"),
        ])

    counts_df = (
        df_lab
        .group_by(["WINDOW_DATETIME_DEP", "WINDOW_DATETIME_DEP_MAX"])
        .agg(pl.count().alias("nbr_de_vol"))
        .sort("WINDOW_DATETIME_DEP", descending=False)
    )

    total = counts_df["nbr_de_vol"].sum()
    if total == 0:
        return [], []

    counts_df = counts_df.with_columns(
        (pl.col("nbr_de_vol") * 100 / total).round(2).alias("pourcentage")
    )

    columns = [
        {"name": "Min_Date", "id": "WINDOW_DATETIME_DEP", "type": "datetime"},
        {"name": "Max_Date", "id": "WINDOW_DATETIME_DEP_MAX", "type": "datetime"},
        {"name": "Nbr_de_vol", "id": "nbr_de_vol", "type": "numeric"},
        {"name": "Pourcentage", "id": "pourcentage", "type": "numeric", "format": {"specifier": ".2f"}},
    ]
    data = counts_df.to_dicts()
    return columns, data
@app.callback(
    Output("interval-table", "columns"),
    Output("interval-table", "data"),
    add_watcher_for_data(),
)
def update_interval_table(_):
    df = get_df()
    if df is None:
        return [], []
    df = df.collect()
    if df.is_empty():
        return [], []
    columns, data = build_interval_table_data(df)
    return columns, data
@app.callback(
    Output("interval-download", "data"),
    Input("interval-export-btn", "n_clicks"),
    State("interval-table", "data"),
    prevent_initial_call=True,
)
def download_interval_excel(n_clicks, table_data):
    if not n_clicks or not table_data:
        return no_update

    df_to_download = pl.DataFrame(table_data)
    buf = BytesIO()
    workbook = xlsxwriter.Workbook(buf, {"in_memory": True})
    worksheet = workbook.add_worksheet("Répartition intervalles")

    for j, col in enumerate(df_to_download.columns):
        worksheet.write(0, j, col)
    for i, row in enumerate(df_to_download.rows(), start=1):
        for j, value in enumerate(row):
            worksheet.write(i, j, value)

    workbook.close()
    buf.seek(0)

    filename = "vols_intervalles.xlsx"
    return send_bytes(lambda out_io: out_io.write(buf.getvalue()), filename=filename)

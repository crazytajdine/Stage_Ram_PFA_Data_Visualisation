import dash
import polars as pl
from dash import html, dcc, dash_table, Output
import dash_bootstrap_components as dbc
from calculations.analytics import (
    COL_NAME_COUNT_DELAY_FAMILY,
    COL_NAME_COUNT_DELAY_PER_CODE_DELAY_PER_FAMILY,
    COL_NAME_PERCENTAGE_DELAY_CODE_PER_FAMILY_PER_PERIOD,
    COL_NAME_PERCENTAGE_DELAY_CODE_PER_FAMILY_PER_PERIOD_TOTAL,
    COL_NAME_PERCENTAGE_FAMILY_PER_PERIOD,
    prepare_delay_data,
)
from utils_dashboard.utils_download import add_export_callbacks
from server_instance import get_app
import data_managers.excel_manager as excel_manager
from utils_dashboard.utils_graph import (
    create_bar_figure,
)

app = get_app()
# ------------------------------------------------------------------ #
# 1 ▸  Read & prepare data                                           #
# ------------------------------------------------------------------ #
time_period = excel_manager.COL_NAME_WINDOW_TIME
time_period_max = excel_manager.COL_NAME_WINDOW_TIME_MAX

TABLE_NAMES_RENAME = {
    time_period: "Time Window",
    time_period_max: "Max Time Window",
    COL_NAME_COUNT_DELAY_FAMILY: "Number of Occurrences",
    COL_NAME_COUNT_DELAY_PER_CODE_DELAY_PER_FAMILY: "Number of Occurrences of Delay Code",
    COL_NAME_PERCENTAGE_FAMILY_PER_PERIOD: "Percentage of Occurrences",
    COL_NAME_PERCENTAGE_DELAY_CODE_PER_FAMILY_PER_PERIOD: "Percentage of Occurrences per family ",
    COL_NAME_PERCENTAGE_DELAY_CODE_PER_FAMILY_PER_PERIOD_TOTAL: "Percentage of Occurrences per family (total)",
    "FAMILLE_DR": "Family",
    "DELAY_CODE": "Delay Code",
}


CODE_DESCRIPTIONS = {
    41: "TECHNICAL DEFECTS",
    42: "SCHEDULED MAINTENANCE",
    43: "NON-SCHEDULED MAINTENANCE",
    44: "SPARES AND MAINTENANCE",
    45: "AOG SPARES",
    46: "AIRCRAFT CHANGE",
    47: "STANDBY AIRCRAFT",
    51: "DAMAGE DURING FLIGHT OPERATIONS",
    52: "DAMAGE DURING GROUND OPERATIONS",
}

STATIC_FAM_CODES = {
    "Technie": list(range(41, 48)),  # 41-47 inclus
    "Avarie": [51, 52],
}


# ----- FILTERS + STATS -----------------------------------------
stats_block = html.Div(
    [
        # ── Stats ───────────────────────────────────────────────
        html.H3("Statistics", className="h4"),
        dbc.Card(html.Div(id="stats-div", className="p-3"), className="mb-4"),
    ]
)

# ----- CHART GRID ----------------------------------------------
charts_block = html.Div(
    id="charts-container",
    children=[],
    style={
        "display": "grid",
        "gridTemplateColumns": "1fr",  # ← au lieu de repeat(2, 1fr)
        "gap": "16px",
        "alignItems": "start",
    },
)

# ----- TABLE (placed last) -------------------------------------
table_block = html.Div(
    [
        html.H3("Delay Code Details", className="h4 mt-4"),
        dbc.Button(
            [html.I(className="bi bi-download me-2"), "Exporter Excel"],
            id="export-btn",
            className="btn-export mt-2",
            n_clicks=0,
        ),
        html.Div(id="table-container"),
    ]
)


family_code_cards = []
for fam, codes in STATIC_FAM_CODES.items():
    code_items = []
    for code in codes:
        code_items.append(
            html.Li(
                [
                    # restore the numeric badge
                    dbc.Badge(
                        str(code),
                        className="me-2",
                        style={
                            "background": "rgba(0,0,0,0.7)",
                            "color": "#fff",
                            "font-size": "0.8rem",
                            "min-width": "2rem",
                            "text-align": "center",
                        },
                    ),
                    html.Span(CODE_DESCRIPTIONS[code]),
                ],
                className="d-flex align-items-center mb-2",
            )
        )

    family_code_cards.append(
        dbc.Card(
            [
                dbc.CardHeader(fam, className="bg-dark text-white"),
                dbc.CardBody(html.Ul(code_items, className="ps-3 mb-0")),
            ],
            className="about-card mb-4",
        )
    )

about_section = html.Div(
    [
        html.H3("About", className="h4 mt-4"),
        dbc.Row(
            [dbc.Col(card, width=6, lg=3) for card in family_code_cards],
            className="g-4",
        ),
    ],
    style={"gridColumn": "1 / -1"},
)


# ------------------------------------------------------------------ #
# 4 ▸  Dash app & callbacks                                          #
# ------------------------------------------------------------------ #
layout = dbc.Container(
    fluid=True,
    className="px-4",
    children=[
        stats_block,
        charts_block,
        table_block,
        # ← insert this:
        html.Div(id="about-container", children=about_section),
    ],
)


plot_config = {
    # everything else you already put in config …
    "toImageButtonOptions": {
        "format": "png",  # or "svg" / "pdf" for vector
        "filename": "codes-chart",
        "width": 1600,  # px  (≈ A4 landscape)
        "height": 600,  # px
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
    excel_manager.add_watcher_for_data(),
    prevent_initial_call=False,
)
def update_plots_tables(n_clicks):
    summary, temporal_all, famille_share_df = prepare_delay_data()
    if temporal_all is None:
        return dash.no_update

    # --- Stats ---
    unique_codes = summary.height if not summary.is_empty() else 0
    total_delays = summary["Occurrences"].sum() if not summary.is_empty() else 0
    stats = dbc.Row(
        [
            dbc.Col(
                [
                    html.H5("Unique codes", className="text-muted"),
                    html.H3(f"{unique_codes}", className="text-success mb-0"),
                ],
                md=6,
            ),
            dbc.Col(
                [
                    html.H5("Total delays", className="text-muted"),
                    html.H3(f"{total_delays}", className="text-warning mb-0"),
                ],
                md=6,
            ),
        ]
    )

    # --- Charts ---
    fig_familles = create_bar_figure(
        df=famille_share_df,
        x=time_period,
        x_max=time_period_max,
        y=COL_NAME_PERCENTAGE_FAMILY_PER_PERIOD,
        title="Percentage of delays by family by segmentation",
        unit="%",
        color="FAMILLE_DR",
        legend_title="Family",
    )
    big_chart = html.Div(
        dcc.Graph(
            figure=fig_familles,
            config=plot_config,
            style={"width": "100%", "height": "600px"},
        ),
        className="graph mb-4 mx-auto",
        style={"width": "90%", "gridColumn": "1 / -1"},
    )
    tab_children = []
    for fam in temporal_all["FAMILLE_DR"].unique():
        fam_data = temporal_all.filter(pl.col("FAMILLE_DR") == fam)
        dts = (
            fam_data.group_by(time_period, "DELAY_CODE")
            .agg(
                pl.col(time_period_max).first().alias(time_period_max),
                pl.col(COL_NAME_COUNT_DELAY_PER_CODE_DELAY_PER_FAMILY)
                .sum()
                .alias("all_counts"),
                pl.col(COL_NAME_PERCENTAGE_DELAY_CODE_PER_FAMILY_PER_PERIOD_TOTAL)
                .sum()
                .alias("y_vals"),
            )
            .with_columns(pl.col("DELAY_CODE").cast(pl.Utf8))
        )
        fig = create_bar_figure(
            df=dts,
            x=time_period,
            x_max=time_period_max,
            y="y_vals",
            unit="%",
            title=f"{fam} Delay codes distribution over time",
            color="DELAY_CODE",
            barmode="group",
            legend_title=fam,
        )
        tab_children.append(
            dcc.Tab(
                label=fam,
                value=fam,
                children=[
                    dcc.Graph(
                        figure=fig,
                        config=plot_config,
                        style={
                            "backgroundColor": "white",
                            "boxShadow": "0px 4px 6px rgba(0, 0, 0, 0.1)",
                            "borderBottomLeftRadius": "12px",
                            "borderBottomRightRadius": "12px",
                            "padding": "10px",
                            "border": "1px solid #d6d6d6",
                            "borderTop": "none",
                        },
                    )
                ],
                selected_style={
                    "borderTop": "3px solid var(--ram-red)",
                },
            )
        )

    family_tabs = dcc.Tabs(
        id="family-tabs",
        value=tab_children[0].value if tab_children else None,
        children=tab_children,
        persistence=True,
    )

    # --- Table ---
    summary_table = temporal_all.select(
        [
            time_period,
            time_period_max,
            "FAMILLE_DR",
            "DELAY_CODE",
            COL_NAME_COUNT_DELAY_PER_CODE_DELAY_PER_FAMILY,
            COL_NAME_PERCENTAGE_DELAY_CODE_PER_FAMILY_PER_PERIOD,
            COL_NAME_PERCENTAGE_DELAY_CODE_PER_FAMILY_PER_PERIOD_TOTAL,
        ]
    )
    if summary_table.is_empty():
        table = dbc.Alert(
            "Aucun code de retard trouvé dans la sélection",
            color="warning",
            className="text-center",
        )
    else:
        table = dash_table.DataTable(
            id="codes-table",
            data=summary_table.to_dicts(),
            columns=[
                {"name": TABLE_NAMES_RENAME.get(c, c), "id": c}
                for c in summary_table.columns
            ],
            style_cell={"textAlign": "left"},
            sort_action="native",
            page_size=15,
            style_table={"overflowX": "auto"},
        )

    return stats, [big_chart, family_tabs], table


add_export_callbacks(
    id_table="codes-table",
    id_button="export-btn",
    name="codes-retard",
)
add_export_callbacks(
    id_table="family-summary-table",
    id_button="export-family-btn",
    name="family-summary",
)

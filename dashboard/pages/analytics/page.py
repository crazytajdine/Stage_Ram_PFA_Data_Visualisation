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
    COL_NAME_PERCENTAGE_SUBTYPE_FAMILY,
    COL_NAME_PERCENTAGE_REGISTRATION_FAMILY,
    analyze_summery,
    prepare_delay_data,
    prepare_registration_family_data,
    prepare_subtype_family_data,
)
from data_managers.excel_manager import (
    COL_NAME_WINDOW_TIME,
    COL_NAME_WINDOW_TIME_MAX,
    add_watcher_for_data,
)
from utils_dashboard.utils_download import add_export_callbacks
from server_instance import get_app
from utils_dashboard.utils_graph import (
    create_bar_figure,
    create_navbar,
    register_navbar_callback,
)

app = get_app()
# ------------------------------------------------------------------ #
# 1 ▸  Read & prepare data                                           #
# ------------------------------------------------------------------ #

ID_STATS_DIV = "stats-div"
ID_CHARTS_CONTAINER = "charts-container"
ID_TABLE_CONTAINER = "table-container"
ID_CHARTS_CONTAINER_SUBTYPE = "charts-container-subtype"
ID_TABLE_CONTAINER_SUBTYPE = "table-container-subtype"
ID_CHARTS_CONTAINER_REGISTRATION = "charts-container-registration"
ID_TABLE_CONTAINER_REGISTRATION = "table-container-registration"

ID_TABLE_SUMMARY = "table-summary"
ID_TABLE_SUBTYPE = "table-subtype"
ID_TABLE_REGISTRATION = "table-registration"
ID_TABLE_DELAY_CODE = "table-delay-code"


ID_NAVBAR_FAMILY = "navbar-family"
ID_NAVBAR_SUBTYPE = "navbar-subtype"
ID_NAVBAR_REGISTRATION = "navbar-registration"


TABLE_NAMES_RENAME = {
    COL_NAME_WINDOW_TIME: "Time Window",
    COL_NAME_WINDOW_TIME_MAX: "Max Time Window",
    COL_NAME_COUNT_DELAY_FAMILY: "Number of Occurrences",
    COL_NAME_COUNT_DELAY_PER_CODE_DELAY_PER_FAMILY: "Number of Occurrences of Delay Code",
    COL_NAME_PERCENTAGE_FAMILY_PER_PERIOD: "Percentage of Occurrences",
    COL_NAME_PERCENTAGE_DELAY_CODE_PER_FAMILY_PER_PERIOD: "Percentage of Occurrences per family ",
    COL_NAME_PERCENTAGE_DELAY_CODE_PER_FAMILY_PER_PERIOD_TOTAL: "Percentage of Occurrences per family (total)",
    COL_NAME_PERCENTAGE_SUBTYPE_FAMILY: "Percentage of Occurrences per subtype",
    COL_NAME_PERCENTAGE_REGISTRATION_FAMILY: "Percentage per Registration",
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
    "Technique": list(range(41, 48)),  # 41-47 inclus
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
    style={
        "display": "grid",
        "gridTemplateColumns": "1fr",  # ← au lieu de repeat(2, 1fr)
        "gap": "16px",
        "alignItems": "start",
    },
)
charts_block_subtype = html.Div(
    id="charts-container-subtype",
    style={
        "display": "grid",
        "gridTemplateColumns": "1fr",  # ← au lieu de repeat(2, 1fr)
        "gap": "16px",
        "alignItems": "start",
    },
    className="mt-2",
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
table_block_subtype = html.Div(
    [
        html.H3("Details by Subtype", className="h4 mt-4"),
        dbc.Button(
            [html.I(className="bi bi-download me-2"), "Exporter Excel"],
            id="export-btn-subtype",
            className="btn-export mt-2",
            n_clicks=0,
        ),
        html.Div(id="table-container-subtype"),
    ]
)

charts_block_registration = html.Div(
    id="charts-container-registration",
    style={
        "display": "grid",
        "gridTemplateColumns": "1fr",
        "gap": "16px",
        "alignItems": "start",
    },
    className="mt-2",
)

table_block_registration = html.Div(
    [
        html.H3("Details by Registration", className="h4 mt-4"),
        dbc.Button(
            [html.I(className="bi bi-download me-2"), "Exporter Excel"],
            id="export-btn-registration",
            className="btn-export mt-2",
            n_clicks=0,
        ),
        html.Div(id="table-container-registration"),
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
        charts_block_subtype,
        table_block_subtype,
        charts_block_registration,
        table_block_registration,
        # ← insert this:
        html.Div(id="about-container", children=about_section),
    ],
)


# --- Outputs -------------------------------------------------------


@app.callback(
    [
        Output(ID_STATS_DIV, "children"),
        Output(ID_CHARTS_CONTAINER, "children"),
        Output(ID_TABLE_CONTAINER, "children"),
        Output(ID_CHARTS_CONTAINER_SUBTYPE, "children"),
        Output(ID_TABLE_CONTAINER_SUBTYPE, "children"),
        Output(ID_CHARTS_CONTAINER_REGISTRATION, "children"),
        Output(ID_TABLE_CONTAINER_REGISTRATION, "children"),
    ],
    add_watcher_for_data(),
    prevent_initial_call=False,
)
def update_plots_tables(n_clicks):
    # --- Prepare data ---
    temporal_all, famille_share_df = prepare_delay_data()
    subtype_family_percentage_df = prepare_subtype_family_data()
    df_pers_by_registration_by_family = prepare_registration_family_data()

    if temporal_all is None or temporal_all.is_empty():
        return dash.no_update

    # --- Stats ---
    summary = analyze_summery()
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

    # --- Family chart ---
    fig_familles = create_bar_figure(
        df=famille_share_df,
        x=COL_NAME_WINDOW_TIME,
        x_max=COL_NAME_WINDOW_TIME_MAX,
        y=COL_NAME_PERCENTAGE_FAMILY_PER_PERIOD,
        title="Percentage of delays by family by segmentation",
        unit="%",
        color="FAMILLE_DR",
        legend_title="Family",
    )
    big_chart = html.Div(
        dcc.Graph(figure=fig_familles, style={"width": "100%", "height": "600px"}),
        className="graph mb-4 mx-auto",
        style={"width": "90%", "gridColumn": "1 / -1"},
    )

    # --- Family table ---
    if famille_share_df.is_empty():
        family_summary_block = dbc.Alert(
            "Aucune donnée famille/segmentation trouvée pour cette sélection.",
            color="warning",
            className="text-center mb-4 mx-auto",
            style={"width": "90%", "gridColumn": "1 / -1"},
        )
    else:
        fam_table_df = (
            famille_share_df.select(
                [
                    COL_NAME_WINDOW_TIME,
                    COL_NAME_WINDOW_TIME_MAX,
                    "FAMILLE_DR",
                    COL_NAME_PERCENTAGE_FAMILY_PER_PERIOD,
                ]
            )
            .sort([COL_NAME_WINDOW_TIME, "FAMILLE_DR"])
            .with_columns(pl.col(COL_NAME_PERCENTAGE_FAMILY_PER_PERIOD).round(2))
        )
        family_summary_table = dash_table.DataTable(
            id=ID_TABLE_SUMMARY,
            data=fam_table_df.to_dicts(),
            columns=[
                {"name": TABLE_NAMES_RENAME.get(c, c), "id": c}
                for c in fam_table_df.columns
            ],
            page_size=10,
            sort_action="native",
            style_cell={"textAlign": "left", "padding": "8px"},
            style_table={"overflowX": "auto"},
            style_header={"fontWeight": "600"},
        )
        family_summary_block = html.Div(
            [
                dbc.Button(
                    [html.I(className="bi bi-download me-2"), "Exporter Excel"],
                    id="export-family-btn",
                    className="btn-export mb-2",
                    n_clicks=0,
                ),
                family_summary_table,
            ],
            className="mb-4 mx-auto",
            style={"width": "90%", "gridColumn": "1 / -1"},
        )

    # --- Family Navbar ---
    navbar_family_layout = create_navbar(
        df=temporal_all,
        tabs_col="FAMILLE_DR",
        id_prefix=ID_NAVBAR_FAMILY,
    )

    # --- Family table (per code) ---
    summary_table = temporal_all.select(
        [
            COL_NAME_WINDOW_TIME,
            COL_NAME_WINDOW_TIME_MAX,
            "FAMILLE_DR",
            "DELAY_CODE",
            COL_NAME_COUNT_DELAY_PER_CODE_DELAY_PER_FAMILY,
            COL_NAME_PERCENTAGE_DELAY_CODE_PER_FAMILY_PER_PERIOD,
            COL_NAME_PERCENTAGE_DELAY_CODE_PER_FAMILY_PER_PERIOD_TOTAL,
        ]
    )
    table = (
        dash_table.DataTable(
            id=ID_TABLE_DELAY_CODE,
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
        if not summary_table.is_empty()
        else dbc.Alert(
            "Aucun code de retard trouvé dans la sélection",
            color="warning",
            className="text-center",
        )
    )

    # --- Subtype Navbar ---
    navbar_subtype_layout = create_navbar(
        df=subtype_family_percentage_df,
        tabs_col="AC_SUBTYPE",
        id_prefix=ID_NAVBAR_SUBTYPE,
    )

    summary_table_subtype = subtype_family_percentage_df.select(
        [
            COL_NAME_WINDOW_TIME,
            COL_NAME_WINDOW_TIME_MAX,
            "AC_SUBTYPE",
            "FAMILLE_DR",
            COL_NAME_PERCENTAGE_SUBTYPE_FAMILY,
        ]
    )
    table_subtype = (
        dash_table.DataTable(
            id=ID_TABLE_SUBTYPE,
            data=summary_table_subtype.to_dicts(),
            columns=[
                {"name": TABLE_NAMES_RENAME.get(c, c), "id": c}
                for c in summary_table_subtype.columns
            ],
            style_cell={"textAlign": "left"},
            sort_action="native",
            page_size=15,
            style_table={"overflowX": "auto"},
        )
        if not summary_table_subtype.is_empty()
        else dbc.Alert(
            "Aucun code de retard trouvé dans la sélection",
            color="warning",
            className="text-center",
        )
    )

    # --- Registration Navbar ---
    navbar_registration_layout = create_navbar(
        df=df_pers_by_registration_by_family,
        tabs_col="AC_REGISTRATION",
        id_prefix=ID_NAVBAR_REGISTRATION,
    )

    summary_table_registration = df_pers_by_registration_by_family.select(
        [
            COL_NAME_WINDOW_TIME,
            COL_NAME_WINDOW_TIME_MAX,
            "AC_REGISTRATION",
            "FAMILLE_DR",
            COL_NAME_PERCENTAGE_REGISTRATION_FAMILY,
        ]
    )
    table_registration = (
        dash_table.DataTable(
            id=ID_TABLE_REGISTRATION,
            data=summary_table_registration.to_dicts(),
            columns=[
                {"name": TABLE_NAMES_RENAME.get(c, c), "id": c}
                for c in summary_table_registration.columns
            ],
            style_cell={"textAlign": "left"},
            sort_action="native",
            page_size=15,
            style_table={"overflowX": "auto"},
        )
        if not summary_table_registration.is_empty()
        else dbc.Alert(
            "No registration data found",
            color="warning",
        )
    )

    return (
        stats,
        [big_chart, family_summary_block, navbar_family_layout],
        table,
        navbar_subtype_layout,
        table_subtype,
        navbar_registration_layout,
        table_registration,
    )


add_export_callbacks(
    id_table=ID_TABLE_DELAY_CODE,
    id_button="export-btn",
    name="delay_code",
)
add_export_callbacks(
    id_table=ID_TABLE_SUMMARY,
    id_button="export-family-btn",
    name="family_summary",
)

add_export_callbacks(
    id_table=ID_TABLE_SUBTYPE,
    id_button="export-btn-subtype",
    name="subtype_summary",
)
add_export_callbacks(
    id_table=ID_TABLE_REGISTRATION,
    id_button="export-btn-registration",
    name="registration_summary",
)


register_navbar_callback(
    id_prefix=ID_NAVBAR_FAMILY,
    get_df_fn=lambda: prepare_delay_data()[0],
    tabs_col="FAMILLE_DR",
    x=COL_NAME_WINDOW_TIME,
    x_max=COL_NAME_WINDOW_TIME_MAX,
    y=COL_NAME_PERCENTAGE_DELAY_CODE_PER_FAMILY_PER_PERIOD,
    title="Distribution of delay codes of {fam} subtype over time",
    color="DELAY_CODE",
    legend_title="Code Delay",
)

register_navbar_callback(
    id_prefix=ID_NAVBAR_SUBTYPE,
    get_df_fn=prepare_subtype_family_data,
    tabs_col="AC_SUBTYPE",
    x=COL_NAME_WINDOW_TIME,
    x_max=COL_NAME_WINDOW_TIME_MAX,
    y=COL_NAME_PERCENTAGE_SUBTYPE_FAMILY,
    title="Distribution of Family type of {fam} subtype over time",
    color="FAMILLE_DR",
    legend_title="Family",
)

register_navbar_callback(
    id_prefix=ID_NAVBAR_REGISTRATION,
    get_df_fn=prepare_registration_family_data,
    tabs_col="AC_REGISTRATION",
    x=COL_NAME_WINDOW_TIME,
    x_max=COL_NAME_WINDOW_TIME_MAX,
    y=COL_NAME_PERCENTAGE_REGISTRATION_FAMILY,
    title="Distribution of Family types for registration {fam} over time",
    color="FAMILLE_DR",
    legend_title="Registration",
)

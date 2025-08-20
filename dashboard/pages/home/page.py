from dash import (
    html,
    dcc,
    Output,
    dash_table,
)
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from calculations.main_dashboard import (
    COL_NAME_CATEGORY_GT_15MIN,
    COL_NAME_CATEGORY_GT_15MIN_COUNT,
    COL_NAME_CATEGORY_GT_15MIN_MEAN,
    COL_NAME_COUNT_FLIGHTS,
    COL_NAME_PERCENTAGE,
    COL_NAME_PERCENTAGE_DELAY,
    COL_NAME_SUBTYPE,
    calculate_delay_pct,
    calculate_period_distribution,
    calculate_subtype_airport_pct,
    calculate_subtype_registration_pct,
    process_subtype_pct_data,
)
from utils_dashboard.utils_download import add_export_callbacks
from server_instance import get_app
from data_managers.excel_manager import (
    get_df,
    add_watcher_for_data,
    COL_NAME_WINDOW_TIME_MAX,
    COL_NAME_WINDOW_TIME,
)

from utils_dashboard.utils_graph import (
    create_bar_figure,
    create_bar_horizontal_figure,
    create_navbar,
)


ID_SUMMERY_TABLE = "summary-table"
ID_FIGURE_CATEGORY_DELAY_GT_15MIN = "figure-category-delay-gt-15min"
ID_TABLE_CATEGORY_DELAY_GT_15MIN = "table-category-delay-gt-15min"
ID_TABLE_FLIGHT_DELAY = "table-flight-delay"
ID_FIGURE_FLIGHT_DELAY = "figure-flight-delay"
ID_FIGURE_SUBTYPE_PR_DELAY_MEAN = "figure-subtype-pr-delay-mean"
ID_TABLE_SUBTYPE_PR_DELAY_MEAN = "table-subtype-pr-delay-mean"
ID_navbar_SUBTYPE_REG_PCT = "figure-subtype-reg-pct"
ID_TABLE_SUBTYPE_REG_PCT = "table-subtype-reg-pct"
ID_TABLE_SUBTYPE_AIRPORT_PCT = "table-subtype-airport-pct"
ID_NAVBAR_SUBTYPE_AIRPORT_PCT = "navbar-subtype-airport-pct"

TABLE_NAMES_RENAME = {
    "AC_SUBTYPE": "Aircraft Subtype",
    "AC_REGISTRATION": "Registration",
    "DEP_DAY_SCHED": "Scheduled Departure Day",
    "DELAY_TIME": "Delay Time (min)",
    "DELAY_CODE": "Delay Code",
    "count": "Flight Count",
    COL_NAME_WINDOW_TIME: "Interval Start",
    COL_NAME_WINDOW_TIME_MAX: "Interval End",
    COL_NAME_PERCENTAGE_DELAY: "Percentage of Delayed Flights",
    COL_NAME_COUNT_FLIGHTS: "Count of Delayed Flights",
    COL_NAME_CATEGORY_GT_15MIN: "Delay Category",
    COL_NAME_CATEGORY_GT_15MIN_MEAN: "Perentage of Delayed Flights",
    COL_NAME_CATEGORY_GT_15MIN_COUNT: "Category Count",
    COL_NAME_PERCENTAGE: "percentage",
    "DEP_AP_SCHED": "Departure Airport",
}


app = get_app()


layout = dbc.Container(
    [
        html.Div(
            [
                dbc.Alert(
                    [
                        html.I(
                            className="bi bi-check-circle me-2"
                        ),  # icône Bootstrap Icons
                        html.Span(
                            id="result-message-text"
                        ),  # ↔ « 268 result(s) found »
                    ],
                    id="result-message",
                    color="success",
                    is_open=False,
                    className="result-alert glass-success mt-4 mb-3",
                ),
                # Premier bouton + tableau + export
                dbc.Row(
                    dbc.Col(
                        html.H2(
                            "Table of flights with delay.",
                            className="lead",
                        )
                    )
                ),
                dbc.Button(
                    [html.I(className="bi bi-download me-2"), "Exporter Excel"],
                    id="result-export-btn",
                    className="btn-export mt-2",
                    n_clicks=0,
                ),
                dash_table.DataTable(
                    id=ID_SUMMERY_TABLE,
                    columns=[],
                    data=[],
                    page_size=10,
                    style_cell={"textAlign": "left"},
                    sort_action="native",
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
                ),
                # Graphique subtype pct
                html.Div(
                    dcc.Graph(
                        id=ID_FIGURE_SUBTYPE_PR_DELAY_MEAN, style={"height": "400px"}
                    ),
                    className="graph mb-4 mx-auto",  # ← nouvelle classe CSS
                    style={"width": "90%"},
                ),
                # Tableau des subtypes
                # Deuxième bouton + tableau + export
                html.Div(
                    [
                        dbc.Button(
                            [html.I(className="bi bi-download me-2"), "Exporter Excel"],
                            id="subtype-export-btn",
                            className="btn-export mt-2",
                            n_clicks=0,
                        ),
                        dash_table.DataTable(
                            id=ID_TABLE_SUBTYPE_PR_DELAY_MEAN,
                            columns=[],
                            data=[],
                            page_size=10,
                            style_cell={"textAlign": "left"},
                            sort_action="native",
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
                        ),
                    ]
                ),
                # Graphique retard %
                html.Div(
                    dcc.Graph(
                        id=ID_FIGURE_CATEGORY_DELAY_GT_15MIN,
                        style={"margin": "auto", "height": "400px", "width": "90%"},
                    ),
                    className="graph mb-4 mx-auto",  # ← nouvelle classe CSS
                    style={"width": "90%"},
                ),
                html.Div(
                    [
                        dbc.Button(
                            [html.I(className="bi bi-download me-2"), "Exporter Excel"],
                            id="category-export-btn",
                            className="btn-export mt-2",
                            n_clicks=0,
                        ),
                        dash_table.DataTable(
                            id=ID_TABLE_CATEGORY_DELAY_GT_15MIN,
                            columns=[],
                            data=[],
                            page_size=10,
                            style_cell={"textAlign": "left"},
                            sort_action="native",
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
                        ),
                    ],
                    style={"marginBottom": "40px"},
                ),
                # Graphique intervalles
                html.Div(
                    dcc.Graph(
                        id=ID_FIGURE_FLIGHT_DELAY,
                        style={"margin": "auto", "width": "100%"},
                    ),
                    className="graph mb-4 mx-auto",  # ← nouvelle classe CSS
                    style={"width": "90%"},
                ),
                # Troisième bouton + tableau + export
                html.Div(
                    [
                        dbc.Button(
                            [html.I(className="bi bi-download me-2"), "Exporter Excel"],
                            id="interval-export-btn",
                            className="btn-export mt-2",
                            n_clicks=0,
                        ),
                        dash_table.DataTable(
                            id=ID_TABLE_FLIGHT_DELAY,
                            columns=[],
                            data=[],
                            page_size=10,
                            style_cell={"textAlign": "left"},
                            sort_action="native",
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
                        ),
                    ],
                    style={"marginBottom": "40px"},
                ),
                # Subtype-registration % chart + table
                dcc.Tabs(
                    id=ID_navbar_SUBTYPE_REG_PCT,
                    persistence=True,
                ),
                html.Div(
                    [
                        dbc.Button(
                            [
                                html.I(className="bi bi-download me-2"),
                                "Exporter Excel",
                            ],
                            id="subtype-reg-export-btn",
                            className="btn-export mt-2",
                            n_clicks=0,
                        ),
                        dash_table.DataTable(
                            id=ID_TABLE_SUBTYPE_REG_PCT,
                            columns=[],
                            data=[],
                            page_size=10,
                            style_cell={"textAlign": "left"},
                            sort_action="native",
                            style_data_conditional=[
                                {
                                    "if": {"row_index": "odd"},
                                    "backgroundColor": "#f8f9fa",
                                },
                                {
                                    "if": {"row_index": "even"},
                                    "backgroundColor": "white",
                                },
                            ],
                        ),
                    ],
                    style={"marginTop": "12px", "marginBottom": "40px"},
                ),
                dcc.Tabs(
                    id=ID_NAVBAR_SUBTYPE_AIRPORT_PCT,
                    persistence=True,
                ),
                html.Div(
                    [
                        dbc.Button(
                            [
                                html.I(className="bi bi-download me-2"),
                                "Exporter Excel",
                            ],
                            id="subtype-airport-export-btn",
                            className="btn-export mt-2",
                            n_clicks=0,
                        ),
                        dash_table.DataTable(
                            id=ID_TABLE_SUBTYPE_AIRPORT_PCT,
                            columns=[],
                            data=[],
                            page_size=10,
                            style_cell={"textAlign": "left"},
                            sort_action="native",
                            style_data_conditional=[
                                {
                                    "if": {"row_index": "odd"},
                                    "backgroundColor": "#f8f9fa",
                                },
                                {
                                    "if": {"row_index": "even"},
                                    "backgroundColor": "white",
                                },
                            ],
                        ),
                    ],
                    style={"marginTop": "12px", "marginBottom": "40px"},
                ),
            ],
            className="mx-3",
        ),
    ],
    fluid=True,
)


# 1) Summary table callback
@app.callback(
    Output("result-message", "children"),
    Output("result-message", "color"),
    Output("result-message", "is_open"),
    Output(ID_SUMMERY_TABLE, "columns"),
    Output(ID_SUMMERY_TABLE, "data"),
    add_watcher_for_data(),
)
def update_summary(_):
    df_lazy = get_df()
    if df_lazy is None:
        alert = dbc.Alert(
            "No Excel file loaded. Please upload first.",
            color="danger",
            className="mt-3",
        )
        return alert, "danger", True, [], []
    df = df_lazy.collect()
    if df.is_empty():
        return (
            dbc.Alert("No results found.", color="warning", className="mt-3"),
            "warning",
            True,
            [],
            [],
        )
    # build summary table
    df_summary = df.select(
        [
            "AC_SUBTYPE",
            "AC_REGISTRATION",
            "DEP_DAY_SCHED",
            "DELAY_TIME",
            "DELAY_CODE",
        ]
    )
    cols = [{"name": TABLE_NAMES_RENAME.get(c, c), "id": c} for c in df_summary.columns]
    data = df_summary.to_dicts()
    alert = dbc.Alert(
        f"{df.height} result(s) found.", color="success", className="mt-3"
    )
    return alert, "success", True, cols, data


# 2) Subtype-delay % chart + table callback
@app.callback(
    Output(ID_FIGURE_SUBTYPE_PR_DELAY_MEAN, "figure"),
    Output(ID_TABLE_SUBTYPE_PR_DELAY_MEAN, "columns"),
    Output(ID_TABLE_SUBTYPE_PR_DELAY_MEAN, "data"),
    add_watcher_for_data(),
)
def update_subtype(_):
    df_lazy = get_df()
    if df_lazy is None:
        return go.Figure(), [], []
    df_sub = process_subtype_pct_data(df_lazy).collect()
    # figure
    # fig = create_bar_horizontal_figure(
    #     df_sub,
    #     x=COL_NAME_PERCENTAGE_DELAY,
    #     y=COL_NAME_SUBTYPE,
    #     title="Delayed flights by SUBTYPE (%)",
    # )

    fig = create_bar_horizontal_figure(
        df_sub,
        x=COL_NAME_PERCENTAGE_DELAY,
        y=COL_NAME_WINDOW_TIME,
        y_max=COL_NAME_WINDOW_TIME_MAX,
        title="Delayed flights by SUBTYPE (%) per time window",
        color="AC_SUBTYPE",
        legend_title="Subtype",
        barmode="stack",
    )

    # table
    cols = [{"name": TABLE_NAMES_RENAME.get(c, c), "id": c} for c in df_sub.columns]
    data = df_sub.to_dicts()
    return fig, cols, data


# 3) Delay-category chart + table callback
@app.callback(
    Output(ID_FIGURE_CATEGORY_DELAY_GT_15MIN, "figure"),
    Output(ID_TABLE_CATEGORY_DELAY_GT_15MIN, "columns"),
    Output(ID_TABLE_CATEGORY_DELAY_GT_15MIN, "data"),
    add_watcher_for_data(),
)
def update_category(_):
    print("Updating category...")
    df_lazy = get_df()
    if df_lazy is None:
        return go.Figure(), [], []
    df_cat = calculate_delay_pct(df_lazy).collect()
    # figure
    fig = create_bar_figure(
        df_cat,
        x=COL_NAME_WINDOW_TIME,
        x_max=COL_NAME_WINDOW_TIME_MAX,
        y=COL_NAME_CATEGORY_GT_15MIN_MEAN,
        color=COL_NAME_CATEGORY_GT_15MIN,
        legend_title="Category of delay",
        title="Flight delays ≥15 min vs <15 min (per time window)",
    )
    # table
    display_cols = [
        COL_NAME_WINDOW_TIME,
        COL_NAME_WINDOW_TIME_MAX,
        COL_NAME_CATEGORY_GT_15MIN,
        COL_NAME_CATEGORY_GT_15MIN_MEAN,
    ]

    df_disp = df_cat.select(display_cols)
    cols = [{"name": TABLE_NAMES_RENAME.get(c, c), "id": c} for c in display_cols]
    data = df_disp.to_dicts()
    return fig, cols, data


# 4) Interval-distribution chart + table callback
@app.callback(
    Output(ID_FIGURE_FLIGHT_DELAY, "figure"),
    Output(ID_TABLE_FLIGHT_DELAY, "columns"),
    Output(ID_TABLE_FLIGHT_DELAY, "data"),
    add_watcher_for_data(),
)
def update_interval(_):
    df_lazy = get_df()
    if df_lazy is None:
        return go.Figure(), [], []
    df = df_lazy.collect()
    if df.is_empty():
        return go.Figure(), [], []
    df_period = calculate_period_distribution(df)
    # figure
    fig = create_bar_horizontal_figure(
        df_period,
        x=COL_NAME_PERCENTAGE_DELAY,
        y=COL_NAME_WINDOW_TIME,
        y_max=COL_NAME_WINDOW_TIME_MAX,
        title="Distribution of flights by time intervals",
    )
    # table
    cols = [{"name": TABLE_NAMES_RENAME.get(c, c), "id": c} for c in df_period.columns]
    data = df_period.to_dicts()
    return fig, cols, data


@app.callback(
    Output(ID_navbar_SUBTYPE_REG_PCT, "children"),
    Output(ID_navbar_SUBTYPE_REG_PCT, "value"),
    Output(ID_TABLE_SUBTYPE_REG_PCT, "columns"),
    Output(ID_TABLE_SUBTYPE_REG_PCT, "data"),
    add_watcher_for_data(),
)
def update_subtype_registration_pct(_):
    df_lazy = get_df()
    if df_lazy is None:
        return [], None, [], []

    # calculate (cached)
    df_reg = calculate_subtype_registration_pct(df_lazy).collect()
    if df_reg.is_empty():
        return [], None, [], []

    # figure: horizontal stacked bars per time-window showing registration % within subtypes
    figs = create_navbar(
        df_reg,
        tabs=COL_NAME_SUBTYPE,
        x=COL_NAME_WINDOW_TIME,
        x_max=COL_NAME_WINDOW_TIME_MAX,
        y=COL_NAME_PERCENTAGE,
        title="distribution of registrations for {fam} subtype across time",
        legend_title="Registrations",
        color="AC_REGISTRATION",
        value_other=3,
    )

    value = figs[0].value if figs else None
    # table: pick useful columns to display
    display_cols = [
        COL_NAME_WINDOW_TIME,
        COL_NAME_WINDOW_TIME_MAX,
        COL_NAME_SUBTYPE,
        "AC_REGISTRATION",
        COL_NAME_PERCENTAGE,
    ]
    df_disp = df_reg.select(display_cols)
    cols = [{"name": TABLE_NAMES_RENAME.get(c, c), "id": c} for c in display_cols]

    data = df_disp.to_dicts()

    return figs, value, cols, data


@app.callback(
    Output(ID_NAVBAR_SUBTYPE_AIRPORT_PCT, "children"),
    Output(ID_NAVBAR_SUBTYPE_AIRPORT_PCT, "value"),
    Output(ID_TABLE_SUBTYPE_AIRPORT_PCT, "columns"),
    Output(ID_TABLE_SUBTYPE_AIRPORT_PCT, "data"),
    add_watcher_for_data(),
)
def update_subtype_airport_pct(_):
    df_lazy = get_df()
    if df_lazy is None:
        return [], None, [], []

    # calculate (cached)
    df_air = calculate_subtype_airport_pct(df_lazy).collect()
    if df_air.is_empty():
        return [], None, [], []

    # figure: horizontal stacked bars per time-window showing airport % within subtypes
    figs = create_navbar(
        df_air,
        tabs=COL_NAME_SUBTYPE,
        x=COL_NAME_WINDOW_TIME,
        x_max=COL_NAME_WINDOW_TIME_MAX,
        y=COL_NAME_PERCENTAGE,
        title="distribution of airports for {fam} subtype across time",
        legend_title="Airports",
        color="DEP_AP_SCHED",
        value_other=3,
    )

    value = figs[0].value if figs else None
    # table: pick useful columns to display
    display_cols = [
        COL_NAME_WINDOW_TIME,
        COL_NAME_WINDOW_TIME_MAX,
        COL_NAME_SUBTYPE,
        "DEP_AP_SCHED",
        COL_NAME_PERCENTAGE,
    ]
    df_disp = df_air.select(display_cols)
    cols = [{"name": TABLE_NAMES_RENAME.get(c, c), "id": c} for c in display_cols]

    data = df_disp.to_dicts()

    return figs, value, cols, data


# --- CALLBACKS POUR TELECHARGEMENT EXCEL ---
for tbl, btn, name in [
    (ID_SUMMERY_TABLE, "result-export-btn", "flights_filtres"),
    (ID_TABLE_SUBTYPE_PR_DELAY_MEAN, "subtype-export-btn", "flights_subtype_filtres"),
    (ID_TABLE_FLIGHT_DELAY, "interval-export-btn", "flights_intervalles"),
    (
        ID_TABLE_CATEGORY_DELAY_GT_15MIN,
        "category-export-btn",
        "flights_lt_15min_vs_gt_15min_filtres",
    ),
    (
        ID_TABLE_SUBTYPE_REG_PCT,
        "subtype-reg-export-btn",
        "flights_subtype_reg_filtres",
    ),
    (
        ID_TABLE_SUBTYPE_AIRPORT_PCT,
        "subtype-airport-export-btn",
        "flights_subtype_airport_filtres",
    ),
]:
    add_export_callbacks(id_table=tbl, id_button=btn, name=name)

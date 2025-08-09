import dash
import dash_bootstrap_components as dbc
from dash import Output, dash_table, dcc
from calculations.performance_metrics import (
    COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46,
    COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN,
    COL_NAME_PER_FLIGHTS_NOT_DELAYED,
    COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY,
    COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_41_46_GTE_15MIN,
    COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_GTE_15MIN,
    ID_CARD_DELAY,
    ID_CARD_DELAY_15MIN,
    ID_CARD_DELAY_15MIN_41_46,
    ID_GRAPH_DELAY,
    ID_GRAPH_DELAY_15MIN,
    ID_GRAPH_DELAY_41_46_15MIN,
    calculate_result,
)
from utils_dashboard.utils_graph import (
    create_bar_figure,
    generate_card_info_change,
)
from server_instance import get_app
import dash.html as html

from data_managers.excel_manager import (
    COL_NAME_TOTAL_COUNT,
    COL_NAME_WINDOW_TIME,
    COL_NAME_WINDOW_TIME_MAX,
    get_df,
    add_watcher_for_data,
)

from utils_dashboard.utils_download import (
    add_export_callbacks,
)


app = get_app()

ID_TABLE_CONTAINER = "result_table_percentage_metrics"
ID_TABLE = "result_table_metrics"

TABLE_COL_NAMES = [
    {"name": "Window Start", "id": COL_NAME_WINDOW_TIME},
    {"name": "Window End", "id": COL_NAME_WINDOW_TIME_MAX},
    {
        "name": "Percentage of On-Time Flights",
        "id": COL_NAME_PER_FLIGHTS_NOT_DELAYED,
    },
    {
        "name": "Percentage of On-Time or Delays Less Than 15 Minutes",
        "id": COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN,
    },
    {
        "name": "Percentage of On-Time or less than 15 Minutes, or Delays Not Due to Reasons 41/46",
        "id": COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46,
    },
    {
        "name": "Total count of flights",
        "id": COL_NAME_TOTAL_COUNT,
    },
    {
        "name": "Total count of flights with delay",
        "id": COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY,
    },
    {
        "name": "Total count of flights with delay greater than 15 min",
        "id": COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_GTE_15MIN,
    },
    {
        "name": "Total count of flights with delay than 15 min with code delay 41 and 46",
        "id": COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_41_46_GTE_15MIN,
    },
]


# ---------- layout definition -----------------------------------

layout = dbc.Container(
    [
        # Metrics row
        dbc.Row(
            [
                dbc.Col(id=ID_CARD_DELAY, md=4),
                dbc.Col(id=ID_CARD_DELAY_15MIN, md=4),
                dbc.Col(id=ID_CARD_DELAY_15MIN_41_46, md=4),
            ],
            className="g-4 mb-5",
            justify="center",
        ),
        # Graphs row (unchanged)
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        id=ID_GRAPH_DELAY,
                    ),
                    className="graph",
                    lg=12,
                    xl=6,
                ),
                dbc.Col(
                    dcc.Graph(
                        id=ID_GRAPH_DELAY_15MIN,
                    ),
                    className="graph",
                    lg=12,
                    xl=6,
                ),
                dbc.Col(
                    dcc.Graph(
                        id=ID_GRAPH_DELAY_41_46_15MIN,
                    ),
                    className="graph",
                    lg=12,
                    xl=12,
                ),
            ],
            className="g-4 justify-content-center",
        ),
        dbc.Button(
            [html.I(className="bi bi-download me-2"), "Exporter Excel"],
            id="export-pre-metrics-btn",
            className="btn-export mt-2",
            n_clicks=0,
        ),
        dbc.Row(
            id=ID_TABLE_CONTAINER,
        ),
    ],
    fluid=True,
    className="p-4",
)


add_export_callbacks(
    ID_TABLE,
    "export-pre-metrics-btn",
    "performance_metrics",
)


@app.callback(
    [
        Output(ID_CARD_DELAY, "children"),
        Output(ID_CARD_DELAY_15MIN, "children"),
        Output(ID_CARD_DELAY_15MIN_41_46, "children"),
        Output(ID_GRAPH_DELAY, "figure"),
        Output(ID_GRAPH_DELAY_15MIN, "figure"),
        Output(ID_GRAPH_DELAY_41_46_15MIN, "figure"),
        Output(ID_TABLE_CONTAINER, "children"),
    ],
    add_watcher_for_data(),
)
def create_layout(
    _,
):

    df = get_df()
    if df is None:
        return dash.no_update

    result = calculate_result()

    if result is None:
        return dash.no_update
    card1 = generate_card_info_change(
        result,
        COL_NAME_PER_FLIGHTS_NOT_DELAYED,
        "Percentage of On-Time Flights",
    )  # example first card
    card2 = generate_card_info_change(
        result,
        COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN,
        "Percentage of On-Time or Delays Less Than 15 Minutes",
    )  # example second card
    card3 = generate_card_info_change(
        result,
        COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46,
        "Percentage of On-Time or less than 15 Minutes, or Delays Not Due to Reasons 41/46",
    )  # example second card

    fig1 = create_bar_figure(
        result,
        COL_NAME_WINDOW_TIME,
        COL_NAME_PER_FLIGHTS_NOT_DELAYED,
        "Percentage of On-Time Flights",
    )
    fig2 = create_bar_figure(
        result,
        COL_NAME_WINDOW_TIME,
        COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN,
        "Percentage of On-Time or Delays Less Than 15 Minutes",
    )
    fig3 = create_bar_figure(
        result,
        COL_NAME_WINDOW_TIME,
        COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46,
        "Percentage of On-Time or less than 15 Minutes, or Delays Not Due to Reasons 41/46",
    )

    table_col_names = [
        {"id": col["id"], "name": col["name"]} for col in TABLE_COL_NAMES
    ]

    table_data = (
        result.drop_nulls(
            subset=[
                COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY,
                COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_GTE_15MIN,
                COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_41_46_GTE_15MIN,
            ]
        )
        .select([col["id"] for col in table_col_names])
        .to_dicts()
    )

    table = []
    # builds

    if result.height != 0:
        table = dash_table.DataTable(
            data=table_data,
            columns=table_col_names,
            id=ID_TABLE,
            page_size=10,
            sort_action="native",
            sort_by=[{"column_id": COL_NAME_WINDOW_TIME, "direction": "desc"}],
            style_cell={
                "textAlign": "left",
            },
            style_table={"overflowX": "auto"},
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
        )

    return (
        card1,
        card2,
        card3,
        fig1,
        fig2,
        fig3,
        table,
    )

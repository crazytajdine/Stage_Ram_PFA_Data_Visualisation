import dash_bootstrap_components as dbc
from dash import html, dcc
from dashboard.server_instance import get_app
from dashboard.excel_manager import get_df

app = get_app()


def create_layout():
    df = get_df()
    if df is None:
        return None


layout = dbc.Container(
    [
        html.H1("Performance Metrics Dashboard", className="text-center my-4"),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        id="graph1",
                        figure={
                            "data": [
                                {
                                    "x": ["dd", "ddd", "dada"],
                                    "y": [4, 1, 2],
                                    "type": "bar",
                                }
                            ],
                            "layout": {"title": "Graph 1"},
                        },
                    ),
                    width=6,
                    style={"padding": "0 5px"},
                ),
                dbc.Col(
                    dcc.Graph(
                        id="graph2",
                        figure={
                            "data": [{"x": [1, 2, 3], "y": [2, 4, 5], "type": "line"}],
                            "layout": {"title": "Graph 2"},
                        },
                    ),
                    width=6,
                    style={"padding": "0 5px"},
                ),
            ],
            className="gx-1",  # Bootstrap 5: very small horizontal gutters (space)
            # For Bootstrap 4: use no_gutters=True instead
        ),
        dbc.Row(
            dbc.Col(
                dcc.Graph(
                    id="graph3",
                    figure={
                        "data": [{"x": [1, 2, 3], "y": [5, 3, 6], "type": "scatter"}],
                        "layout": {"title": "Big Graph"},
                    },
                ),
                width=12,
                style={"padding": "0"},
            ),
            className="gx-0",  # no horizontal gutters for full width graph
        ),
    ],
    fluid=True,
)

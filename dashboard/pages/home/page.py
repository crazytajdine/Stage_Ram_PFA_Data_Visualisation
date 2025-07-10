from dash import html, dcc
import dash_bootstrap_components as dbc

from dash import Input, Output
import random


from dashboard.server_instance import get_app

app = get_app()

@app.callback(
    Output("card-users", "children"),
    Output("card-sessions", "children"),
    Output("card-errors", "children"),
    Output("home-chart", "figure"),
    Input("refresh-btn", "n_clicks"),
)
def refresh_data(n_clicks):
    # Generate random metrics
    total_users = random.randint(800, 2000)
    sessions = random.randint(200, 500)
    errors = random.randint(0, 20)

    # Generate a simple line chart for the last 6 months
    months = ["Feb", "Mar", "Apr", "May", "Jun", "Jul"]
    users_trend = [random.randint(800, 2000) for _ in months]

    figure = {
        "data": [
            {"x": months, "y": users_trend, "type": "line", "name": "Users"}
        ],
        "layout": {
            "title": "Monthly User Growth (Dummy)",
            "plot_bgcolor": "#f8f9fa",
            "paper_bgcolor": "#f8f9fa",
        }
    }

    return f"{total_users:,}", f"{sessions:,}", str(errors), figure



layout = html.Div([
    html.H2("🏠 Home Overview", className="mb-4"),

    dbc.Button("🔄 Refresh Data", id="refresh-btn", color="info", className="mb-4"),

    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Total Users"),
                dbc.CardBody(html.H3(id="card-users", className="card-title")),
                dbc.CardFooter("New users this month"),
            ], color="primary", inverse=True),
            width=4
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Active Sessions"),
                dbc.CardBody(html.H3(id="card-sessions", className="card-title")),
                dbc.CardFooter("Current live users"),
            ], color="success", inverse=True),
            width=4
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Errors Reported"),
                dbc.CardBody(html.H3(id="card-errors", className="card-title")),
                dbc.CardFooter("Last 24 hours"),
            ], color="danger", inverse=True),
            width=4
        ),
    ]),

    html.Hr(),

    dcc.Graph(id='home-chart')
])

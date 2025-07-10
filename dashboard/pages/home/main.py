from dash import html, dcc
import dash_bootstrap_components as dbc

layout = html.Div([
    html.H2("🏠 Home Overview", className="mb-4"),
    
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Total Users"),
            dbc.CardBody([
                html.H3("1,245", className="card-title"),
                html.P("New users this month", className="card-text"),
            ])
        ], color="primary", inverse=True), width=4),

        dbc.Col(dbc.Card([
            dbc.CardHeader("Active Sessions"),
            dbc.CardBody([
                html.H3("317", className="card-title"),
                html.P("Current live users", className="card-text"),
            ])
        ], color="success", inverse=True), width=4),

        dbc.Col(dbc.Card([
            dbc.CardHeader("Errors Reported"),
            dbc.CardBody([
                html.H3("7", className="card-title"),
                html.P("Last 24 hours", className="card-text"),
            ])
        ], color="danger", inverse=True), width=4),
    ]),

    html.Hr(),

    dcc.Graph(
        id='home-chart',
        figure={
            'data': [
                {'x': ['Jan', 'Feb', 'Mar', 'Apr'], 'y': [100, 200, 300, 400], 'type': 'line', 'name': 'Users'},
            ],
            'layout': {
                'title': 'Monthly User Growth',
                'plot_bgcolor': '#f8f9fa'
            }
        }
    )
])

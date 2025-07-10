from dash import html, dcc
import dash_bootstrap_components as dbc




layout = html.Div([
    html.H2("💻 Tech Metrics", className="mb-4"),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Server Load"),
            dbc.CardBody([
                html.H3("58%", className="card-title"),
                html.P("Average load last hour", className="card-text"),
            ])
        ], color="warning", inverse=True), width=6),

        dbc.Col(dbc.Card([
            dbc.CardHeader("Deployments"),
            dbc.CardBody([
                html.H3("4", className="card-title"),
                html.P("In the last 24 hours", className="card-text"),
            ])
        ], color="info", inverse=True), width=6),
    ]),

    html.Hr(),

    dcc.Graph(
        id='tech-chart',
        figure={
            'data': [
                {'x': ['00:00', '06:00', '12:00', '18:00', '00:00'], 'y': [20, 40, 30, 50, 58], 'type': 'bar', 'name': 'CPU Load'},
            ],
            'layout': {
                'title': 'Server Load Trend (Last 24h)',
                'plot_bgcolor': '#f8f9fa'
            }
        }
    )
])

import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import dashboard.pages.home.page as home
import dashboard.pages.tech.page as tech
import dash_bootstrap_components as dbc

from dashboard.server_instance import get_app


app = get_app()






NAVBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    "box-shadow": "2px 0 10px rgba(0,0,0,0.1)",
    "transition": "all 0.3s",
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
    "transition": "all 0.3s",
}

TOGGLE_STYLE = {
    "position": "fixed",
    "top": "1rem",
    "left": "16.5rem",
    "zIndex": 1,
    "transition": "all 0.3s",
}

# Icônes avec Font Awesome
get_app().index_string = '''<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>'''

# Données pour les éléments de navigation
nav_items = [
    {"name": "Dashboard", "icon": "fas fa-home", "id": "btn-home", "page": home.layout},
    {"name": "Analytics", "icon": "fas fa-chart-line", "id": "btn-analytics", "page": tech.layout},
    {"name": "Settings", "icon": "fas fa-cog", "id": "btn-settings", "page": html.Div("Paramètres")},
]

get_app().layout = html.Div([
    # Barre de navigation
    html.Div(
        [
            html.Div(
                [
                    html.H3("Dashboard Pro", className="navbar-brand", style={"margin-bottom": "2rem"}),
                    html.Hr(),
                    dbc.Nav(
                        [
                            dbc.NavLink(
                                [
                                    html.I(className=item["icon"], style={"margin-right": "10px"}),
                                    html.Span(item["name"])
                                ],
                                id=item["id"],
                                n_clicks=0,
                                href="#",
                                className="nav-link",
                                style={"border-radius": "5px", "margin": "5px 0"}
                            )
                            for item in nav_items
                        ],
                        vertical=True,
                        pills=True,
                    ),
                    html.Div(
                        [
                            html.Hr(),
                            html.Div(
                                [
                                    html.I(className="fas fa-user-circle", style={"font-size": "2rem"}),
                                    html.Div(
                                        [
                                            html.P("Admin User", style={"margin": "0", "font-weight": "bold"}),
                                            html.P("admin@example.com", style={"margin": "0", "font-size": "0.8rem"})
                                        ],
                                        style={"margin-left": "10px"}
                                    )
                                ],
                                style={"display": "flex", "align-items": "center"}
                            )
                        ],
                        className="user-profile"
                    )
                ],
                className="navbar-content"
            )
        ],
        id="sidebar",
        style=NAVBAR_STYLE
    ),
    
    # Contenu principal
    html.Div(
        [
            dbc.Button(
                html.I(className="fas fa-bars"),
                id="sidebar-toggle",
                color="primary",
                className="mb-3",
                style=TOGGLE_STYLE
            ),
            html.Div(id="page-content", style=CONTENT_STYLE)
        ],
        id="main-content"
    ),
    
    # Stockage pour suivre l'état du menu
    dcc.Store(id='sidebar-collapsed', data=False),
])

@get_app().callback(
    Output("page-content", "children"),
    [Input(item["id"], "n_clicks") for item in nav_items],
)
def render_page(*args):
    ctx = dash.callback_context
    if not ctx.triggered:
        return home.layout
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    for item in nav_items:
        if item["id"] == button_id:
            return item["page"]
    
    return home.layout

@get_app().callback(
    [Output("sidebar", "style"), Output("main-content", "style"), Output("sidebar-toggle", "style")],
    [Input("sidebar-toggle", "n_clicks")],
    [State("sidebar-collapsed", "data")]
)
def toggle_sidebar(n, collapsed):
    if n:
        collapsed = not collapsed
    
    if collapsed:
        # Menu réduit
        sidebar_style = NAVBAR_STYLE.copy()
        sidebar_style.update({"width": "5rem", "padding": "2rem 0.5rem"})
        
        content_style = CONTENT_STYLE.copy()
        content_style.update({"margin-left": "7rem"})
        
        toggle_style = TOGGLE_STYLE.copy()
        toggle_style.update({"left": "5.5rem"})
        
        return sidebar_style, content_style, toggle_style
    
    # Menu étendu
    return NAVBAR_STYLE, CONTENT_STYLE, TOGGLE_STYLE



if __name__ == '__main__':
    app.run(debug=True)
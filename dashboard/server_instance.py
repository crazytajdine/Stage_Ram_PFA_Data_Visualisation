import dash
import dash_bootstrap_components as dbc

app = None
server = None


def init_server():

    app = dash.Dash(
        __name__,
        suppress_callback_exceptions=True,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
    )
    app.title = "Dashboard Pro"
    server = app.server
    return app,server

def get_app() -> dash.Dash:
    global app,server
    if app is None:
        print("Initializing server instance...")
        app,server = init_server()
    return app

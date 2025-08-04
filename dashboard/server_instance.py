import dash
import dash_bootstrap_components as dbc

app = None
server = None


def init_server():
    global app, server
    app = dash.Dash(
        __name__,
        use_pages=False,  # ← Disable automatic page discovery
        suppress_callback_exceptions=True,  # still needed for legacy callbacks
        assets_folder="assets",
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            dbc.icons.BOOTSTRAP,
        ],
    )
    app.title = "Dashboard Pro"
    server = app.server
    return app, server


def get_app() -> dash.Dash:
    global app, server
    if app is None:
        print("Initializing server instance...")
        app, server = init_server()
    return app


def get_server():
    global server, app
    if server is None:
        print("Initializing server instance...")
        app, server = init_server()
    return server

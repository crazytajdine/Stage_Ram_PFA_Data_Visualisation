import dash
import dash_bootstrap_components as dbc

app = None
server = None



from dash import Dash                  # ⬅️ import the class
import dash_bootstrap_components as dbc


def init_server():
    global app, server
    app = Dash(                        # ✅ class constructor
         __name__,
         use_pages=False,
         suppress_callback_exceptions=True,
         assets_folder="assets",
        external_stylesheets=[
            dbc.themes.LUX,
            # (optional) Bootstrap-Icons CDN for the user icon
            "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css","/assets/ram.css",
        ],
     )
    return app, app.server

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
